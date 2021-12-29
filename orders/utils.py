from django.utils.timezone import now
from .models import Order
from accounts.models import Trader
import requests


class Bot:
    def __init__(self):
        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        self.params = {
            'start': 1,
            'limit': 1,
            'convert': 'USD'
        }
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': 'acaa2fac-67e2-40cc-8612-33c27b3d7c3d'
        }

    def fetch_currency_data(self):
        r = requests.get(url=self.url, headers=self.headers, params=self.params).json()
        return r['data']


def get_current_btc_value():
    bot = Bot()
    currency = bot.fetch_currency_data()
    return currency[0]['quote']['USD']['price']


def assess_transaction(trans, trader_id):
    sales = trans['sales']
    purchase = trans['purchase']

    if sales['trader_id'] == trader_id:
        sold_order_value = sales['btc'] * sales['current_btc_value']
        seller_profit = 100 - (sold_order_value / purchase['price']) * 100
        if seller_profit >= 0:
            return f'+{int(seller_profit)}%'
        else:
            return f'{int(seller_profit)}%'

    if purchase['trader_id'] == trader_id:
        buyer_profit = 100 - (purchase['price'] / (sales['btc'] * purchase['current_btc_value'])) * 100
        if buyer_profit >= 0:
            return f'+{int(buyer_profit)}%'
        else:
            return f'{int(buyer_profit)}%'


def transaction(buyer_trader, pur_order):
    sales_order = Order.objects.exclude(trader_id=buyer_trader.pk) \
        .filter(active__in=[True], type='S', price__lte=pur_order.price).order_by('timestamp').first()

    if sales_order:
        seller_trader = Trader.objects.get(pk=sales_order.trader_id)
        seller_trader.btc_balance -= sales_order.btc
        seller_trader.dollar_balance += pur_order.price
        seller_trader.fungible_balance += pur_order.price

        buyer_trader.btc_balance += sales_order.btc
        buyer_trader.fungible_btc += sales_order.btc
        buyer_trader.dollar_balance -= pur_order.price

        transaction = {
            'trans_timestamp': now(),
            'sales':
                {
                    '_id': sales_order.pk,
                    'trader_id': sales_order.trader_id,
                    'btc': sales_order.btc,
                    'price': sales_order.price,
                    'current_btc_value': get_current_btc_value(),
                    'timestamp': sales_order.timestamp,
                },
            'purchase':
                {
                    '_id': pur_order.pk,
                    'trader_id': pur_order.trader_id,
                    'btc': pur_order.btc,
                    'price': pur_order.price,
                    'current_btc_value': get_current_btc_value(),
                    'timestamp': pur_order.timestamp,
                }
        }

        for trader in [buyer_trader, seller_trader]:
            trader.transactions.append(transaction)
            trader.n_open_orders -= 1
            trader.n_close_orders += 1
            trader.save()

        for order in [pur_order, sales_order]:
            order.active = False
            order.save()

    else:
        print('Nothing to purchase')


def is_valid_transaction(trader, order_btc, order_price, order_type):
    if order_type == 'S':
        if trader.fungible_btc >= order_btc:
            return True
        else:
            return False

    elif order_type == 'P':
        if trader.fungible_balance >= order_price:
            return True
        else:
            return False
    else:
        print("Transaction validation failed")
        return False


def is_valid_action(actual_trader, order_trader, order_type):
    order_trader = Trader.objects.get(pk=order_trader)
    if actual_trader == order_trader.pk:
        return True
    elif actual_trader in order_trader.subprofiles['sellers']:
        if order_type == 'S':
            return True
        else:
            print('This subprofiles is not a seller...')
            return False
    elif actual_trader in order_trader.subprofiles['buyers']:
        if order_type == 'P':
            return True
        else:
            print('This subprofiles is not a buyer...')
            return False
    else:
        print('Action not permitted...')


def get_subprofiles(request):
    profiles = {'sellers': [], 'buyers': []}
    for trader in Trader.objects.all():
        if request.user.pk in trader.subprofiles['sellers']:
            profiles['sellers'].append(trader.pk)
        if request.user.pk in trader.subprofiles['buyers']:
            profiles['buyers'].append(trader.pk)
    return profiles
