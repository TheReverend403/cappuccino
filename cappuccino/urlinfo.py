#  This file is part of cappuccino.
#
#  cappuccino is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  cappuccino is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cappuccino.  If not, see <https://www.gnu.org/licenses/>.

import concurrent
import contextlib
import html
import ipaddress
import random
import re
import socket
import time
from copy import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from email.headerregistry import ContentDispositionHeader, ContentTypeHeader

from email.policy import EmailPolicy
from io import StringIO
from urllib.parse import urlparse

import bs4
import irc3
import requests
from humanize import naturalsize

from cappuccino import Plugin
from cappuccino.util.formatting import Color, style, truncate_with_ellipsis, unstyle


class ResponseBodyTooLarge(requests.RequestException):
    pass


class InvalidIPAddressError(Exception):
    pass


class ContentTypeNotAllowedError(Exception):
    pass


class RequestTimeout(requests.RequestException):
    pass


def _clean_url(url: str):
    if url:
        url = url.rstrip("'.,\"\1")
        braces = [("{", "}"), ("<", ">"), ("[", "]"), ("(", ")")]
        for left_brace, right_brace in braces:
            if left_brace not in url and url.endswith(right_brace):
                url = url.rstrip(right_brace)
    return url


def _extract_title_from_soup(soup: bs4.BeautifulSoup):
    if title_tag := soup.find("meta", property="og:title", content=True):
        return title_tag.get("content")
    with contextlib.suppress(AttributeError):
        return soup.title.string


def _extract_site_name_from_soup(soup: bs4.BeautifulSoup):
    if site_name_tag := soup.find("meta", property="og:site_name", content=True):
        return site_name_tag.get("content")
    return None


@irc3.plugin
class UrlInfo(Plugin):
    _max_bytes = 10 * 1000 * 1000  # 10M
    _url_regex = re.compile(r"https?://\S+", re.IGNORECASE | re.UNICODE)
    _max_title_length = 300
    _request_timeout = 5
    _html_mimetypes = ["text/html", "application/xhtml+xml"]
    _request_chunk_size = 1024  # Bytes
    _allowed_content_types = ["text", "video", "application"]

    def __init__(self, bot):
        super().__init__(bot)
        self._ignore_nicks: list[str] = self.config.get("ignore_nicks", "").split()
        self._ignore_hostnames: list[str] = self.config.get("ignore_hostnames", [])
        self._real_user_agent: str = self.requests.headers.get("User-Agent")
        self._fake_user_agent: str = self.config.get(
            "fake_useragent", "Googlebot/2.1 (+http://www.google.com/bot.html)"
        )
        self._fake_useragent_hostnames: list[str] = self.config.get(
            "fake_useragent_hostnames", []
        )

    @irc3.event(
        rf"(?iu):(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>#\S+) :(?P<data>.*{_url_regex.pattern}).*"
    )
    def on_url(self, mask, target, data):  # noqa: C901
        if mask.nick in self._ignore_nicks or data.startswith(
            (self.bot.config.cmd, f"{self.bot.nick}: ")
        ):
            return

        urls = [_clean_url(url) for url in set(self._url_regex.findall(data))] or []
        for url in urls:
            if urlparse(url).hostname in self._ignore_hostnames:
                urls.remove(url)

        if not urls:
            return

        random.shuffle(urls)
        urls = urls[:3]

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
            messages = []
            self.logger.debug(f"Retrieving page titles for {urls}")

            future_to_url = {
                executor.submit(self._process_url, url): url for url in urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                hostname = urlparse(url).hostname

                try:
                    hostname, title, mimetype, size = future.result()
                except InvalidIPAddressError:
                    return
                except ContentTypeNotAllowedError as ex:
                    self.logger.debug(ex)
                except (socket.gaierror, ValueError, requests.RequestException) as ex:
                    hostname = style(hostname, fg=Color.RED)

                    with contextlib.suppress(AttributeError, IndexError):
                        ex = ex.args[0].reason

                    error = style(ex, bold=True)
                    if isinstance(ex, requests.RequestException):
                        if ex.response is not None and ex.response.reason is not None:
                            status_code = style(ex.response.status_code, bold=True)
                            error = style(ex.response.reason, bold=True)
                            messages.append(f"[ {hostname} ] {status_code} {error}")
                        return
                    messages.append(f"[ {hostname} ] {error}")
                # no exception
                else:
                    hostname = style(hostname, fg=Color.GREEN)
                    if title is not None:
                        title = style(title, bold=True)
                        reply = f"[ {hostname} ] {title}"
                        if (size and mimetype) and mimetype != "text/html":
                            size = naturalsize(size)
                            reply = f"{reply} ({size} - {mimetype})"
                        messages.append(reply)

            # Send all parsed URLs now that we have them all.
            if messages:
                pipe_character = style(" | ", fg=Color.LIGHT_GRAY)
                self.bot.privmsg(target, pipe_character.join(messages))

    def _stream_response(self, response: requests.Response) -> str:
        start_time = time.time()
        content = StringIO()

        for chunk in response.iter_content(self._request_chunk_size):
            if time.time() - start_time >= self._request_timeout:
                raise RequestTimeout(
                    f"Request timed out ({self._request_timeout} seconds)."
                )
            if not chunk:  # filter out keep-alive new chunks
                continue
            content_length = content.write(chunk.decode("UTF-8", errors="ignore"))
            if content_length > self._max_bytes:
                size = naturalsize(content_length)
                raise ResponseBodyTooLarge(
                    f"Couldn't find the page title within {size}."
                )

        return content.getvalue()

    def _process_url(self, url: str):
        urlp = urlparse(url)
        if urlp.netloc.lower().removeprefix("www.") == "twitter.com":
            urlp = urlp._replace(netloc="nitter.net")
        url = urlp.geturl()

        hostname = urlp.hostname
        self._validate_ip_address(hostname)
        hostname = hostname.removeprefix("www.")

        # Spoof user agent for certain sites so they give up their secrets.
        request = copy(self.requests)
        if any(
            f".{hostname}".endswith(f".{host}")
            for host in self._fake_useragent_hostnames
        ):
            request.headers.update({"User-Agent": self._fake_user_agent})

        with request.get(url, stream=True) as response:
            if response.status_code != requests.codes.ok:
                response.raise_for_status()

            content_type = response.headers.get("Content-Type")
            self._validate_content_type(content_type)

            title, size = self._extract_title_and_size(response, content_type)

        return hostname, title, content_type, size

    def _validate_ip_address(self, hostname: str):
        for _, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
            ip = ipaddress.ip_address(sockaddr[0])
            if not ip.is_global:
                raise InvalidIPAddressError(
                    f"{hostname} is not a publicly routable address."
                )

    def _validate_content_type(self, content_type: str):
        if content_type:
            header: ContentTypeHeader = EmailPolicy.header_factory(
                "content-type", content_type
            )
            main_type = header.maintype
            if main_type not in self._allowed_content_types:
                raise ContentTypeNotAllowedError(
                    f"{main_type} not in {self._allowed_content_types}"
                )

    def _extract_title_and_size(self, response: requests.Response, content_type: str):
        title = None
        size = int(response.headers.get("Content-Length", 0))
        content_disposition = response.headers.get("Content-Disposition")
        if content_disposition:
            header: ContentDispositionHeader = EmailPolicy.header_factory(
                "content-disposition", content_disposition
            )
            title = header.params.get("filename")
        elif content_type in self._html_mimetypes or content_type == "text/plain":
            content = self._stream_response(response)
            if content and not size:
                size = len(content.encode("UTF-8"))

            soup = bs4.BeautifulSoup(content, "html5lib")
            title = _extract_title_from_soup(soup)

            site_name = _extract_site_name_from_soup(soup)
            if (site_name and len(site_name) < (site_name_max_size := 16)) and (
                len(site_name) > site_name_max_size
            ):
                site_name = truncate_with_ellipsis(title, site_name_max_size)

            if not title and (content and content_type not in self._html_mimetypes):
                title = re.sub(r"\s+", " ", " ".join(content.split("\n")))

        if title:
            title = unstyle(html.unescape(title).strip())
            if len(title) > self._max_title_length:
                title = truncate_with_ellipsis(title, self._max_title_length)

        return title, size
