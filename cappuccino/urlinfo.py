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

import cgi
import concurrent
import html
import ipaddress
import logging
import random
import re
import socket
import time
from io import StringIO
from urllib.parse import urlparse

import bs4
import irc3
import requests
from humanize import naturalsize

from cappuccino.util.formatting import Color, style, unstyle

log = logging.getLogger(__name__)


class ResponseBodyTooLarge(requests.RequestException):
    pass


class InvalidIPAddress(Exception):
    pass


class ContentTypeNotAllowed(Exception):
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


@irc3.plugin
class UrlInfo(object):
    requires = ["cappuccino.botui"]

    _max_bytes = 10 * 1000 * 1000  # 10M
    _url_regex = re.compile(r"(?:https?://\S+)", re.IGNORECASE | re.UNICODE)
    _hostname_cleanup_regex = re.compile(r"^www\.", re.IGNORECASE | re.UNICODE)
    _max_title_length = 128
    _request_timeout = 5
    _html_mimetypes = ["text/html", "application/xhtml+xml"]
    _request_chunk_size = 1024  # Bytes
    _allowed_content_types = ["text", "video", "application"]

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config.get(__name__, {})
        self.ignore_nicks = self.config.get("ignore_nicks", "").split()
        self.ignore_hostnames = self.config.get("ignore_hostnames", "").split()
        self.real_user_agent = self.bot.requests.headers.get("User-Agent")
        self.fake_user_agent = self.config.get(
            "fake_useragent", "Googlebot/2.1 (+http://www.google.com/bot.html)"
        )
        self.fake_useragent_hostnames = self.config.get(
            "fake_useragent_hostnames", ""
        ).split()

    @irc3.event(
        rf":(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>#\S+) :(?iu)(?P<data>.*{_url_regex.pattern}).*"
    )
    def on_url(self, mask, target, data):
        if (
            mask.nick in self.ignore_nicks
            or data.startswith(self.bot.config.cmd)
            or data.startswith(f"{self.bot.nick}: ")
        ):
            return

        urls = [_clean_url(url) for url in set(self._url_regex.findall(data))] or []
        for url in urls:
            if urlparse(url).hostname in self.ignore_hostnames:
                urls.remove(url)

        if not urls:
            return

        random.shuffle(urls)
        urls = urls[:3]

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
            messages = []
            log.debug(f"Retrieving page titles for {urls}")

            future_to_url = {
                executor.submit(self._process_url, url): url for url in urls
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                hostname = urlparse(url).hostname

                try:
                    hostname, title, mimetype, size = future.result()
                except InvalidIPAddress:
                    return
                except ContentTypeNotAllowed as ex:
                    log.debug(ex)
                except (socket.gaierror, ValueError, requests.RequestException) as ex:
                    hostname = style(hostname, fg=Color.RED)

                    try:
                        ex = ex.args[0].reason
                    except (AttributeError, IndexError):
                        pass

                    error = style(ex, bold=True)
                    if type(ex) == requests.RequestException:
                        if ex.response is not None and ex.response.reason is not None:
                            status_code = style(ex.response.status_code, bold=True)
                            error = style(ex.response.reason, bold=True)
                            messages.append(f"[ {hostname} ] {status_code} {error}")
                        return
                    else:
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
        hostname = urlparse(url).hostname
        for (_, _, _, _, sockaddr) in socket.getaddrinfo(hostname, None):
            ip = ipaddress.ip_address(sockaddr[0])
            if not ip.is_global:
                raise InvalidIPAddress(
                    f"{hostname} is not a publicly routable address."
                )

        hostname = self._hostname_cleanup_regex.sub("", hostname)

        # Spoof user agent for certain sites so they give up their secrets.
        if any(host.endswith(hostname) for host in self.fake_useragent_hostnames):
            self.bot.requests.headers.update({"User-Agent": self.fake_user_agent})

        with self.bot.requests.get(url, stream=True) as response:
            # Reset to the real user agent after the request.
            self.bot.requests.headers.update({"User-Agent": self.real_user_agent})

            if response.status_code != requests.codes.ok:
                response.raise_for_status()

            content_type = response.headers.get("Content-Type")
            if content_type:
                content_type, _ = cgi.parse_header(content_type)
                main_type = content_type.split("/")[0]
                if main_type not in self._allowed_content_types:
                    raise ContentTypeNotAllowed(
                        f"{main_type} not in {self._allowed_content_types}"
                    )

            title = None
            size = int(response.headers.get("Content-Length", 0))
            content_disposition = response.headers.get("Content-Disposition")
            if content_disposition:
                _, params = cgi.parse_header(content_disposition)
                title = params.get("filename")
            elif content_type in self._html_mimetypes or content_type == "text/plain":
                content = self._stream_response(response)
                if content and not size:
                    size = len(content.encode("UTF-8"))

                soup = bs4.BeautifulSoup(content, "html5lib")
                if title_tag := soup.find("meta", property="og:title", content=True):
                    title = title_tag.get("content")
                else:
                    try:
                        title = soup.title.string
                    except AttributeError:
                        pass

                site_name = None
                if site_name_tag := soup.find(
                    "meta", property="og:site_name", content=True
                ):
                    site_name = site_name_tag.get("content")

                if site_name and len(site_name) < (site_name_max_size := 15):
                    if len(site_name) > site_name_max_size:
                        site_name = "".join(title[: site_name_max_size - 3]) + "..."
                    hostname = site_name

                if description_tag := soup.find(
                    "meta", property="og:description", content=True
                ):
                    description = description_tag.get("content")

                    # GitHub's repo <title> is better than the og:title
                    # How to check if it's a repo? Simple.
                    # The description on GitHub ends with the repo name (og:title).
                    if site_name == "GitHub" and title in description:
                        title = soup.title.string.replace("GitHub - ", "", 1)

                    if site_name == "Twitter" and description:
                        title = f"{title}: {description}"

                if not title and (content and content_type not in self._html_mimetypes):
                    title = re.sub(r"\s+", " ", " ".join(content.split("\n")))

            if title:
                title = unstyle(html.unescape(title).strip())
                if len(title) > self._max_title_length:
                    title = "".join(title[: self._max_title_length - 3]) + "..."

        return hostname, title, content_type, size
