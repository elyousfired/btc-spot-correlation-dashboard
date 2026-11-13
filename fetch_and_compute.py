#!/usr/bin/env python3
"""
Fetch daily historical USD prices from CoinGecko starting 2026-07-01
and compute BTC-Token correlation, beta, volatility, and rolling correlation metrics.
"""

import argparse
import datetime
import json
import math
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TOKENS = [
    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "sector": "Benchmark"},
    {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "sector": "L1"},
    {"id": "solana", "symbol": "SOL", "name": "Solana", "sector": "L1"},
    {"id": "binancecoin", "symbol": "BNB", "name": "BNB", "sector": "L1 / Exchange"},
    {"id": "ripple", "symbol": "XRP", "name": "XRP", "sector": "Payments / L1"},
    {"id": "hyperliquid", "symbol": "HYPE", "name": "Hyperliquid", "sector": "Perp DEX / L1"},
    {"id": "dogecoin", "symbol": "DOGE", "name": "Dogecoin", "sector": "Meme"},
    {"id": "chainlink", "symbol": "LINK", "name": "Chainlink", "sector": "Oracle / Infra"},
    {"id": "cardano", "symbol": "ADA", "name": "Cardano", "sector": "L1"},
    {"id": "near", "symbol": "NEAR", "name": "NEAR Protocol", "sector": "L1 / AI"},
    {"id": "avalanche-2", "symbol": "AVAX", "name": "Avalanche", "sector": "L1"},
    {"id": "sui", "symbol": "SUI", "name": "Sui", "sector": "L1"},
    {"id": "uniswap", "symbol": "UNI", "name": "Uniswap", "sector": "DeFi"},
    {"id": "zcash", "symbol": "ZEC", "name": "Zcash", "sector": "Privacy"},
    {"id": "monero", "symbol": "XMR", "name": "Monero", "sector": "Privacy"},
    {"id": "the-open-network", "symbol": "TON", "name": "Toncoin", "sector": "L1"},
]


def coingecko_get_json(url: str, max_retries: int = 5) -> dict:
    """Fetch JSON from CoinGecko public v3 API with polite 429 retry/backoff."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CryptoQuantResearch/1.0",
        "Accept": "application/json",
    }
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", "20"))
                wait_s = max(retry_after, 15 * (attempt + 1))
                print(f"  [429 Rate Limit] Sleeping {wait_s}s before retry ({attempt + 1}/{max_retries})...")
                time.sleep(wait_s)
                continue
            raise
        except Exception as exc:
            wait_s = 5 * (attempt + 1)
            print(f"  [Error: {exc}] Retrying in {wait_s}s...")
            time.sleep(wait_s)
    raise RuntimeError(f"Failed to fetch {url} after {max_retries} retries")


def fetch_token_daily_series(coin_id: str, start_ts: int, end_ts: int) -> dict[str, float]:
    """Return {YYYY-MM-DD: price_usd} map from CoinGecko market_chart/range."""
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
        f"?vs_currency=usd&from={start_ts}&to={end_ts}"
    )
    data = coingecko_get_json(url)
    prices = data.get("prices", [])
    daily: dict[str, float] = {}
    for ts_ms, price in prices:
        if price is None or price <= 0:
            continue
        dt = datetime.datetime.fromtimestamp(ts_ms / 1000.0, datetime.timezone.utc)
        day_str = dt.strftime("%Y-%m-%d")
        # Keep the latest price entry for each UTC date
        daily[day_str] = float(price)
    return dict(sorted(daily.items()))


def pearson_corr(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 3 or n != len(y):
        return None
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = sum((xi - mx) ** 2 for xi in x)
    dy = sum((yi - my) ** 2 for yi in y)
    denom = math.sqrt(dx * dy)
    if denom == 0:
        return None
    return num / denom


def average_ranks(vals: list[float]) -> list[float]:
    indexed = sorted(enumerate(vals), key=lambda t: t[1])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_corr(x: list[float], y: list[float]) -> float | None:
    if len(x) < 3 or len(x) != len(y):
        return None
    return pearson_corr(average_ranks(x), average_ranks(y))


def beta_vs_benchmark(token_rets: list[float], bench_rets: list[float]) -> float | None:
    n = len(token_rets)
    if n < 3 or n != len(bench_rets):
        return None
    mt = sum(token_rets) / n
    mb = sum(bench_rets) / n
    cov = sum((t - mt) * (b - mb) for t, b in zip(token_rets, bench_rets))
    var_b = sum((b - mb) ** 2 for b in bench_rets)
    if var_b == 0:
        return None
    return cov / var_b


def max_drawdown(prices: list[float]) -> float:
    peak = prices[0]
    mdd = 0.0
    for p in prices:
        if p > peak:
            peak = p
        dd = (p - peak) / peak
        if dd < mdd:
            mdd = dd
    return mdd


def compute_metrics(raw_series: dict[str, dict[str, float]], tokens_meta: list[dict], start_date: str) -> dict:
    btc_map = raw_series["bitcoin"]
    btc_dates = [d for d in sorted(btc_map.keys()) if d >= start_date]

    results = []
    aligned_prices = {"dates": btc_dates, "series": {}}
    aligned_prices["series"]["bitcoin"] = [btc_map[d] for d in btc_dates]

    for meta in tokens_meta:
        cid = meta["id"]
        if cid not in raw_series:
            continue
        tmap = raw_series[cid]
        common_dates = [d for d in btc_dates if d in tmap]
        if len(common_dates) < 10:
            continue

        btc_p = [btc_map[d] for d in common_dates]
        tok_p = [tmap[d] for d in common_dates]
        aligned_prices["series"][cid] = [tmap.get(d) for d in btc_dates]

        btc_log_r = [math.log(btc_p[i] / btc_p[i - 1]) for i in range(1, len(btc_p))]
        tok_log_r = [math.log(tok_p[i] / tok_p[i - 1]) for i in range(1, len(tok_p))]
        ret_dates = common_dates[1:]

        btc_simp_r = [(btc_p[i] - btc_p[i - 1]) / btc_p[i - 1] for i in range(1, len(btc_p))]
        tok_simp_r = [(tok_p[i] - tok_p[i - 1]) / tok_p[i - 1] for i in range(1, len(tok_p))]

        p_log = pearson_corr(btc_log_r, tok_log_r)
        p_simp = pearson_corr(btc_simp_r, tok_simp_r)
        s_log = spearman_corr(btc_log_r, tok_log_r)
        p_level = pearson_corr(btc_p, tok_p)
        beta = beta_vs_benchmark(tok_log_r, btc_log_r)

        # Rolling 14d and 30d Pearson correlation (log returns)
        roll_14 = []
        roll_30 = []
        for idx in range(len(ret_dates)):
            if idx + 1 >= 14:
                c14 = pearson_corr(btc_log_r[idx + 1 - 14 : idx + 1], tok_log_r[idx + 1 - 14 : idx + 1])
            else:
                c14 = None
            if idx + 1 >= 30:
                c30 = pearson_corr(btc_log_r[idx + 1 - 30 : idx + 1], tok_log_r[idx + 1 - 30 : idx + 1])
            else:
                c30 = None
            roll_14.append(round(c14, 4) if c14 is not None else None)
            roll_30.append(round(c30, 4) if c30 is not None else None)

        mean_r = sum(tok_log_r) / len(tok_log_r)
        var_r = sum((r - mean_r) ** 2 for r in tok_log_r) / (len(tok_log_r) - 1)
        ann_vol = math.sqrt(var_r * 365.0)
        period_ret = (tok_p[-1] - tok_p[0]) / tok_p[0]
        mdd = max_drawdown(tok_p)

        results.append(
            {
                "id": cid,
                "symbol": meta["symbol"],
                "name": meta["name"],
                "sector": meta["sector"],
                "start_date": common_dates[0],
                "end_date": common_dates[-1],
                "n_days": len(common_dates),
                "n_returns": len(tok_log_r),
                "start_price": tok_p[0],
                "end_price": tok_p[-1],
                "period_return_pct": round(period_ret * 100.0, 2),
                "ann_volatility_pct": round(ann_vol * 100.0, 2),
                "max_drawdown_pct": round(mdd * 100.0, 2),
                "pearson_log_corr": round(p_log, 4) if p_log is not None else None,
                "pearson_simple_corr": round(p_simp, 4) if p_simp is not None else None,
                "spearman_log_corr": round(s_log, 4) if s_log is not None else None,
                "price_level_corr": round(p_level, 4) if p_level is not None else None,
                "beta_vs_btc": round(beta, 4) if beta is not None else None,
                "r_squared": round(p_log ** 2, 4) if p_log is not None else None,
                "latest_roll_14d": next((v for v in reversed(roll_14) if v is not None), None),
                "latest_roll_30d": next((v for v in reversed(roll_30) if v is not None), None),
                "rolling_dates": ret_dates,
                "rolling_14d": roll_14,
                "rolling_30d": roll_30,
                "daily_log_returns": [round(r, 6) for r in tok_log_r],
            }
        )

    # Sort non-BTC tokens by pearson_log_corr descending, keeping BTC first
    btc_row = [r for r in results if r["id"] == "bitcoin"]
    others = sorted(
        [r for r in results if r["id"] != "bitcoin"],
        key=lambda r: r["pearson_log_corr"] if r["pearson_log_corr"] is not None else -999,
        reverse=True,
    )

    return {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "CoinGecko Public API v3 (/coins/{id}/market_chart/range)",
        "start_date": start_date,
        "end_date": btc_dates[-1] if btc_dates else None,
        "total_days": len(btc_dates),
        "tokens": btc_row + others,
        "aligned_prices": aligned_prices,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-07-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--refresh", action="store_true", help="Force re-fetch from CoinGecko")
    parser.add_argument(
        "--extra",
        default="",
        help="Optional comma-separated extra CoinGecko IDs (e.g. pepe,bittensor,ondo-finance)",
    )
    args = parser.parse_args()

    tokens_list = list(DEFAULT_TOKENS)
    known_ids = {t["id"] for t in tokens_list}
    if args.extra:
        for raw_id in args.extra.split(","):
            cid = raw_id.strip().lower()
            if cid and cid not in known_ids:
                tokens_list.append(
                    {"id": cid, "symbol": cid.upper()[:8], "name": cid.replace("-", " ").title(), "sector": "Custom"}
                )
                known_ids.add(cid)

    start_dt = datetime.datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    start_ts = int(start_dt.timestamp())
    end_ts = int(time.time()) + 3600

    cache_path = DATA_DIR / "coingecko_prices.json"
    raw_series: dict[str, dict[str, float]] = {}
    if cache_path.exists() and not args.refresh:
        raw_series = json.loads(cache_path.read_text(encoding="utf-8"))

    for idx, meta in enumerate(tokens_list):
        cid = meta["id"]
        if cid in raw_series and len(raw_series[cid]) > 100 and not args.refresh:
            print(f"[Cache] {meta['symbol']} ({cid}): {len(raw_series[cid])} days")
            continue
        print(f"[Fetch {idx+1}/{len(tokens_list)}] {meta['symbol']} ({cid}) from {args.start}...")
        series = fetch_token_daily_series(cid, start_ts, end_ts)
        raw_series[cid] = series
        print(f"  -> {len(series)} days ({min(series.keys())} .. {max(series.keys())})")
        # Save progressively
        cache_path.write_text(json.dumps(raw_series, indent=2), encoding="utf-8")
        if idx < len(tokens_list) - 1:
            time.sleep(3.5)

    report = compute_metrics(raw_series, tokens_list, args.start)
    out_path = DATA_DIR / "correlation_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved correlation report to {out_path}")
    print(f"Period: {report['start_date']} -> {report['end_date']} ({report['total_days']} days)\n")
    for row in report["tokens"]:
        print(
            f"{row['symbol']:6s} | r(log)={row['pearson_log_corr']:+.4f} | "
            f"spearman={row['spearman_log_corr']:+.4f} | beta={row['beta_vs_btc']:+.3f} | "
            f"roll30d={row['latest_roll_30d']} | ret={row['period_return_pct']:+.2f}%"
        )


if __name__ == "__main__":
    main()
