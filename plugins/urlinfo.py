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
USER_AGENT = 'ricedb/urlinfo.py (https://github.com/TheReverend403/ricedb)'
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-GB, en-US, en'
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
            response.close()
            return size, None
        size += len(chunk)

    return size, content.getvalue().decode('UTF-8', errors='ignore')


@irc3.plugin
class UrlInfo(object):
    def __init__(self, bot):
        self.bot = bot

    @irc3.event(r'.*PRIVMSG (?P<target>#\S+) :(?P<data>.*https?://\S+).*')
    def on_url(self, target, data):
        urls = URL_FINDER.findall(data)
        if len(urls) == 0:
            return
        for url in urls[-3:]:
            self.bot.log.info('Parsing hostname for {0}'.format(url))
            hostname = urlparse(url).hostname
            try:
                for (_, _, _, _, sockaddr) in socket.getaddrinfo(hostname, None):
                    ip = ipaddress.ip_address(sockaddr[0])
                    if ip.is_private or ip.is_reserved or ip.is_link_local or ip.is_loopback:
                        continue
            except (socket.gaierror, ValueError) as err:
                self.bot.log.warn(err)
                continue

            self.bot.log.info('Fetching page title for {0}'.format(url))
            try:
                with closing(requests.get(url, stream=True, headers=DEFAULT_HEADERS, allow_redirects=True)) as response:
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
                    title = html.fromstring(content).findtext('.//title')
                    if title:
                        title = ''.join(title.strip()[:150])
                        if len(title) == 150:
                            title += '...'
                        self.bot.privmsg(target, '[ {0} ] {1} ({2})'.format(
                            self.bot.color(hostname, 3),
                            self.bot.bold(title),
                            size_fmt(size)))

            except requests.RequestException as err:
                self.bot.privmsg(target, '[ {0} ] - {1}'.format(self.bot.color(hostname, 4), self.bot.bold(err)))
