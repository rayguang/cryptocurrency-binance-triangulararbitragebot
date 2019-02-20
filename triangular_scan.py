# Import system modules
import time
from datetime import datetime
import pprint
import math
import heapq
import logger
from operator import itemgetter

import multiprocessing
import os

# Import arbitrage related modules
from binance.client import Client
from binance.enums import *
from apikeys import BinanceKey
from bina_pair import *

# Init API key/secret
api_key = BinanceKey['api_key']
api_secret = BinanceKey['api_secret']


# Create Binance API client
client = Client(api_key, api_secret)
#client.synced('order_market_buy', symbol='BNBBTC', quantity=10)

# Setup market to run tri-arbitrage
#arbitrage_pairs = [['ETHBTC', 'BTCUSDT', 'ETHUSDT']]
#arbitrage_pairs = [['BNBETH', 'PAXBNB', 'PAXETH']]
arbitrage_pairs = pairs_allcoins
len_pairs = len(arbitrage_pairs)
process_count = 3


def set_time_binance():
    gt = client.get_server_time()
    tt = time.gmtime(int((gt["serverTime"])/1000))
    #win32api.SetSystemTime(tt[0], tt[1],0,tt[2], tt[3], tt[4],tt[5],0)


def initialize_arb(list_arbitrage_pairs):
    # Get local time and exchange server time.
    bot_start_time = get_local_time()
    serverTimestamp = client.get_server_time()["serverTime"]
    exchange_time = datetime.fromtimestamp(serverTimestamp/1000).isoformat()

    #info = client.get_account()
    # Clear All Pending Trades

    # Clear All Pending Trades
    # welcome_message+=str(info)
    #trades = client.get_my_trades(symbol='BNBBTC')
    # print(trades)
    # data_log_to_file(balance)

    # Dummy way to keep us from reach limit, i.e., delay 5 seconds for each run, current rate 1200 calls/minute
    #print("Take a rest for before the next scan ...\n")
    time.sleep(5)

    try:
        status = client.get_system_status()
        print("\nExchange Status: *** {} ***\n".format(status["msg"]))

        # Collect all symbols in Exchange
        #coin_list = ['BTC', 'ETH', 'USDT', 'BNB']
        balance_list = []

        # Calc triangular arbitrage opportunity for pairs
        arb_profit = []
        ranked_profit = []

        # Get order book
        tickers = client.get_orderbook_tickers()

        for pairs in list_arbitrage_pairs:
            pnl = calc_triarbitrage_profit(pairs, list_arbitrage_pairs.index(pairs), len(list_arbitrage_pairs))

            # Save pnl for each arbitrage pair
            arb_profit.append({pairs[2]: pnl})

        # print(arb_profit)
        # ranked_profit = sorted(arb_profit, key=lambda x: tuple(
        #     x.values()), reverse=True)[:10]
        # print(ranked_profit)

    except Exception as e:
        # Save to log
        logger.log_error(e)
        print("\n!!!Failed to init arbitrage engine!!!")
        raise


def data_log_to_file(message):
    filename = datetime.now().strftime("%Y%m%d")
    with open('results_'+filename+'.txt', 'a+') as f:
        f.write(message)


def portf_file_save(portfolio, filename='Portfolio.txt'):
    with open(filename, 'a+') as f:
        f.write('\n'+str(portfolio))


def get_local_time():
    return datetime.now()


def get_execution_step():
    print("Execution Strategy (cross - market), for example, cross - ETHBTC x BTCUSDT, market - ETHUSDT:\n")
    print("We convert coin#1 -> coin#2 -> coin#3 -> coin#1. For example, ETHBTC->BTCUSDT->ETHUSDT, start with 1ETH, sell for xxx BTC @ bid ETHBTC, then sell xxx BTC ")
    if (arb_pnl > 0):
        print("Case 1: PnL greater than 0. Sell market buy cross, for example, sell USDT buy ETH in market, sell ETH buy BTC, sell BTC buy USDT\n.")
    elif (arb_pnl < 0):
        print("Case 2: PnL less than 0. Sell cross buy market, for example, sell USDT buy BTC, sell BTC buy ETH, sell ETH buy USDT\n")
    else:
        pass
        #print("No arbitrage opportunity found")


def profit_rank(*args):
    heapq.nlargest(10, *args)


def calc_triarbitrage_profit(list_of_symbols, id, num_symbols, place_order='NO', real_order='NO'):
    # msg_welcome_arbitrage = "\n++++ Triangular Arbitrage Calculation - Running ++++\n"
    # print(msg_welcome_arbitrage)
    # data_log_to_file(msg_welcome_arbitrage)
    print("Calculating arbitrage for pairs {}/{}: {} ...".format(int(id+1),num_symbols, list_of_symbols))

    # Transaction costs in percentage, e.g. 0.1% per transaction, in total 3 transactions
    fee_maker = 0.0525
    fee_taker = 0.0525



    # symbol 1 x symbol 2 arrives cross price for symbol 3
    # Bid/Ask spreads calculation:
    # Start with coin 1, coin#1 -> coin#2 @ bid; coin#2 -> coin#3 @bid, coin#3->coin#1 @ask
    i = 0
    symbol_price = []
    coin_depth = {}
    for sym in list_of_symbols:
        currency_pair = "Ticker: "+str(sym)+" "
        last_price = client.get_symbol_ticker(symbol=sym)
        symbol_price.append(last_price)

        try:
            depth = client.get_order_book(symbol=sym)
            #print("DEBUG Depth {}: bid {} bidQuant {}; ask {} askQuant {}\n".format(sym, depth['bids'][0][0], depth['bids'][0][1],depth['asks'][0][0], depth['asks'][0][1]))
            coin_depth[i]= {
                'symbol': sym,
                'bid': depth['bids'][0][0],
                'bidQuant': depth['bids'][0][1],
                'ask': depth['asks'][0][0],
                'askQuant': depth['asks'][0][1]
            }
            #print("DEBUG: coin depth coin#{} {}".format(i, coin_depth[i]))
            # i max value is 2, since we have only 3 pairs
            i +=1
        except Exception as e:
        # Save to log
            logger.log_error(e)
            print("\n!!!Failed to get the order book for {}, depth {}\n!!!".format(sym,depth))
            pass

    # cross_price = float(symbol_price[0]["price"]) * \
    #     float(symbol_price[1]["price"])
    # market_price = float(symbol_price[2]["price"])
    # print(" single pair price {} {}\n".format(symbol_price[0]["price"],symbol_price[1]["price"]))
    # print("cross pair {} cross price {}".format(sym,cross_price))
    # arb_pnl = cross_price - market_price
    # arb_pnl_percentage = arb_pnl/market_price * 100

    # Calc triangular arbitrage PnL in percentage
    # Worst scenario 1: market takers, sell@bid, sell@bid and buy@ask, counter clockwise, e.g., ETHBTC/BTCUSDT/ETHUSDT, ETH->BTC->USDT->ETH
    # ETHUSDT(cross_bid) = ETHBTC[bid]*BTCUSDT[bid], this is the price we can sell ETH at cross at cross_bid
    # ETHUSDT(market_ask): this is the price we can buy ETH on the market at market_ask.
    # Arbitrage exists if we can buy low ETHUSDT[market_ask] and sell high ETHUSDT[cross_bid], i.e., ETHUSDT[cross_bid] > ETHUSDT[market_ask]
    # Net PnL should also minus the transaction costs, which includes 3 transactions in total.
    cross_rate = float(coin_depth[0]['bid'])*float(coin_depth[1]['bid'])
    market_rate = float(coin_depth[2]['ask'])
    if (market_rate < cross_rate):
        print("!!!Found Arbitrage!!! (direction counter clockwise):")
        print("DEBUG: cross_rate {}, convert_rate {}\n".format(cross_rate, market_rate))
        PnL_cc = (cross_rate / market_rate - 1) * 100
        # Adjust for transaction cost, 3 transactions, all make makers in this scenario
        PnL_cc_after_fee = float(PnL_cc - fee_taker*3)
        # Output for PnL
        print ("Triangular Arbitrage pairs in order counter clockwise {}".format(list_of_symbols))
        print ("Gross PnL as market taker:\t{:+8.6f}%".format(PnL_cc))
        print ("Net PnL post trans fees:\t {:+8.6f}%\n\n".format(PnL_cc_after_fee))
        time_now = get_local_time()
        if PnL_cc_after_fee > 0:
            msg_cc = "{} Pairs: {}\n".format(time_now, list_of_symbols)+"Gross PnL_cc {} - Net PnL_cc {}\n".format(PnL_cc,PnL_cc_after_fee)
            data_log_to_file(msg_cc)

    # Worst scenario 2: market takers, sell@bid, buy@ask, buy @ask. Clockwise, e.g., ETHBTC/BTCUSDT/ETHUSDT, ETH->USDT->BTC->ETH
    cross_rate_cw = float(coin_depth[2]['bid'])/float(coin_depth[1]['ask'])
    market_rate_cw = float(coin_depth[0]['ask'])
    if (market_rate_cw < cross_rate_cw):
        print("!!!Found Arbitrage!!! (direction clockwise):")
        print("DEBUG: cross_rate {}, convert_rate {}\n".format(cross_rate, market_rate))
        PnL_cw = (cross_rate_cw / market_rate_cw -1)*100
        PnL_cw_after_fee = float(PnL_cw - fee_taker*3)
        # Output for PnL_cw
        print ("Triangular Arbitrage pairs in order clockwise {}".format(list_of_symbols))
        print ("Gross PnL_cw as market taker:\t{:+8.6f}%".format(PnL_cw))
        print ("Net PnL_cw post trans fees:\t {:+8.6f}%\n\n".format(PnL_cw_after_fee))
        time_now = get_local_time()
        if PnL_cw_after_fee > 0:
            msg_cw = "{} Pairs: {}\n".format(time_now, list_of_symbols)+"Gross PnL_cw {} - Net PnL_cw {}\n".format(PnL_cw,PnL_cw_after_fee)
            data_log_to_file(msg_cw)
    
    # Output cross pair and PnL
    # msg_marketprice = str("Market Price {} {}\n".format(
    #     symbol_price[2]["symbol"], market_price))
    # msg_crossprice = str("Cross Price {} x {} {}\n".format(
    #     symbol_price[0]["symbol"], symbol_price[1]["symbol"], cross_price))
    # msg_pnl = str(
    #     "Cross Arbitrage Pnl ${:+8.6f}, PnL {:+8.6f}%\n\n".format(arb_pnl, arb_pnl_percentage))
    # msg = msg_marketprice + msg_crossprice + msg_pnl
    # data_log_to_file(msg)
    # #print("Market Price {} {}".format(symbol_price[2]["symbol"], market_price))
    #print("Cross Price {} x {} {}".format(symbol_price[0]["symbol"], symbol_price[1]["symbol"], cross_price))
    #print("Cross Arbitrage Pnl ${:+8.6f}, PnL {:+8.6f}%\n\n".format(arb_pnl, arb_pnl_percentage))

     


def place_order(arb_profit_percentage):
        # Sanity check to place order ony if profitable
    if arb_profit_percentage <= 0:
        print(
            "Arbitrage PnL less than 0, not profitable trade, be patient and waiting ...\n")
        return

    # Log messages
    real_order_msg = "Entering ****REAL**** ORDER: "
    real_order_msg += "Arbitrage pairs: "
    real_order_msg += "Arbitrage PnL: "
    print(real_order_msg)
    data_log_to_file(real_order_msg)

def place_test_orders(test_symbol='BTCUSD'):
    # Create test order
    try:
        if test_symbol == "":
                test_symbol = 'BTCUSDT'
                print("Create test order with default symbol BTCUSDT.\n")
                        
        client.create_test_order(symbol=test_symbol, side=SIDE_BUY, type=ORDER_TYPE_LIMIT, quantity=1,price=0.01, timeInForce=TIME_IN_FORCE_GTC)
    except:
        logger.log_error(e)
        print("Test order failed to create.")

def run(pid, list_process_pairs):
    # set_time_binance()
    # Initialize Arbitrage Binance Bot
    while 1:
        try:
            initialize_arb(list_process_pairs)
            msg_end = "\n *** P#{} Scan completed at {} ***\n".format(pid, get_local_time())
            data_log_to_file(msg_end)
        except:
            print("Init P#{} failed. Restarting...\n\n".format(pid))

            #exit()
    # Get Binance Wallet Balance - Split into 4 coins evenly

    # Perform our Arbitrage Function

    # Data Output (log) in a text file - keep track of start/end time, trades, balance
    # pass

def spawn():
    pairs_for_process = []
    chunk_size = int(len_pairs / process_count + 1)
    pairs_for_process = [arbitrage_pairs[x:x+chunk_size] for x in range(0, len_pairs, chunk_size)]
    for i in range(process_count):
        p = multiprocessing.Process(target = run, args= (i, pairs_for_process[i]) )
        p.start()
        welcome_message = "\nBot Process P{} is starting at {}.\n".format(i, get_local_time())
        print(welcome_message+"\n")
        data_log_to_file(welcome_message)
        

if __name__ == "__main__":
    spawn()
