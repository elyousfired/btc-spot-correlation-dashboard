# BTC Spot Correlation & Predictive Watchlist (Binance Spot + Bybit Spot)

Interactive quantitative dashboard suite analyzing **all 666 active USDT Spot pairs** across **Binance Spot** and **Bybit Spot**, enriched with CoinGecko Top-1000 Market Cap metadata, starting **2026-07-01**.

## Pages Included
1. **`all_cex_dashboard.html`** (`/`) — Full-market Spot correlation screener (`Pearson`, `Spearman`, `Beta`, `R²`, `30D Rolling`, `Ann. Volatility`, `Max Drawdown`), market-wide correlation histogram, and per-token deep-dive charts.
2. **`btc_event_study.html`** — Historical event-study backtest answering: *When BTC pumps >= +2%, which Spot tokens surge >= +10%, and what is each token's win rate (`Wins / Events`)?*
3. **`btc_predictive_watchlist.html`** — 5-factor predictive follow-probability watchlist ranking pure Spot altcoins most likely to follow the next BTC rally.

## Refresh Data & Rebuild
```bash
python fetch_binance_bybit_all.py --start 2026-07-01 --refresh
python build_all_cex_dashboard.py
python build_event_study.py
python build_predictive_watchlist.py
```
