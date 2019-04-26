# cryptocurrency-binance-triangulararbitragebot
This bot scans 302 pairs of coins currently traded in binance exchange in realtime with N running processes. N is customizable.

The P&L is calculated after considering the bid/ask spreads and transaction costs. 

To complete the full scan, it requires approximately 5 minutes for one process or 2 minutes for 4 processes due to the rate limit 1200 per minute by Binance.

A faster version of C++ implementation is done but not currently available to public.

# How to run the program

1. Enter your api key and secret from binance in apikeys.py

2. Modify the pairs of assets you would like to scan for arbitrage in this file bina_pair.py. It contains the full list of the pairs of tradable assets, you may not need this many. 

NOTE: A smaller list will make the scan faster. However, Binance has a API rate limit of 1000+ per minute, if the scan speed is too fast, you will get a temporary ban. We are working on finalizing a websocket version scanner which does not have the restriction of rate limit and hopefully much faster.

3. Run the following command
python triangular_scan.py
