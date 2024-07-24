# Trading Bots Platform v1 [bybit]

Plan:
- [x] Balance
- [x] [Market] Global market
- [x] [Market] Bybit market
- [x] [Trading] Positions
- [x] [Trading] Open orders
- [x] [Trading] Closed orders
- [x] [Trading] Canceled orders
- [x] [Trading] Transactions
- [ ] [Bots] Real mode
- [ ] [Bots] Backtesting
- [ ] [Bots] Trend Bot
- [ ] [Bots] Impulse Bot
- [ ] [Bots] Simple Spot/Future Grid Bot
- [ ] [Bots] OBLV Spot/Future Grid Bot
- [ ] [Bots] Future Beam Bot
- [ ] [Bots] DCA Bot

<hr>

Run:
```commandline
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python .\main.py
```
Also:
```commandline
python .\main.py --host 0.0.0.0 --port 8080
```

<hr>

Windows Time service (W32Time):
```commandline
python .\win_update_time.py
```
(to fix errors like `please check your server timestamp or recv_window param`)
