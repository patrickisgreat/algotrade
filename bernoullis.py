from binance import ThreadedWebsocketManager
import os, pprint
import sys
import datetime
#
#  start_depth_socket(self, callback: Callable, symbol: str, depth: Union[str, NoneType] = None, interval: Union[int, NoneType] = None) -> str
#
#  start_index_price_socket(self, callback: Callable, symbol: str, fast: bool = True) -> str
#
#  start_kline_socket(self, callback: Callable, symbol: str, interval='1m') -> str
#
#  start_miniticker_socket(self, callback: Callable, update_time: int = 1000) -> str
#
#  start_multiplex_socket(self, callback: Callable, streams: List[str]) -> str
#
#  start_symbol_book_ticker_socket(self, callback: Callable, symbol: str) -> str
#
#  start_symbol_mark_price_socket(self, callback: Callable, symbol: str, fast: bool = True, futures_type: binance.enums.FuturesType = <FuturesType.USD_M: 1>) -> str
#
#  start_symbol_ticker_socket(self, callback: Callable, symbol: str) -> str
#
#  start_ticker_socket(self, callback: Callable) -> str
#
#  start_trade_socket(self, callback: Callable, symbol: str) -> str
#
#  start_user_socket(self, callback: Callable) -> str
#
# Kline information
#  "e": "kline",     // Event type
#  "E": 123456789,   // Event time
#  "s": "BNBBTC",    // Symbol
#  "k": {
#    "t": 123400000, // Kline start time
#    "T": 123460000, // Kline close time
#    "s": "BNBBTC",  // Symbol
#    "i": "1m",      // Interval
#    "f": 100,       // First trade ID
#    "L": 200,       // Last trade ID
#    "o": "0.0010",  // Open price
#    "c": "0.0020",  // Close price
#    "h": "0.0025",  // High price
#    "l": "0.0015",  // Low price
#    "v": "1000",    // Base asset volume
#    "n": 100,       // Number of trades
#    "x": false,     // Is this kline closed?
#    "q": "1.0000",  // Quote asset volume
#    "V": "500",     // Taker buy base asset volume
#    "Q": "0.500",   // Taker buy quote asset volume
#    "B": "123456"   // Ignore
# TODO
# Get historical klines
# Use pandas to create a dataframe of historical klines
# Write a function that takes a set of conditions and asks
# probability questisons that can range from simple to complex.
# For example, a basic p-vale we should keep track of is the
# odds of green candle/red candle. This can be used later with baye's
# This function should also be able to ask questions like:
# "Givin 5 red candles whoose sum totals 5% what is the probability
# that there will be a 3% increase in the next hour?
# Then it will be possible to hypothesize different conditions that
# could trigger favorable conditions. So, then we can ask a series of
# questions using current historical data. Filter out those whose p-value
# is greater than .7 and start betting on them.
# For now the idea is to think of candles as coin tosses.
# The more consecutive of one color we see the more likely it becomes to see
# opposite color.
api_key = os.environ.get('binance_key')
api_secret = os.environ.get('binance_secret')

symbol = sys.argv[1]
interval = sys.argv[2]
closes = []
green_candles = []
red_candles = []
prev_color = ''
consecutive_g = 1
consecutive_r = 1
in_position = False
max_trades = 3
num_trades = 0
num_candles = 0
avg_price = 0
target_buy = 0
target_sell = False
trending_up = False
position_price = 0

# Start listening to a socket
twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
# start is required to initialize its internal loop
twm.start()

def handle_socket_message(msg):
    global closes
    global green_candles
    global red_candles
    global consecutive_g
    global consecutive_r
    global in_position
    global target_buy
    global num_trades
    global max_trades
    global target_sell
    global num_candles
    global avg_price
    global prev_color
    global trending_up
    global position_price

    candle = msg['k']
    current_price = float(candle['c'])
    print("{} Currently {}".format(symbol, current_price))
    if candle['x']:
        num_candles += 1

        # Get candle variables
        open_price = float(candle['o'])
        close_price = float(candle['c'])
#        open_time = datetime.datetime.fromtimestamp(candle['t'])
#        close_time = datetime.datetime.fromtimestamp(candle['T'])
        closes.append(close_price)
        poc = 100 - (close_price / open_price * 100)

        # Print the candle
        print(symbol)
        print(interval)
        print("Open Price: {}".format(open_price))
        print("Close Price: {}".format(close_price))
#        print("Open Time: {}".format(open_time))
#        print("Close Time: {}".format(close_time))
        print("Number of Trades: {}".format(msg['k']['n']))
        print("Total candles: {}".format(num_candles))

        if(close_price > open_price):
            print("Green candle: {}".format(poc * -1))
            green_candles.append(poc * -1)
            print("Green candles: {}".format(len(green_candles)))

            if(prev_color == 'green'):
                consecutive_g += 1
                consecutive_r = 1
                print("Consecutive Green: {}".format(consecutive_g))
            prev_color = 'green'
        else:
            print("Red candle: {}".format(poc * -1))
            red_candles.append(poc * -1)
            pprint.pprint(red_candles)
            print("Red Candles: {}".format(len(red_candles)))

            if(prev_color == 'red'):
                consecutive_r += 1
                consecutive_g = 1
                print("Consecutive Red: {}".format(consecutive_r))
            prev_color = 'red'
        print()

        if consecutive_r == 3 and not in_position and num_trades < max_trades:
            with open("algolog.txt", "a") as fh:
                fh.write("3 red consecutive candles\n")
                fh.write("BUY {} AT {}\n".format(symbol, current_price))
                rate = 0
                for i in red_candles[-3:]:
                    rate += (i * -1)
                rate /= 10
                rate = 1 + rate
                target_sell = closes[-4:][0]
                fh.write("Setting Target Sell Price: {} With a Rate of {}\n".format(target_sell, rate))
                in_position = True
                num_trades += 1
                fh.close()

        if current_price >= target_sell and target_sell:
            with open("algolog.txt","a") as fh:
                fh.write("SELL {} AT {}\n".format(symbol,current_price))
                fh.close()
            in_position = False



twm.start_kline_socket(callback=handle_socket_message, symbol=symbol, interval=interval)

