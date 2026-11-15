#!/usr/bin/env python3
"""
Enrich missing market_cap and mcap_rank entries in data/all_cex_correlation_report.json
using CoinPaprika, CoinGecko (full coins/list + /coins/markets with alias resolution),
and Binance circulating-supply fallback, strictly validated against token end_price.
"""

import json
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPORT_PATH = BASE_DIR / "data" / "all_cex_correlation_report.json"

# Force IPv4 to avoid Windows IPv6 stall on external HTTPS endpoints
_orig_gai = socket.getaddrinfo
socket.getaddrinfo = lambda h, p, f=0, t=0, pr=0, fl=0: _orig_gai(h, p, socket.AF_INET, t, pr, fl)

EXACT_CG_ALIASES = {
    "CLOUD": "sanctum-2",
    "RONIN": "ronin",
    "BTTC": "bittorrent",
    "NEIROCTO": "neiro-3",
    "BROCCOLI714": "czs-dog",
    "BABY1": "babylon",
}


def get_json(url: str, retries: int = 5, timeout: float = 20.0):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503):
                wait = min(45, 5 * (attempt + 1))
                print(f"  [HTTP {e.code}] sleeping {wait}s...")
                time.sleep(wait)
                continue
            raise
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed GET {url}")


def price_ok(cand_price: float | None, tok_price: float | None, mult: float = 1.0) -> bool:
    if not cand_price or not tok_price or cand_price <= 0 or tok_price <= 0:
        return False
    ratio = (cand_price * mult) / tok_price
    return 0.45 <= ratio <= 2.20


def alias_candidates(sym: str) -> list[tuple[str, float]]:
    out = [(sym, 1.0)]
    if sym == "BEAMX":
        out.append(("BEAM", 1.0))
    for pfx, mult in (("1000000", 1e6), ("10000", 1e4), ("1000", 1000.0), ("1M", 1e6)):
        if sym.startswith(pfx) and len(sym) > len(pfx) + 1:
            out.append((sym[len(pfx):], mult))
    return out


def main():
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    tokens = report["tokens"]
    missing = {t["symbol"]: t for t in tokens if not (t.get("market_cap") and t["market_cap"] > 0)}
    print(f"Total tokens: {len(tokens)} | Initially missing market_cap: {len(missing)}")

    # 1. CoinPaprika /v1/tickers (top 2000 coins in 1 request)
    cp_rows = get_json("https://api.coinpaprika.com/v1/tickers")
    cp_by_sym: dict[str, list[tuple[str, float, float, int | None]]] = {}
    for c in cp_rows:
        s = (c.get("symbol") or "").upper()
        q = (c.get("quotes") or {}).get("USD") or {}
        mc = q.get("market_cap") or 0
        pr = q.get("price") or 0
        if s and mc > 0 and pr > 0:
            cp_by_sym.setdefault(s, []).append((c.get("name") or s, float(mc), float(pr), c.get("rank")))

    cp_hits = 0
    for sym, tok in list(missing.items()):
        ep = tok.get("end_price")
        for s_lookup, mult in alias_candidates(sym):
            cands = sorted(cp_by_sym.get(s_lookup, []), key=lambda x: x[1], reverse=True)
            for name, mc, pr, rk in cands:
                if price_ok(pr, ep, mult):
                    tok["market_cap"] = mc
                    if not tok.get("mcap_rank") and rk:
                        tok["mcap_rank"] = rk
                    if tok.get("name") == sym and name:
                        tok["name"] = name
                    cp_hits += 1
                    del missing[sym]
                    break
            if sym not in missing:
                break
    print(f"After CoinPaprika: +{cp_hits} matched | {len(missing)} remaining")

    # 2. CoinGecko /coins/list + /coins/markets?ids=...
    if missing:
        cg_list = get_json("https://api.coingecko.com/api/v3/coins/list")
        ids_by_sym: dict[str, list[str]] = {}
        for c in cg_list:
            s = (c.get("symbol") or "").upper()
            if s:
                ids_by_sym.setdefault(s, []).append(c["id"])

        cand_ids: list[str] = []
        id_to_targets: dict[str, list[tuple[str, float]]] = {}
        for sym in missing:
            if sym in EXACT_CG_ALIASES:
                cid = EXACT_CG_ALIASES[sym]
                cand_ids.append(cid)
                id_to_targets.setdefault(cid, []).append((sym, 1.0))
            for s_lookup, mult in alias_candidates(sym):
                for cid in ids_by_sym.get(s_lookup, [])[:10]:
                    cand_ids.append(cid)
                    id_to_targets.setdefault(cid, []).append((sym, mult))

        cand_ids = list(dict.fromkeys(cand_ids))
        cg_rows: list[dict] = []
        for i in range(0, len(cand_ids), 150):
            chunk = cand_ids[i : i + 150]
            url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={','.join(chunk)}&per_page=250"
            rows = get_json(url)
            cg_rows.extend(rows)
            if i + 150 < len(cand_ids):
                time.sleep(4.0)

        best_cg: dict[str, tuple[float, int | None, str, str]] = {}
        for r in cg_rows:
            cid = r.get("id")
            mc = r.get("market_cap") or 0
            pr = r.get("current_price") or 0
            if not (mc > 0 and pr > 0):
                continue
            for sym, mult in id_to_targets.get(cid, []):
                if sym in missing and price_ok(pr, missing[sym].get("end_price"), mult):
                    if sym not in best_cg or mc > best_cg[sym][0]:
                        best_cg[sym] = (float(mc), r.get("market_cap_rank"), cid, r.get("name") or sym)

        for sym, (mc, rk, cid, nm) in best_cg.items():
            tok = missing[sym]
            tok["market_cap"] = mc
            tok["cg_id"] = cid
            if not tok.get("mcap_rank") and rk:
                tok["mcap_rank"] = rk
            if tok.get("name") == sym and nm:
                tok["name"] = nm
            del missing[sym]
        print(f"After CoinGecko full list: +{len(best_cg)} matched | {len(missing)} remaining")

    # 3. Binance product circulating supply fallback
    if missing:
        bp = get_json("https://www.binance.com/bapi/asset/v2/public/asset-service/product/get-products?includeEtf=true")
        bn_hits = 0
        for r in bp.get("data", []):
            if r.get("q") != "USDT":
                continue
            b = (r.get("b") or "").upper()
            if b not in missing:
                continue
            cs = float(r.get("cs") or 0)
            cp = float(r.get("c") or 0)
            ep = missing[b].get("end_price")
            if cs > 0 and cp > 0 and price_ok(cp, ep, 1.0):
                missing[b]["market_cap"] = cs * ep
                if missing[b].get("name") == b and r.get("an"):
                    missing[b]["name"] = r["an"]
                bn_hits += 1
                del missing[b]
        print(f"After Binance cs fallback: +{bn_hits} matched | {len(missing)} remaining")

    full_non_stable = [t for t in tokens if t["symbol"] != "BTC" and not t.get("is_stable") and t.get("full_history")]
    with_mc_full = sum(1 for t in full_non_stable if (t.get("market_cap") or 0) > 0)
    print(f"Final full-history non-stable alts with market_cap: {with_mc_full} / {len(full_non_stable)}")
    if missing:
        print("Unresolved symbols:", sorted(missing.keys()))

    REPORT_PATH.write_text(json.dumps(report, separators=(",", ":")), encoding="utf-8")
    print(f"Saved enriched report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
