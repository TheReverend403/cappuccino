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
import random
import re
import socket
import time
from io import StringIO
from urllib.parse import urlparse

import irc3
import requests
from bs4 import BeautifulSoup
from humanize import naturalsize

from util.formatting import Color, style, unstyle

_URL_FINDER = re.compile(r'(?:https?://\S+)', re.IGNORECASE | re.UNICODE)
_BRACES = [('{', '}'), ('<', '>'), ('[', ']'), ('(', ')')]
_DEFAULT_MAX_BYTES = 655360  # 64K
_MAX_TITLE_LENGTH = 128
_REQUEST_TIMEOUT = 5
_HOSTNAME_CLEANUP_REGEX = re.compile(r'^www\.', re.IGNORECASE | re.UNICODE)
_FORCE_IPV4_HOSTNAMES = ['www.youtube.com', 'youtube.com', 'youtu.be']
_HTML_MIMETYPES = ['text/html', 'application/xhtml+xml']
_REQUEST_CHUNK_SIZE = 256  # Bytes
_ALLOWED_CONTENT_TYPES = ['text', 'video', 'application']


class ResponseBodyTooLarge(requests.RequestException):
    pass


class InvalidIPAddress(Exception):
    pass


class ContentTypeNotAllowed(Exception):
    pass


class RequestTimeout(requests.RequestException):
    pass


original_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_wrapper(host, port, family=0, type=0, proto=0, flags=0):
    """
    Some sites like YouTube like to block certain IPv6 ranges, so forcing IPv4 is necessary to get info on those URLs.
    Because neither requests, urllib, or HTTPRequest provide a way to do that, it's necessary to bypass them and
    go straight to the Python socket library and wrap it's getaddrinfo function transparently to return only
    IPv4 addresses for certain hosts.

    This function requires `socket.getaddrinfo = getaddrinfo_wrapper` somewhere early in a script's startup,
    preferably before any network requests are made.
    """
    family = socket.AF_INET if host in _FORCE_IPV4_HOSTNAMES else family
    return original_getaddrinfo(host, port, family, type, proto, flags)


def _read_stream(response: requests.Response, max_bytes: int = _DEFAULT_MAX_BYTES) -> str:
    start_time = time.time()
    content = StringIO()

    for chunk in response.iter_content(_REQUEST_CHUNK_SIZE):
        if time.time() - start_time >= _REQUEST_TIMEOUT:
            raise RequestTimeout(f'Request timed out ({_REQUEST_TIMEOUT} seconds).')
        if not chunk:  # filter out keep-alive new chunks
            continue
        content_length = content.write(chunk.decode('UTF-8', errors='ignore'))
        if '</title>' in content.getvalue():
            break
        if content_length > max_bytes:
            size = naturalsize(content_length, gnu=True)
            raise ResponseBodyTooLarge(f'Couldn\'t find the page title within {size}.')

    return content.getvalue()


def _parse_url(url: str, session):
    hostname = urlparse(url).hostname
    for (_, _, _, _, sockaddr) in socket.getaddrinfo(hostname, None):
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global:
            raise InvalidIPAddress(f'{hostname} is not a publicly routable address.')

    hostname = _HOSTNAME_CLEANUP_REGEX.sub('', hostname)
    with session.get(url, stream=True) as response:
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        content_type = response.headers.get('Content-Type')
        if content_type:
            content_type, _ = cgi.parse_header(content_type)
            main_type = content_type.split('/')[0]
            if main_type not in _ALLOWED_CONTENT_TYPES:
                raise ContentTypeNotAllowed(f'{main_type} not in {_ALLOWED_CONTENT_TYPES}')

        title = None
        size = int(response.headers.get('Content-Length', 0))
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            _, params = cgi.parse_header(content_disposition)
            title = params.get('filename')
        elif content_type in _HTML_MIMETYPES or content_type == 'text/plain':
            content = _read_stream(response)
            try:
                title = BeautifulSoup(content, 'html.parser').title.string
            except AttributeError:
                if content and content_type not in _HTML_MIMETYPES:
                    title = re.sub(r'\s+', ' ', ' '.join(content.split('\n')))

        if title:
            title = unstyle(html.unescape(title).strip())
            if len(title) > _MAX_TITLE_LENGTH:
                title = ''.join(title[:_MAX_TITLE_LENGTH - 3]) + '...'
    return hostname, title, content_type, size


def _clean_url(url: str):
    if url:
        url = url.rstrip('\'.,"\1')
        for left_brace, right_brace in _BRACES:
            if left_brace not in url and url.endswith(right_brace):
                url = url.rstrip(right_brace)
    return url


@irc3.plugin
class UrlInfo(object):
    requires = [
        'plugins.botui'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config.get(__name__, {})
        self.ignore_nicks = self.config.get('ignore_nicks', '').split()
        self.ignore_hostnames = self.config.get('ignore_hostnames', '').split()
        socket.getaddrinfo = _getaddrinfo_wrapper

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>#\S+) :(?iu)(?P<data>.*{0}).*'.format(_URL_FINDER.pattern))
    def on_url(self, mask, target, data):
        if mask.nick in self.ignore_nicks or data.startswith(self.bot.config.cmd) or data.startswith(
                f'{self.bot.nick}: '):
            return

        urls = [_clean_url(url) for url in set(_URL_FINDER.findall(data))] or []
        for url in urls:
            if urlparse(url).hostname in self.ignore_hostnames:
                urls.remove(url)

        if not urls:
            return

        random.shuffle(urls)
        urls = urls[:3]

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
            messages = []
            self.bot.log.debug(f'Retrieving page titles for {urls}')

            future_to_url = {executor.submit(_parse_url, url, self.bot.requests): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                hostname = urlparse(url).hostname

                try:
                    hostname, title, mimetype, size = future.result()
                except InvalidIPAddress:
                    return
                except ContentTypeNotAllowed as ex:
                    self.bot.log.debug(ex)
                except (socket.gaierror, ValueError, requests.RequestException) as ex:
                    hostname = style(hostname, fg=Color.RED)
                    error = style(ex, bold=True)

                    if type(ex) == requests.RequestException:
                        if ex.response is not None and ex.response.reason is not None:
                            status_code = style(ex.response.status_code, bold=True)
                            error = style(ex.response.reason, bold=True)
                            messages.append(f'[ {hostname} ] {status_code} {error}')
                        return
                    else:
                        messages.append(f'[ {hostname} ] {error}')
                # no exception
                else:
                    hostname = style(hostname, fg=Color.GREEN)
                    if title is not None and mimetype is not None:
                        title = style(title, bold=True)
                        size = f' - {naturalsize(size, gnu=True)}' if size else ''
                        reply = f'[ {hostname} ] {title} ({mimetype}{size})'
                        messages.append(reply)

            # Send all parsed URLs now that we have them all.
            if messages:
                pipe_character = style(' | ', fg=Color.LIGHT_GRAY)
                self.bot.privmsg(target, pipe_character.join(messages))
