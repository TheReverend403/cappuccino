import ipaddress
import socket
from contextlib import closing
from urllib.parse import urlparse

import irc3
import re
import requests
from io import BytesIO
from lxml import html

URL_FINDER = re.compile(r'(?:http|https)(?:://\S+)', re.IGNORECASE)

# 640k
MAX_BYTES = 655360
MAX_TITLE_LENGTH = 150
USER_AGENT = 'ricedb/urlinfo.py (https://github.com/TheReverend403/ricedb)'
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB, en-US, en'
}

REQUEST_PARAMS = {
    'timeout': 5,
    'stream': True,
    'allow_redirects': True,
    'headers': DEFAULT_HEADERS
}


def size_fmt(num, suffix='B'):
    # https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def _read_stream(response):
    content = BytesIO()
    size = 0
    chunk_size = 512  # Bytes
    for chunk in response.iter_content(chunk_size):
        content.write(chunk)
        if size > MAX_BYTES:
            return size, None
        size += len(chunk)

    return size, content.getvalue().decode('UTF-8', errors='ignore')


@irc3.plugin
class UrlInfo(object):
    def __init__(self, bot):
        self.bot = bot

    def _find_title(self, content):
        title = html.fromstring(content).findtext('.//title')
        if title:
            title = ''.join(title.strip()[:MAX_TITLE_LENGTH])
            if len(title) == MAX_TITLE_LENGTH:
                title += '...'
        return title or self.bot.color('No Title', 4)

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?P<data>.*https?://\S+).*')
    def on_url(self, target, data):
        urls = URL_FINDER.findall(data)
        if len(urls) == 0:
            return
        for url in urls[-3:]:
            self.bot.log.debug('Parsing hostname for {0}'.format(url))
            hostname = urlparse(url).hostname
            try:
                for (_, _, _, _, sockaddr) in socket.getaddrinfo(hostname, None):
                    ip = ipaddress.ip_address(sockaddr[0])
                    if ip.is_private or ip.is_reserved or ip.is_link_local or ip.is_loopback:
                        continue
            except (socket.gaierror, ValueError) as err:
                self.bot.log.warn(err)
                continue

            self.bot.log.debug('Fetching page title for {0}'.format(url))
            try:
                with closing(requests.get(url, **REQUEST_PARAMS)) as response:
                    if not response.status_code == requests.codes.ok:
                        response.raise_for_status()
                    try:
                        content_type = response.headers.get('Content-Type').split(';')[0]
                    except IndexError:
                        return
                    if content_type not in ['text/html']:
                        return
                    size, content = _read_stream(response)
                    if size > MAX_BYTES:
                        self.bot.privmsg(target, '[ {0} ] - {1}'.format(
                            self.bot.color(hostname, 4), self.bot.bold('Response too large ({0} > {1})'.format(
                                size_fmt(size), size_fmt(MAX_BYTES)))))
                        continue
                    if not content:
                        continue
                    title = self._find_title(content)
                    self.bot.privmsg(target, '[ {0} ] {1} ({2})'.format(
                        self.bot.color(hostname, 3),
                        self.bot.bold(title),
                        size_fmt(size)))

            except requests.RequestException as err:
                if err.response and err.response.status_code and err.response.reason:
                    self.bot.privmsg(target, '[ {0} ] - {1} {2}'.format(
                        self.bot.color(hostname, 4),
                        self.bot.bold(err.response.status_code),
                        self.bot.bold(err.response.reason)))
                else:
                    self.bot.privmsg(target, '[ {0} ] - {1}'.format(self.bot.color(hostname, 4), self.bot.bold(err)))
