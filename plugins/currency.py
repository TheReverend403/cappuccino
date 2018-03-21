try:
    import ujson as json
except ImportError:
    import json

import irc3
from contextlib import closing

import requests
from irc3.plugins.command import command


@irc3.plugin
class Currency(object):

    def __init__(self, bot):
        self.bot = bot
        self.api_url = 'https://api.coinmarketcap.com/v1/ticker/{0}/?convert={1}'

    @command(permission='view', aliases=['btc', 'crypto'])
    def coin(self, mask, target, args):
        """Shows current exchange rate of cryptocoins to various currencies. Defaults to BTC -> USD.

            %%coin [FROM] [TO]
        """
        from_currency = args['FROM'] or 'bitcoin'
        from_currency = from_currency.lower()
        to_currency = args['TO'] or 'USD'

        api_url = self.api_url.format(from_currency, to_currency.upper())
        value = None

        try:
            with closing(requests.get(api_url)) as response:
                json_data = response.json()
                if 'error' in json_data:
                    self.bot.privmsg(target, f'No such coin. Try using the full name e.g. "ethereum"')
                    return

                currency = response.json()[0]
                print(currency)
                change_1h, change_24h, change_7d = currency['percent_change_1h'], \
                                                   currency['percent_change_24h'], \
                                                   currency['percent_change_7d']
                value = float(currency[f'price_{to_currency.lower()}'])
                value = '{0:.3f}'.format(value)
                symbol = currency['symbol']
        except requests.RequestException as ex:
            self.bot.privmsg(target, f'{mask.nick}: {ex}')
        finally:
            if not value:
                return

            exchange = self.bot.format(f'1 {symbol} = {value} {to_currency.upper()}', bold=True)
            self.bot.privmsg(target,
                             f'{exchange}. Changes over 1h/24h/7d: {change_1h}/{change_24h}/{change_7d}')
