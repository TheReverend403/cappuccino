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
        self.submission_cache = []

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
            client_secret=self.client_secret
        )

        self.praw_thread = threading.Thread(target=self.fetch_latest_posts, name=__name__, daemon=True)

    def fetch_latest_posts(self):
        # Clear out old submissions before starting a submission stream to avoid spam.
        self.bot.log.info('Starting /r/unixporn new submission stream')
        self.submission_cache = [submission.id for submission in self.praw.subreddit('unixporn').new(limit=150)]
        subreddit = self.praw.subreddit('unixporn')
        for submission in subreddit.stream.submissions():
            if submission.is_self or '[' not in submission.title:
                self.bot.log.debug('Ignoring %s because it is not a screenshot', submission.id)
                continue

            if submission.id in self.submission_cache:
                self.bot.log.debug('Ignoring %s because I have it cached', submission.id)
                continue

            self.bot.log.info('Got new submission: %s', submission.title)
            self.submission_cache.append(submission.id)

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
            time.sleep(random.randint(5, 10))
            self.bot.loop.call_soon_threadsafe(self.bot.privmsg, self.channel, msg)

    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel):
        if mask.nick == self.bot.nick and channel.lower() == self.channel and not self.praw_thread.is_alive():
            self.praw_thread.start()
