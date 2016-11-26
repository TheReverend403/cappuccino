import cgi
import ipaddress
import socket
import time
from contextlib import closing

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

ALLOWED_CONTENT_TYPES = ['text', 'video', 'image', 'application']


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
        if content.write(chunk.decode('UTF-8', errors='ignore')) > max_bytes:
            raise ResponseBodyTooLarge('Couldn\'t find page title in less than {0}'.format(size_fmt(max_bytes)))
        if '</title>' in content.getvalue():
            break

    return content.getvalue()


def _parse_url(url):
    with closing(requests.get(url, **REQUEST_OPTIONS)) as response:
        if response.status_code != requests.codes.ok:
            response.raise_for_status()

        content_type = response.headers.get('Content-Type')
        main_type = None
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
            try:
                title = params['filename']
            except KeyError:
                pass
        elif main_type == 'text':
            try:
                content = _read_stream(response)
                title = BeautifulSoup(content, 'html.parser').title.string
            except AttributeError:
                pass

        if title:
            title = title.strip()
            if len(title) > MAX_TITLE_LENGTH:
                title = ''.join(title[:MAX_TITLE_LENGTH - 3]) + '...'
        return title, content_type, size


@irc3.plugin
class UrlInfo(object):
    requires = [
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        try:
            self.ignore_nicks = self.bot.config[__name__]['ignore_nicks'].split()
        except KeyError:
            self.ignore_nicks = []
        socket.getaddrinfo = getaddrinfo_wrapper
        requests.packages.urllib3.disable_warnings()

    @irc3.event(r':(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>#\S+) :(?i)(?P<data>.*{0}).*'.format(URL_FINDER.pattern))
    def on_url(self, mask, target, data):
        if mask.nick in self.ignore_nicks or data.startswith(self.bot.config.cmd):
            return

        urls = URL_FINDER.findall(data)
        if not urls:
            return

        messages = []
        random.shuffle(urls)
        for url in urls[-3:]:
            url = url.rstrip('\'.,"')
            for left_brace, right_brace in BRACES:
                if left_brace not in url and url.endswith(right_brace):
                    url = url.rstrip(right_brace)

            self.bot.log.info('Fetching page title for {0}'.format(url))

            hostname = urlparse(url).hostname
            try:
                for (_, _, _, _, sockaddr) in socket.getaddrinfo(hostname, None):
                    ip = ipaddress.ip_address(sockaddr[0])
                    if ip.is_private or ip.is_reserved or ip.is_link_local or ip.is_loopback or ip.is_multicast:
                        raise InvalidIPAddress('{0} is not a publicly routable address.'.format(hostname))
            except (socket.gaierror, ValueError, InvalidIPAddress) as err:
                self.bot.log.error(err)
                messages.append('[ {0} ] {1}'.format(
                    self.bot.format(hostname, color=self.bot.color.RED), self.bot.format(err, bold=True)))
                continue

            hostname = HOSTNAME_CLEANUP_REGEX.sub('', hostname)
            try:
                title, mimetype, size = _parse_url(url)

                if not title:
                    title = self.bot.format('No Title', color=self.bot.color.RED)

                reply = '[ {0} ] {1}'.format(
                    self.bot.format(hostname, color=self.bot.color.GREEN), self.bot.format(title, bold=True))
                if mimetype:
                    reply += ' ({0})'.format(mimetype)
                if size:
                    reply += ' ({0})'.format(size_fmt(size))

                messages.append(reply)

            except ContentTypeNotAllowed:
                continue

            except requests.RequestException as err:
                self.bot.log.error(err)
                if err.response is not None and err.response.reason is not None:
                    messages.append('[ {0} ] {1} {2}'.format(
                        self.bot.format(hostname, color=self.bot.color.RED),
                        self.bot.format(err.response.status_code, bold=True),
                        self.bot.format(err.response.reason, bold=True)))
                    continue

                messages.append('[ {0} ] {1}'.format(
                    self.bot.format(hostname, color=self.bot.color.RED), self.bot.format(err, bold=True)))

        if messages:
            self.bot.privmsg(target, ' | '.join(messages))
