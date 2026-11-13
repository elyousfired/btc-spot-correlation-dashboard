#!/usr/bin/env python3
"""
Fetch ALL active USDT trading tokens across Binance (Spot + Futures) and Bybit (Spot + Linear Perps),
enrich with CoinGecko market cap/rank metadata, and compute BTC-Token correlations from 2026-07-01.
"""

import argparse
import concurrent.futures
import datetime
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STABLECOINS = {
    "USDT", "USDC", "FDUSD", "TUSD", "USDE", "DAI", "USDP", "BUSD", "USD1",
    "USDD", "PYUSD", "RLUSD", "USDG", "USDS", "BFUSD", "GUSD", "FRAX", "LUSD",
    "EUR", "EURI", "AEUR", "EURC", "EURS", "XUSD", "USDJ", "USDY", "SUSD",
    "CUSD", "AUSD", "BUIDL", "USUAL", "USD0", "U", "USDR",
    "KGST", "AEDZ", "USAT", "RWUSD", "USDTB",
}

GOLD_TOKENS = {"PAXG", "XAUT", "KAU"}

LEVERAGED_SUFFIXES = ("UP", "DOWN", "BULL", "BEAR", "3L", "3S", "2L", "2S", "5L", "5S")


def http_get_json(url: str, retries: int = 4, timeout: float = 15.0) -> dict | list:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) QuantScanner/1.0"}
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 418, 502, 503):
                wait = min(30, 3 * (attempt + 1))
                time.sleep(wait)
                continue
            raise
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed GET {url}")


def normalize_perp_base(base: str, known_spot_bases: set[str]) -> str:
    """Map 1000PEPE / 1000000MOG style perp tickers to underlying if Spot exists."""
    for prefix in ("1000000", "10000", "1000", "1M"):
        if base.startswith(prefix):
            stripped = base[len(prefix):]
            if stripped in known_spot_bases:
                return stripped
    return base


def discover_universe(spot_only: bool = True) -> dict[str, dict]:
    """Discover active USDT tokens across Binance Spot & Bybit Spot (and optionally Perps)."""
    print(f"[1/4] Discovering instruments from Binance & Bybit ({'SPOT ONLY' if spot_only else 'SPOT + PERP'})...")
    universe: dict[str, dict] = {}

    def ensure_entry(base: str) -> dict:
        if base not in universe:
            universe[base] = {
                "symbol": base,
                "binance_spot": None,
                "binance_perp": None,
                "bybit_spot": None,
                "bybit_perp": None,
            }
        return universe[base]

    # 1. Binance Spot
    b_spot = http_get_json("https://api.binance.com/api/v3/exchangeInfo", timeout=25)
    for s in b_spot.get("symbols", []):
        if s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING" and s.get("isSpotTradingAllowed", True):
            base = s["baseAsset"].upper()
            if any(base.endswith(suf) and len(base) > len(suf) + 1 for suf in LEVERAGED_SUFFIXES):
                continue
            ensure_entry(base)["binance_spot"] = s["symbol"]

    # 2. Bybit Spot
    by_spot = http_get_json("https://api.bybit.com/v5/market/instruments-info?category=spot&limit=1000", timeout=25)
    for s in by_spot.get("result", {}).get("list", []):
        if s.get("quoteCoin") == "USDT" and s.get("status") == "Trading":
            base = s["baseCoin"].upper()
            if any(base.endswith(suf) and len(base) > len(suf) + 1 for suf in LEVERAGED_SUFFIXES):
                continue
            ensure_entry(base)["bybit_spot"] = s["symbol"]

    if not spot_only:
        spot_bases = set(universe.keys())

        # 3. Binance Futures USDT Perpetual
        b_fut = http_get_json("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=25)
        for s in b_fut.get("symbols", []):
            if (
                s.get("quoteAsset") == "USDT"
                and s.get("status") == "TRADING"
                and s.get("contractType") == "PERPETUAL"
            ):
                raw_base = s["baseAsset"].upper()
                base = normalize_perp_base(raw_base, spot_bases)
                ensure_entry(base)["binance_perp"] = s["symbol"]

        # 4. Bybit Linear USDT Perpetual
        cursor = ""
        while True:
            url = "https://api.bybit.com/v5/market/instruments-info?category=linear&limit=1000"
            if cursor:
                url += f"&cursor={cursor}"
            by_lin = http_get_json(url, timeout=25)
            res = by_lin.get("result", {})
            for s in res.get("list", []):
                if (
                    s.get("quoteCoin") == "USDT"
                    and s.get("status") == "Trading"
                    and s.get("contractType") == "LinearPerpetual"
                ):
                    raw_base = s["baseCoin"].upper()
                    base = normalize_perp_base(raw_base, spot_bases)
                    ensure_entry(base)["bybit_perp"] = s["symbol"]
            cursor = res.get("nextPageCursor") or ""
            if not cursor:
                break

    print(
        f"  -> Discovered {len(universe)} unique tokens | "
        f"Binance Spot={sum(1 for v in universe.values() if v['binance_spot'])}, "
        f"Bybit Spot={sum(1 for v in universe.values() if v['bybit_spot'])}, "
        f"Binance Perp={sum(1 for v in universe.values() if v['binance_perp'])}, "
        f"Bybit Perp={sum(1 for v in universe.values() if v['bybit_perp'])}"
    )
    return universe


def fetch_coingecko_metadata(pages: int = 4) -> dict[str, dict]:
    """Fetch top 1000 coins from CoinGecko /coins/markets for market cap & rank enrichment."""
    print(f"[2/4] Fetching CoinGecko metadata (top {pages * 250} coins by market cap)...")
    meta_by_symbol: dict[str, dict] = {}
    for page in range(1, pages + 1):
        url = (
            f"https://api.coingecko.com/api/v3/coins/markets"
            f"?vs_currency=usd&order=market_cap_desc&per_page=250&page={page}&sparkline=false"
        )
        try:
            coins = http_get_json(url, retries=4, timeout=20)
            for c in coins:
                sym = (c.get("symbol") or "").upper()
                if not sym:
                    continue
                # Keep highest market cap coin if multiple coins share a ticker
                if sym not in meta_by_symbol or (c.get("market_cap") or 0) > (meta_by_symbol[sym].get("market_cap") or 0):
                    meta_by_symbol[sym] = {
                        "cg_id": c.get("id"),
                        "name": c.get("name"),
                        "rank": c.get("market_cap_rank"),
                        "market_cap": c.get("market_cap"),
                        "vol_24h": c.get("total_volume"),
                    }
            print(f"  -> Page {page}/{pages}: {len(coins)} coins")
            if page < pages:
                time.sleep(3.5)
        except Exception as exc:
            print(f"  [Warn] CoinGecko page {page} failed: {exc}")
    return meta_by_symbol


def fetch_klines_for_token(entry: dict, start_ms: int, end_ms: int) -> tuple[str, str, dict[str, float]]:
    """Fetch daily closes from primary available source: Binance Spot > Bybit Spot > Binance Perp > Bybit Perp."""
    sym = entry["symbol"]

    def parse_binance(rows: list) -> dict[str, float]:
        out: dict[str, float] = {}
        for k in rows:
            ts = int(k[0])
            close = float(k[4])
            if close > 0:
                day = datetime.datetime.fromtimestamp(ts / 1000.0, datetime.timezone.utc).strftime("%Y-%m-%d")
                out[day] = close
        return out

    def parse_bybit(rows: list) -> dict[str, float]:
        out: dict[str, float] = {}
        for k in rows:
            ts = int(k[0])
            close = float(k[4])
            if close > 0:
                day = datetime.datetime.fromtimestamp(ts / 1000.0, datetime.timezone.utc).strftime("%Y-%m-%d")
                out[day] = close
        return out

    attempts = []
    if entry["binance_spot"]:
        attempts.append(
            ("Binance Spot", f"https://api.binance.com/api/v3/klines?symbol={entry['binance_spot']}&interval=1d&startTime={start_ms}&endTime={end_ms}&limit=1000", parse_binance)
        )
    if entry["bybit_spot"]:
        attempts.append(
            ("Bybit Spot", f"https://api.bybit.com/v5/market/kline?category=spot&symbol={entry['bybit_spot']}&interval=D&start={start_ms}&end={end_ms}&limit=1000", parse_bybit)
        )
    if entry["binance_perp"]:
        attempts.append(
            ("Binance Perp", f"https://fapi.binance.com/fapi/v1/klines?symbol={entry['binance_perp']}&interval=1d&startTime={start_ms}&endTime={end_ms}&limit=1000", parse_binance)
        )
    if entry["bybit_perp"]:
        attempts.append(
            ("Bybit Perp", f"https://api.bybit.com/v5/market/kline?category=linear&symbol={entry['bybit_perp']}&interval=D&start={start_ms}&end={end_ms}&limit=1000", parse_bybit)
        )

    for src_name, url, parser in attempts:
        try:
            data = http_get_json(url, retries=3, timeout=12)
            rows = data.get("result", {}).get("list", []) if isinstance(data, dict) else data
            series = parser(rows)
            if len(series) >= 5:
                return sym, src_name, dict(sorted(series.items()))
        except Exception:
            continue
    return sym, "NONE", {}


def pearson_corr(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 5 or n != len(y):
        return None
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = sum((xi - mx) ** 2 for xi in x)
    dy = sum((yi - my) ** 2 for yi in y)
    denom = math.sqrt(dx * dy)
    return None if denom == 0 else num / denom


def average_ranks(vals: list[float]) -> list[float]:
    indexed = sorted(enumerate(vals), key=lambda t: t[1])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_r
        i = j + 1
    return ranks


def spearman_corr(x: list[float], y: list[float]) -> float | None:
    if len(x) < 5 or len(x) != len(y):
        return None
    return pearson_corr(average_ranks(x), average_ranks(y))


def beta_vs_benchmark(tok_r: list[float], bench_r: list[float]) -> float | None:
    n = len(tok_r)
    if n < 5 or n != len(bench_r):
        return None
    mt = sum(tok_r) / n
    mb = sum(bench_r) / n
    cov = sum((t - mt) * (b - mb) for t, b in zip(tok_r, bench_r))
    var_b = sum((b - mb) ** 2 for b in bench_r)
    return None if var_b == 0 else cov / var_b


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


def round_sig(val: float, sig: int = 6) -> float:
    if val == 0:
        return 0.0
    return float(f"{val:.{sig}g}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-07-01")
    parser.add_argument("--workers", type=int, default=14)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--include-perps", action="store_true", help="Include perpetual futures in addition to Spot")
    args = parser.parse_args()

    start_dt = datetime.datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(time.time() * 1000) + 86400000

    universe = discover_universe(spot_only=not args.include_perps)
    cg_cache_path = DATA_DIR / "coingecko_meta.json"
    if cg_cache_path.exists() and not args.refresh:
        cg_meta = json.loads(cg_cache_path.read_text(encoding="utf-8"))
        print(f"[2/4] Loaded {len(cg_meta)} CoinGecko metadata entries from cache")
    else:
        cg_meta = fetch_coingecko_metadata(pages=4)
        cg_cache_path.write_text(json.dumps(cg_meta), encoding="utf-8")

    cache_path = DATA_DIR / "all_cex_klines.json"
    klines_cache: dict[str, dict] = {}
    if cache_path.exists() and not args.refresh:
        klines_cache = json.loads(cache_path.read_text(encoding="utf-8"))

    to_fetch = [entry for sym, entry in universe.items() if sym not in klines_cache]
    print(f"[3/4] Fetching daily klines ({len(to_fetch)} to fetch, {len(klines_cache)} cached)...")

    if to_fetch:
        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = [pool.submit(fetch_klines_for_token, e, start_ms, end_ms) for e in to_fetch]
            for fut in concurrent.futures.as_completed(futs):
                sym, src, series = fut.result()
                if series:
                    klines_cache[sym] = {"source": src, "prices": series}
                done += 1
                if done % 100 == 0 or done == len(to_fetch):
                    print(f"  -> Progress: {done}/{len(to_fetch)} fetched")
        cache_path.write_text(json.dumps(klines_cache), encoding="utf-8")

    # Align against BTC daily dates
    print("[4/4] Computing correlations, Beta, R2, and rolling windows...")
    btc_prices_map = klines_cache["BTC"]["prices"]
    all_dates = sorted(d for d in btc_prices_map.keys() if d >= args.start)
    date_to_idx = {d: i for i, d in enumerate(all_dates)}

    rows = []
    compact_series: dict[str, list[float | None]] = {}

    for sym, entry in sorted(universe.items()):
        if sym not in klines_cache:
            continue
        tmap = klines_cache[sym]["prices"]
        common_dates = [d for d in all_dates if d in tmap]
        if len(common_dates) < 15:
            continue

        btc_p = [btc_prices_map[d] for d in common_dates]
        tok_p = [tmap[d] for d in common_dates]
        btc_log = [math.log(btc_p[i] / btc_p[i - 1]) for i in range(1, len(btc_p))]
        tok_log = [math.log(tok_p[i] / tok_p[i - 1]) for i in range(1, len(tok_p))]
        btc_simp = [(btc_p[i] - btc_p[i - 1]) / btc_p[i - 1] for i in range(1, len(btc_p))]
        tok_simp = [(tok_p[i] - tok_p[i - 1]) / tok_p[i - 1] for i in range(1, len(tok_p))]

        p_log = pearson_corr(btc_log, tok_log)
        p_simp = pearson_corr(btc_simp, tok_simp)
        s_log = spearman_corr(btc_log, tok_log)
        beta = beta_vs_benchmark(tok_log, btc_log)
        if p_log is None:
            continue

        roll30 = pearson_corr(btc_log[-30:], tok_log[-30:]) if len(tok_log) >= 30 else None
        roll14 = pearson_corr(btc_log[-14:], tok_log[-14:]) if len(tok_log) >= 14 else None

        mean_r = sum(tok_log) / len(tok_log)
        var_r = sum((r - mean_r) ** 2 for r in tok_log) / max(1, len(tok_log) - 1)
        ann_vol = math.sqrt(var_r * 365.0) * 100.0
        period_ret = ((tok_p[-1] - tok_p[0]) / tok_p[0]) * 100.0
        mdd = max_drawdown(tok_p) * 100.0

        # Compact aligned array over all_dates (None for pre-listing dates)
        aligned = [None] * len(all_dates)
        for d in common_dates:
            aligned[date_to_idx[d]] = round_sig(tmap[d], 6)
        compact_series[sym] = aligned

        cg = cg_meta.get(sym, {})
        ex_flags = []
        if entry["binance_spot"]:
            ex_flags.append("BN-Spot")
        if entry["binance_perp"]:
            ex_flags.append("BN-Perp")
        if entry["bybit_spot"]:
            ex_flags.append("BB-Spot")
        if entry["bybit_perp"]:
            ex_flags.append("BB-Perp")

        rows.append(
            {
                "symbol": sym,
                "name": cg.get("name") or sym,
                "cg_id": cg.get("cg_id"),
                "mcap_rank": cg.get("rank"),
                "market_cap": cg.get("market_cap"),
                "vol_24h": cg.get("vol_24h"),
                "is_stable": (sym in STABLECOINS) or (ann_vol < 2.0),
                "is_gold": sym in GOLD_TOKENS,
                "price_source": klines_cache[sym]["source"],
                "exchanges": ex_flags,
                "has_binance": bool(entry["binance_spot"] or entry["binance_perp"]),
                "has_bybit": bool(entry["bybit_spot"] or entry["bybit_perp"]),
                "has_spot": bool(entry["binance_spot"] or entry["bybit_spot"]),
                "has_perp": bool(entry["binance_perp"] or entry["bybit_perp"]),
                "start_date": common_dates[0],
                "end_date": common_dates[-1],
                "n_days": len(common_dates),
                "full_history": len(common_dates) >= len(all_dates) - 2,
                "end_price": round_sig(tok_p[-1], 6),
                "period_return_pct": round(period_ret, 2),
                "ann_volatility_pct": round(ann_vol, 2),
                "max_drawdown_pct": round(mdd, 2),
                "pearson_log": round(p_log, 4),
                "pearson_simple": round(p_simp, 4) if p_simp is not None else None,
                "spearman_log": round(s_log, 4) if s_log is not None else None,
                "beta": round(beta, 3) if beta is not None else None,
                "r_squared": round(p_log ** 2, 4),
                "roll_14d": round(roll14, 4) if roll14 is not None else None,
                "roll_30d": round(roll30, 4) if roll30 is not None else None,
            }
        )

    rows.sort(key=lambda r: (r["symbol"] != "BTC", -(r["pearson_log"] or -9)))

    report = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "start_date": all_dates[0],
        "end_date": all_dates[-1],
        "total_days": len(all_dates),
        "total_tokens": len(rows),
        "dates": all_dates,
        "tokens": rows,
        "series": compact_series,
    }
    out_path = DATA_DIR / "all_cex_correlation_report.json"
    out_path.write_text(json.dumps(report), encoding="utf-8")

    non_stable = [r for r in rows if not r["is_stable"] and r["symbol"] != "BTC"]
    print(f"\nDONE! Total tokens analyzed: {len(rows)} ({len(non_stable)} non-stable alts) | Period: {all_dates[0]} -> {all_dates[-1]}")
    print("Top 10 Highest Correlation (full history):")
    full = [r for r in non_stable if r["full_history"]]
    for r in full[:10]:
        print(f"  {r['symbol']:10s} r={r['pearson_log']:+.4f} beta={r['beta']:.2f} ret={r['period_return_pct']:+.1f}% src={r['price_source']}")
    print("Bottom 10 Lowest / Negative Correlation (full history):")
    for r in full[-10:]:
        print(f"  {r['symbol']:10s} r={r['pearson_log']:+.4f} beta={r['beta']:.2f} ret={r['period_return_pct']:+.1f}% src={r['price_source']}")


if __name__ == "__main__":
    main()
