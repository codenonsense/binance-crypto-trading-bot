from binance.um_futures import UMFutures
import ta
import pandas as pd
import time
from time import sleep
from binance.error import ClientError

api = "clQDBSZ1QPqgTKxWWy0x8Vvxz2EqLaVb64Q3EaUrNizlyNakLoMifCOVqJl6Dhsc"
secret = "PdZTHmC2qtMNv2wA3QkK6kNuw6wkRJeE50eMvakXyn4Y1yfP9trIOdw4S04g9H7Q"

client = UMFutures(key=api, secret=secret)

tp = 0.01
sl = 0.01
volume = 50
leverage = 10
type = 'ISOLATED'

def get_balance_usdt():
    try:
        response = client.balance(recvWindow=10000)
        for elem in response:
            print(elem)
            if elem['asset'] == 'USDT':
                return float(elem['balance'])
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def get_tickers_usdt():
    tickers = []
    resp = client.ticker_price()
    for ticker in resp:
        if 'USDT' in ticker['symbol']:
            tickers.append(ticker['symbol'])
    return tickers

def klines(symbol):
    try:
        resp = pd.DataFrame(client.klines(symbol, '1h'))
        resp = resp.iloc[:,:6]
        resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        resp = resp.set_index('Time')
        resp.index = pd.to_datetime(resp.index, unit='ms')
        resp = resp.astype(float)
        return resp
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        
def set_leverage(symbol, level):
    try:
        response = client.leverage_brackets(symbol=symbol, leverage=level, recvWindow=6000)
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
def set_mode(symbol, type):
    try:
        response = client.change_margin_type(
            symbol=symbol, marginType=type, recvWindow=6000
        )
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
def get_price_precision(symbol):
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['pricePrecision']
def get_quantity_precision(symbol):
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['quantityPrecision']
def open_order(symbol, side):
    price = float(client.ticker_price(symbol=symbol)['price'])
    qty_precision = get_quantity_precision(symbol)
    price_precision = get_price_precision(symbol)
    qty = round(volume/price, qty_precision)
    if side == 'buy':
        try:
            resp1 = client.new_order(symbol=symbol, side='BUY', type='LIMIT', quantity=qty, timeInForce='GTC', price=price)
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price - price*sl, price_precision)
            resp2 = client.new_order(symbol=symbol, side='SELL', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price)
            print(resp2)
            sleep(2)
            tp_price = round(price + price*tp, price_precision)
            resp3 = client.new_order(symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC', stopPrice=tp_price)
            print(resp3)
        except ClientError as error:
            print(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                )
            )
    if side == 'sell':
        try:
            resp1 = client.new_order(symbol=symbol, side='SELL', type='LIMIT', quantity=qty, timeInForce='GTC', price=price)
            print(symbol, side, "placing order")
            print(resp1)
            sleep(2)
            sl_price = round(price + price*sl, price_precision)
            resp2 = client.new_order(symbol=symbol, side='BUY', type='STOP_MARKET', quantity=qty, timeInForce='GTC', stopPrice=sl_price)
            print(resp2)
            sleep(2)
            tp_price = round(price - price*tp, price_precision)
            resp3 = client.new_order(symbol=symbol, side='BUY', type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce='GTC', stopPrice=tp_price)
            print(resp3)
        except ClientError as error:
            print(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                )
            )
def check_positions():
    try:
        resp = client.get_position_risk()
        positions = 0
        for elem in resp:
            if float(elem['positionAmt']) != 0:
                positions += 1
        return positions
    except ClientError as error:
            print(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                )
            )
def close_open_orders(symbol):
    try:
        response = client.cancel_open_orders(symbol=symbol, recvWindow=2000)
        print(response)
    except ClientError as error:
        print(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
def check_macd_ema(symbol):
    kl = klines(symbol)
    if ta.trend.macd_diff(kl.close).iloc[-1] > 0 and ta.trend.macd_diff(kl.close).iloc[-2] < 0 and ta.trend.ema_indicator(kl.close, window=200).iloc[-1] < kl.close.iloc[-1]:
        return 'up'
    elif ta.trend.macd_diff(kl.close).iloc[-1] < 0 and ta.trend.macd_diff(kl.close).iloc[-2] > 0 and ta.trend.ema_indicator(kl.close, window=200).iloc[-1] > kl.close.iloc[-1]:
        return 'down'
    else: 
        return None
    
order = False
symbol = ''
symbols = get_tickers_usdt()

while True:
    get_balance_usdt()
    # positions = check_positions()
    # print(f'You Have {positions} opened positions')   
    # if positions == 0:
    #     order = False
    #     if symbol != '':
    #         close_open_orders(symbol=symbol)
            
    # if order == False:
    #     for elem in symbols:
    #         signal = check_macd_ema(elem)
    #         if signal == 'up':
    #             print('Found Buy Signal for', elem)
    #             set_mode(elem, type=type)
    #             sleep(1)
    #             set_leverage(elem, leverage)
    #             sleep(1)
    #             print('Placing order for ', elem)
    #             open_order(elem, 'buy')
    #             symbol = elem
    #             order = True
    #             break
    #         if signal == 'down':
    #             print('Found Sell Signal for', elem)
    #             set_mode(elem, type=type)
    #             sleep(1)
    #             set_leverage(elem, leverage)
    #             sleep(1)
    #             print('Placing order for ', elem)
    #             open_order(elem, 'sell')
    #             symbol = elem
    #             order = True
    #             break
    print('Waiting for 60sec')
    sleep(60)