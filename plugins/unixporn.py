import os
import random
import threading
try:
    import ujson as json
except ImportError:
    import json

import irc3
import time
from praw import Reddit

MAX_TITLE_LENGTH = 64

@irc3.plugin
class Unixporn(object):

    requires = [
        'plugins.formatting'
    ]

    def __init__(self, bot):
        self.bot = bot
        self.submission_cache_file = os.path.join('data', 'unixporn_cache.json')
        self.submission_cache = []

        datadir = os.path.dirname(self.submission_cache_file)
        try:
            with open(self.submission_cache_file, 'r') as fd:
                self.submission_cache = json.load(fd)
        except FileNotFoundError:
            # Cache file itself doesn't need to exist on first run, it will be created on first write.
            if not os.path.exists(datadir):
                os.mkdir(datadir)
                self.bot.log.debug('Created {0}/ directory'.format(datadir))

        try:
            self.channel = '#' + self.bot.config[__name__]['channel']
            self.client_id = self.bot.config[__name__]['reddit_client_id']
            self.client_secret = self.bot.config[__name__]['reddit_client_secret']
        except KeyError as err:
            self.bot.log.exception(err)
            return

        self.praw = Reddit(
            user_agent='ricedb/unixporn.py (https://github.com/TheReverend403/ricedb)',
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        self.praw_thread = threading.Thread(target=self.fetch_latest_posts, name=__name__, daemon=True)

    def fetch_latest_posts(self):
        while self.praw_thread.is_alive():
            time.sleep(5)
            self.bot.log.debug('Fetching latest /r/unixporn posts')
            for submission in self.praw.subreddit('unixporn').new(limit=5):
                if submission.id in self.submission_cache:
                    self.bot.log.debug('Ignoring "%s" because I\'ve seen it before', submission.title)
                    continue

                if submission.is_self:
                    self.bot.log.debug('Ignoring "%s" because it is a self-post', submission.title)
                    continue

                self.submission_cache.append(submission.id)
                with open(self.submission_cache_file, 'w') as fd:
                    json.dump(self.submission_cache, fd)

                title = submission.title
                if len(title) > MAX_TITLE_LENGTH:
                    title = ''.join(title[:MAX_TITLE_LENGTH - 3]) + '...'

                msg = '[ {0} ] {1} by /u/{2} - {3} - {4}'.format(
                    self.bot.format('unixporn', bold=True, color=self.bot.color.YELLOW),
                    self.bot.format(title, bold=True),
                    submission.author,
                    self.bot.format(submission.url, color=self.bot.color.BLUE, bold=True),
                    self.bot.format(submission.shortlink, color=self.bot.color.BLUE, bold=True)
                )

                # Add random delay to avoid posting all submissions at once.
                time.sleep(random.randint(3, 10))
                self.bot.loop.call_soon_threadsafe(self.bot.privmsg, self.channel, msg)

    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel):
        if mask.nick == self.bot.nick and channel.lower() == self.channel and not self.praw_thread.is_alive():
            self.bot.log.info('Started /r/unixporn fetcher')
            self.praw_thread.start()
