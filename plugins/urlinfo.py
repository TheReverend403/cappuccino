import cgi
import ipaddress
import socket
import time
from contextlib import closing
from urllib.parse import urlparse

import irc3
import re
import requests
from io import BytesIO
from lxml import html
from lxml.etree import ParserError
from requests import Session

URL_FINDER = re.compile(r'(?:http|https)(?:://\S+)', re.IGNORECASE)

DEFAULT_MAX_BYTES = 1048576
MAX_TITLE_LENGTH = 150
USER_AGENT = 'ricedb/urlinfo.py (https://github.com/TheReverend403/ricedb)'
REQUEST_TIMEOUT = 5
HOSTNAME_CLEANUP_REGEX = re.compile('^www\.', re.I)

REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB,en-US,en;q=0.5'
}

REQUEST_OPTIONS = {
    'timeout': REQUEST_TIMEOUT,
    'stream': True,
    'allow_redirects': True,
    'headers': REQUEST_HEADERS
}

CONTENT_TYPES_AND_LIMITS = {
    'text': DEFAULT_MAX_BYTES,
    'video': DEFAULT_MAX_BYTES * 10,
    'image': DEFAULT_MAX_BYTES * 5,
    'application': DEFAULT_MAX_BYTES * 10
}


class ResponseBodyTooLarge(requests.RequestException):
    pass


class RequestTimeout(requests.RequestException):
    pass


def size_fmt(num, suffix='B'):
    # https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def _read_stream(response, max_bytes=DEFAULT_MAX_BYTES):
    start_time = time.time()
    content = BytesIO()
    content_size_header = int(response.headers.get('Content-Length', 0))
    downloaded_size = 0
    chunk_size = int(max_bytes / 64)
    response_body_exception = ResponseBodyTooLarge(
        'Response body is too large. Maximum size is {0}.'.format(size_fmt(max_bytes)))

    if content_size_header > max_bytes:
        raise response_body_exception

    for chunk in response.iter_content(chunk_size):
        if time.time() - start_time >= 5:
            raise RequestTimeout('Request timed out.')
        if not chunk:  # filter out keep-alive new chunks
            continue
        content.write(chunk)
        downloaded_size += len(chunk)
        if downloaded_size > max_bytes:
            raise response_body_exception

    return downloaded_size, content.getvalue().decode('UTF-8', errors='ignore')


@irc3.plugin
class UrlInfo(object):
    requires = [
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.session = Session()
        self.session.headers.update(REQUEST_HEADERS)

    def _find_title(self, response, content):
        title = None
        try:
            title = html.fromstring(content).findtext('.//title')
        except ParserError:
            pass
        if not title:
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                _, params = cgi.parse_header(content_disposition)
                title = params['filename']
        if title:
            title = ''.join(title[:MAX_TITLE_LENGTH])
            if len(title) == MAX_TITLE_LENGTH:
                title += '...'
        return title or self.bot.color('No Title', 4)

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)(?P<data>.*https?://\S+).*')
    def on_url(self, target, data):
        urls = URL_FINDER.findall(data)
        if len(urls) == 0:
            return

        for url in urls[-3:]:
            self.bot.log.debug('Fetching page title for {0}'.format(url))
            hostname = urlparse(url).hostname
            try:
                for (_, _, _, _, sockaddr) in socket.getaddrinfo(hostname, None):
                    ip = ipaddress.ip_address(sockaddr[0])
                    if ip.is_private or ip.is_reserved or ip.is_link_local or ip.is_loopback:
                        continue
            except (socket.gaierror, ValueError) as err:
                self.bot.log.warn(err)
                continue

            hostname = HOSTNAME_CLEANUP_REGEX.sub('', hostname)
            try:
                with closing(self.session.get(url, **REQUEST_OPTIONS)) as response:
                    if not response.status_code == requests.codes.ok:
                        response.raise_for_status()

                    try:
                        content_type = response.headers.get('Content-Type').split(';')[0]
                    except IndexError:
                        return

                    content_type_category = content_type.split('/')[0]
                    if content_type_category not in CONTENT_TYPES_AND_LIMITS:
                        return

                    try:
                        size, content = _read_stream(response, CONTENT_TYPES_AND_LIMITS[content_type_category])
                    except ResponseBodyTooLarge as err:
                        self.bot.privmsg(target, '[ {0} ] {1}'.format(self.bot.color(hostname, 4), self.bot.bold(err)))
                        return

                    if not content:
                        continue

                    title = self._find_title(response, content)
                    self.bot.privmsg(target, '[ {0} ] {1} ({2}) ({3})'.format(
                        self.bot.color(hostname, 3),
                        self.bot.bold(title),
                        size_fmt(size),
                        content_type))

            except requests.RequestException as err:
                if err.response is not None and err.response.reason is not None:
                    self.bot.privmsg(target, '[ {0} ] {1} {2}'.format(
                        self.bot.color(hostname, 4),
                        self.bot.bold(err.response.status_code),
                        self.bot.bold(err.response.reason)))
                    return
                self.bot.privmsg(target, '[ {0} ] {1}'.format(self.bot.color(hostname, 4), self.bot.bold(err)))
