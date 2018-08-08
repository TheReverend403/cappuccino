import cgi
import concurrent
import ipaddress
import socket
import time
from contextlib import closing

import html
import random
from bs4 import BeautifulSoup
from io import StringIO
from urllib.parse import urlparse

import irc3
import re
import requests

URL_FINDER = re.compile(r'(?:https?://\S+)', re.IGNORECASE)

BRACES = [('{', '}'), ('<', '>'), ('[', ']'), ('(', ')')]
DEFAULT_MAX_BYTES = 655360  # 64K
MAX_TITLE_LENGTH = 128
USER_AGENT = 'ricedb/urlinfo.py (https://github.com/TheReverend403/ricedb)'
REQUEST_TIMEOUT = 5
HOSTNAME_CLEANUP_REGEX = re.compile('^www\.', re.IGNORECASE)

FORCE_IPV4_HOSTNAMES = ['www.youtube.com', 'youtube.com', 'youtu.be']

HTML_MIMETYPES = ['text/html', 'application/xhtml+xml']
REQUEST_CHUNK_SIZE = 256  # Bytes
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB,en-US,en;q=0.5'
}

REQUEST_OPTIONS = {
    'timeout': REQUEST_TIMEOUT,
    'stream': True,
    'allow_redirects': True,
    'verify': False,
    'headers': REQUEST_HEADERS
}

ALLOWED_CONTENT_TYPES = ['text', 'video', 'application']


class ResponseBodyTooLarge(requests.RequestException):
    pass


class InvalidIPAddress(Exception):
    pass


class ContentTypeNotAllowed(Exception):
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
    content = StringIO()

    for chunk in response.iter_content(REQUEST_CHUNK_SIZE):
        if time.time() - start_time >= REQUEST_TIMEOUT:
            raise RequestTimeout('Request timed out')
        if not chunk:  # filter out keep-alive new chunks
            continue
        content_length = content.write(chunk.decode('UTF-8', errors='ignore'))
        if '</title>' in content.getvalue():
            break
        if content_length > max_bytes:
            raise ResponseBodyTooLarge('Couldn\'t find page title in less than {0}'.format(size_fmt(content_length)))

    return content.getvalue()


def _parse_url(url):
    hostname = urlparse(url).hostname
    for (_, _, _, _, sockaddr) in socket.getaddrinfo(hostname, None):
        ip = ipaddress.ip_address(sockaddr[0])
        if not ip.is_global:
            raise InvalidIPAddress('{0} is not a publicly routable address.'.format(hostname))

    hostname = HOSTNAME_CLEANUP_REGEX.sub('', hostname)
    with closing(requests.get(url, **REQUEST_OPTIONS)) as response:
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        content_type = response.headers.get('Content-Type')
        if content_type:
            content_type, _ = cgi.parse_header(content_type)
            main_type = content_type.split('/')[0]
            if main_type not in ALLOWED_CONTENT_TYPES:
                raise ContentTypeNotAllowed('{0} not in {1}'.format(main_type, ALLOWED_CONTENT_TYPES))

        title = None
        size = int(response.headers.get('Content-Length', 0))
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            _, params = cgi.parse_header(content_disposition)
            title = params.get('filename')
        elif content_type in HTML_MIMETYPES or content_type == 'text/plain':
            content = _read_stream(response)
            try:
                title = BeautifulSoup(content, 'html.parser').title.string
            except AttributeError:
                if content and content_type not in HTML_MIMETYPES:
                    title = re.sub('\s+', ' ', ' '.join(content.split('\n')))

        if title:
            title = html.unescape(title).strip()
            if len(title) > MAX_TITLE_LENGTH:
                title = ''.join(title[:MAX_TITLE_LENGTH - 3]) + '...'
    return hostname, title, content_type, size


def _clean_url(url):
    if url:
        url = url.rstrip('\'.,"')
        for left_brace, right_brace in BRACES:
            if left_brace not in url and url.endswith(right_brace):
                url = url.rstrip(right_brace)
    return url


@irc3.plugin
class UrlInfo(object):
    requires = [
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        socket.getaddrinfo = getaddrinfo_wrapper
        requests.packages.urllib3.disable_warnings()

    def load_config(self):
        try:
            self.ignore_nicks = self.bot.config[__name__]['ignore_nicks'].split()
        except KeyError:
            self.ignore_nicks = []

        try:
            self.ignore_hostnames= self.bot.config[__name__]['ignore_hostnames'].split()
        except KeyError:
            self.ignore_hostnames = []

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>#\S+) :(?i)(?P<data>.*{0}).*'.format(URL_FINDER.pattern))
    def on_url(self, mask, target, data):
        if mask.nick in self.ignore_nicks or data.startswith(self.bot.config.cmd):
            return

        urls = [_clean_url(url) for url in set(URL_FINDER.findall(data))] or []
        for url in urls:
            if urlparse(url).hostname in self.ignore_hostnames:
                urls.remove(url)

        if not urls:
            return

        random.shuffle(urls)
        urls = urls[:3]

        messages = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            self.bot.log.debug('Retrieving page titles for {0}'.format(urls))
            future_to_url = {executor.submit(_parse_url, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                hostname = urlparse(url).hostname

                try:
                    hostname, title, mimetype, size = future.result()
                except ContentTypeNotAllowed as ex:
                    self.bot.log.debug(ex)
                except (socket.gaierror, ValueError, InvalidIPAddress) as ex:
                    self.bot.log.error(ex)
                    messages.append('[ {0} ] {1}'.format(self.bot.format(hostname, color=self.bot.color.RED),
                                                         self.bot.format(ex, bold=True)))

                except requests.RequestException as ex:
                    self.bot.log.error(ex)
                    if ex.response is not None and ex.response.reason is not None:
                        messages.append('[ {0} ] {1} {2}'.format(
                            self.bot.format(hostname, color=self.bot.color.RED),
                            self.bot.format(ex.response.status_code, bold=True),
                            self.bot.format(ex.response.reason, bold=True)))
                    else:
                        messages.append('[ {0} ] {1}'.format(
                            self.bot.format(hostname, color=self.bot.color.RED), self.bot.format(ex, bold=True)))
                else:
                    reply = '[ {0} ]'.format(self.bot.format(hostname, color=self.bot.color.GREEN))

                    if title:
                        reply += ' {0}'.format(self.bot.format(title, bold=True))
                    if mimetype:
                        reply += ' ({0})'.format(mimetype)
                    if size and mimetype not in HTML_MIMETYPES:
                        reply += ' ({0})'.format(size_fmt(size))

                    messages.append(reply)

        if messages:
            self.bot.privmsg(target, self.bot.format(' | ', color=self.bot.color.LIGHT_GRAY, reset=True).join(messages))
