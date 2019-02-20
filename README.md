# cryptocurrency-binance-triangulararbitragebot
This bot scans 302 pairs of coins currently traded in binance exchange in realtime with N running processes. N is customizable.

The P&L is calculated after considering the bid/ask spreads and transaction costs. 

To complete the full scan, it requires approximately 5 minutes for one process or 2 minutes for 4 processes due to the rate limit 1200 per minute by Binance.

A faster version of C++ implementation is done but not currently available to public.
