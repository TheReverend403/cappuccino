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

FORCE_IPV4_HOSTNAMES = ['www.youtube.com', 'youtube.com', 'youtu.be']

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

original_getaddrinfo = socket.getaddrinfo


def getaddrinfo_wrapper(host, port, family=0, type=0, proto=0, flags=0):
    """
    Some sites like YouTube like to block certain IPv6 ranges, so forcing IPv4 is necessary to get info on those URLs.
    Because neither requests, urllib, or HTTPRequest provide a way to do that, it's necessary to bypass them and
    go straight to the Python socket library and wrap it's getaddrinfo function transparently to return only
    IPv4 addresses for certain hosts.

    This function requires `socket.getaddrinfo = getaddrinfo_wrapper` somewhere early in a script's startup,
    preferably before any network requests are made.
    """
    family = socket.AF_INET if host in FORCE_IPV4_HOSTNAMES else family
    return original_getaddrinfo(host, port, family, type, proto, flags)


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
        socket.getaddrinfo = getaddrinfo_wrapper

    def _find_title(self, content, content_disposition=None):
        title = ''
        try:
            title = html.fromstring(content).findtext('.//title')
        except ParserError as err:
            self.bot.log.warn(err)
            pass

        if not title and content_disposition:
            _, params = cgi.parse_header(content_disposition)
            try:
                title = params['filename']
            except KeyError:
                pass

        title = title.strip()
        if len(title) > MAX_TITLE_LENGTH:
            title = ''.join(title[:MAX_TITLE_LENGTH - 3]) + '...'
        return title or self.bot.color('No Title', 4)

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?i)(?P<data>.*https?://\S+).*')
    def on_url(self, target, data):
        urls = URL_FINDER.findall(data)
        if not urls:
            return

        # Only handle 1 URL until I get the hang of Python async.
        for url in urls[-1:]:
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
                    if response.status_code != requests.codes.ok:
                        response.raise_for_status()

                    mimetype, _ = cgi.parse_header(response.headers.get('Content-Type'))
                    maintype = mimetype.split('/')[0]
                    if maintype not in CONTENT_TYPES_AND_LIMITS:
                        continue

                    try:
                        size, content = _read_stream(response, CONTENT_TYPES_AND_LIMITS[maintype])
                    except ResponseBodyTooLarge as err:
                        self.bot.privmsg(target, '[ {0} ] {1}'.format(self.bot.color(hostname, 4), self.bot.bold(err)))
                        continue

                    if not content:
                        continue

                title = self._find_title(content, response.headers.get('Content-Disposition'))
                self.bot.privmsg(target, '[ {0} ] {1} ({2}) ({3})'.format(
                    self.bot.color(hostname, 3), self.bot.bold(title), size_fmt(size), mimetype))

            except requests.RequestException as err:
                if err.response is not None and err.response.reason is not None:
                    self.bot.privmsg(target, '[ {0} ] {1} {2}'.format(
                        self.bot.color(hostname, 4),
                        self.bot.bold(err.response.status_code),
                        self.bot.bold(err.response.reason)))
                    continue
                self.bot.privmsg(target, '[ {0} ] {1}'.format(self.bot.color(hostname, 4), self.bot.bold(err)))
