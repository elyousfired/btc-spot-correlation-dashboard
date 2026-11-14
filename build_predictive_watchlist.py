#!/usr/bin/env python3
"""
Builds Page 3: Next-Rally Predictive Watchlist (Spot Only)
Ranks Binance Spot & Bybit Spot tokens by a 5-factor Follow-Probability Score (0-100)
using empirical data since 2026-07-01.
"""

import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "all_cex_correlation_report.json"
ARTIFACT_PATH = Path(
    r"C:\Users\red1e\.gemini\antigravity\brain\fc84f6c8-80d9-40b0-aa9e-07bc551807d8\btc_predictive_watchlist.html"
)
LOCAL_HTML_PATH = BASE_DIR / "btc_predictive_watchlist.html"

WRAPPED_AND_EQUITIES = {
    "WBTC", "STETH", "WBETH", "METH", "BNSOL", "BBSOL", "CBETH", "RETH", "WETH",
    "TBTC", "CBBTC", "SOLVBTC", "MSTRB", "COINX", "CRCLX", "HOODX", "PAXG", "XAUT",
    "JUPSOL", "JITOSOL", "MSOL", "ETHX", "EZETH", "WEETH", "RSETH", "PUFETH",
}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Next BTC Rally — Predictive Follow Watchlist (Spot)</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    canvas { display: block; width: 100%; }
    .tabular-nums { font-variant-numeric: tabular-nums; }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased p-4 md:p-6">
  <div class="max-w-7xl mx-auto space-y-5">

    <!-- Top Navigation Bar -->
    <nav class="bg-[var(--card)] border border-[var(--border)] rounded-xl px-4 py-2.5 shadow-sm flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <a href="all_cex_dashboard.html" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] text-[var(--muted-foreground)] border border-[var(--border)] hover:text-[var(--foreground)]">
          Correlation Screener (Spot)
        </a>
        <a href="btc_event_study.html" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] text-[var(--muted-foreground)] border border-[var(--border)] hover:text-[var(--foreground)]">
          BTC +2% &rarr; Token +10% Event Study
        </a>
        <a href="btc_predictive_watchlist.html" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)]">
          Next-Rally Predictive Watchlist
        </a>
      </div>
      <span class="text-xs font-medium text-[var(--muted-foreground)] tabular-nums">__PERIOD_LABEL__</span>
    </nav>

    <!-- Header -->
    <header class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-4">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)]">SPOT ONLY &bull; 5-Factor Predictive Model</span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">Live Quantitative Watchlist</span>
          </div>
          <h1 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]">Next BTC Rally Watchlist: Highest-Probability Followers</h1>
          <p class="text-sm text-[var(--muted-foreground)] mt-1">Ranks Spot tokens most likely to follow the next BTC surge using 5 empirical factors: Full-Period r (01/07&rarr;Now), Recent 30D Regime r, BTC &ge; +2% Hit Rate (+10%), Upside Beta (&beta;+), and +5% Consistency.</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button id="exportCsvBtn" class="px-3 py-2 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 cursor-pointer">
            Export Watchlist CSV
          </button>
        </div>
      </div>

      <!-- Filter & Weight Controls -->
      <div class="pt-3 border-t border-[var(--border)] flex flex-wrap items-center gap-3">
        <input id="searchInput" type="text" placeholder="Search ticker or name..." class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] w-48" />
        <select id="exchangeSelect" class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
          <option value="ALL">All Spot (Binance + Bybit)</option>
          <option value="BINANCE">Binance Spot</option>
          <option value="BYBIT">Bybit Spot</option>
          <option value="BOTH">Listed on BOTH Spot</option>
        </select>
        <select id="capSelect" class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
          <option value="ALL">All Market Caps</option>
          <option value="TOP50">CoinGecko Top 50</option>
          <option value="TOP100">CoinGecko Top 100</option>
          <option value="TOP250">CoinGecko Top 250</option>
        </select>
        <select id="tierSelect" class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
          <option value="ALL">All Tiers</option>
          <option value="A">Tier A Only (Score &ge; 70)</option>
          <option value="B">Tier B+ (Score &ge; 60)</option>
        </select>
        <label class="flex items-center gap-1.5 text-xs text-[var(--foreground)] cursor-pointer select-none">
          <input id="hideWrappedChk" type="checkbox" checked class="rounded" />
          <span>Hide Wrapped/Staked &amp; Stocks</span>
        </label>
        <span id="countBadge" class="ml-auto text-xs font-medium text-[var(--muted-foreground)] tabular-nums"></span>
      </div>
    </header>

    <!-- KPI Cards -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">#1 Top Predicted Follower</p>
        <div id="kpiTop1" class="mt-2 text-2xl font-bold tabular-nums text-emerald-400">--</div>
        <p id="kpiTop1Sub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Tier A High-Conviction Tokens</p>
        <div id="kpiTierA" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiTierASub" class="text-xs text-[var(--muted-foreground)] mt-1">Score &ge; 70 / 100 across all 5 factors</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Top-20 Avg +10% Hit Rate</p>
        <div id="kpiTop20Hit" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiTop20HitSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Top-20 Avg Upside Beta (&beta;+)</p>
        <div id="kpiTop20Beta" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiTop20BetaSub" class="text-xs text-[var(--muted-foreground)] mt-1">Measured strictly on BTC green days</p>
      </div>
    </section>

    <!-- Stacked Factor Chart + Methodology -->
    <section class="grid grid-cols-1 xl:grid-cols-12 gap-5">
      <div class="xl:col-span-8 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div>
            <h2 class="text-base font-semibold text-[var(--foreground)]">All Predicted Followers — Factor Score Breakdown (0–100)</h2>
            <p id="stackedSub" class="text-xs text-[var(--muted-foreground)]">Scroll to view stacked contribution across all filtered tokens</p>
          </div>
          <div class="flex flex-wrap items-center gap-3 text-xs text-[var(--muted-foreground)]">
            <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded bg-[#3b82f6]"></span>Full r (25)</span>
            <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded bg-[#06b6d4]"></span>30D r (25)</span>
            <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded bg-[#10b981]"></span>+10% Hit (25)</span>
            <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded bg-[#f59e0b]"></span>Up-Beta (15)</span>
            <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded bg-[#a855f7]"></span>+5% Consist. (10)</span>
          </div>
        </div>
        <div id="stackedContainer" class="h-[460px] overflow-y-auto pr-2 space-y-1 tabular-nums"></div>
      </div>

      <div class="xl:col-span-4 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col justify-between space-y-4">
        <div class="space-y-3">
          <h2 class="text-base font-semibold text-[var(--foreground)]">How the Model Predicts Followers</h2>
          <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">
            Statistical probability does not guarantee future pumps, but combining long-term correlation with recent regime alignment and upside-beta isolates Spot altcoins that reliably expand when BTC breaks upward:
          </p>
          <ul class="space-y-2 text-xs text-[var(--foreground)]">
            <li class="p-2.5 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <strong class="text-blue-400">1. Full-Period Coupling (25 pts):</strong> Correlation from <code>2026-07-01</code> to today ensures structural co-movement.
            </li>
            <li class="p-2.5 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <strong class="text-cyan-400">2. Recent 30D Regime (25 pts):</strong> Guards against tokens that followed in summer but decoupled recently.
            </li>
            <li class="p-2.5 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <strong class="text-emerald-400">3. +10% Surge Hit Rate (25 pts):</strong> Empirical wins across all 11 BTC &ge; +2% days (48h window).
            </li>
            <li class="p-2.5 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <strong class="text-amber-400">4. Upside Beta &beta;+ (15 pts):</strong> Measures amplification strictly on BTC positive days.
            </li>
            <li class="p-2.5 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <strong class="text-purple-400">5. +5% Consistency (10 pts):</strong> Rewards broad reliability across BTC rallies, filtering 1-hit flukes.
            </li>
          </ul>
        </div>
        <div class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-xs text-[var(--foreground)]">
          <strong>Risk Disclaimer:</strong> Quantitative screening based on historical Spot data only; always manage position sizing and invalidation levels.
        </div>
      </div>
    </section>

    <!-- Full Watchlist Table -->
    <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 class="text-base font-semibold text-[var(--foreground)]">Ranked Predictive Spot Watchlist</h2>
          <p class="text-xs text-[var(--muted-foreground)]">Sorted by Composite Follow Score (/100); click column headers to re-sort</p>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <button id="prevPageBtn" class="px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--background)] cursor-pointer">Prev</button>
          <span id="pageInfo" class="tabular-nums text-[var(--muted-foreground)]">Page 1</span>
          <button id="nextPageBtn" class="px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--background)] cursor-pointer">Next</button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs tabular-nums">
          <thead>
            <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)]">
              <th class="py-2 px-2">Rank</th>
              <th class="py-2 px-2">Tier</th>
              <th class="py-2 px-2 cursor-pointer" data-sort="mcapRank">MCap</th>
              <th class="py-2 px-2 cursor-pointer" data-sort="symbol">Token</th>
              <th class="py-2 px-2">Spot</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="price">Price</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="score">Follow Score</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="rFull">Full r</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="r30">30D r</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="upBeta">Up-Beta (&beta;+)</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="w10">+10% Rate</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="w5">+5% Rate</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="medMove">Med Move</th>
            </tr>
          </thead>
          <tbody id="watchlistBody" class="divide-y divide-[var(--border)]"></tbody>
        </table>
      </div>
    </section>

    <footer class="text-xs text-[var(--muted-foreground)] flex flex-wrap items-center justify-between gap-2 pb-4">
      <span>Sources: Binance Spot + Bybit Spot + CoinGecko Top 1000 MCap &bull; Generated __GENERATED_AT__</span>
      <span>Note: Statistical watchlist for research only; not financial advice.</span>
    </footer>
  </div>

<script>
const ITEMS = __ITEMS_JSON__;

let state = {
  search: '',
  exchange: 'ALL',
  cap: 'ALL',
  tier: 'ALL',
  hideWrapped: true,
  sortKey: 'score',
  sortDesc: true,
  page: 1,
  pageSize: 75,
};

function fmtPrice(p) {
  if (p >= 1000) return '$' + p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (p >= 1) return '$' + p.toFixed(2);
  if (p >= 0.01) return '$' + p.toFixed(4);
  return '$' + p.toPrecision(4);
}
function fmtPct(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }

function getThemeColors() {
  const cs = getComputedStyle(document.documentElement);
  const bodyCs = getComputedStyle(document.body);
  return {
    fg: cs.getPropertyValue('--foreground').trim() || bodyCs.color || '#e2e8f0',
    muted: cs.getPropertyValue('--muted-foreground').trim() || '#94a3b8',
    border: cs.getPropertyValue('--border').trim() || '#334155',
  };
}

function getFiltered() {
  const q = state.search.trim().toLowerCase();
  return ITEMS.filter(r => {
    if (state.hideWrapped && r.isWrapped) return false;
    if (state.exchange === 'BINANCE' && !r.hasBinance) return false;
    if (state.exchange === 'BYBIT' && !r.hasBybit) return false;
    if (state.exchange === 'BOTH' && !(r.hasBinance && r.hasBybit)) return false;
    if (state.cap === 'TOP50' && !(r.mcapRank <= 50)) return false;
    if (state.cap === 'TOP100' && !(r.mcapRank <= 100)) return false;
    if (state.cap === 'TOP250' && !(r.mcapRank <= 250)) return false;
    if (state.tier === 'A' && r.score < 70) return false;
    if (state.tier === 'B' && r.score < 60) return false;
    if (q && !r.symbol.toLowerCase().includes(q) && !(r.name || '').toLowerCase().includes(q)) return false;
    return true;
  });
}

function sortRows(rows) {
  const k = state.sortKey;
  return [...rows].sort((a, b) => {
    const va = a[k], vb = b[k];
    if (typeof va === 'string') return state.sortDesc ? vb.localeCompare(va) : va.localeCompare(vb);
    if (k === 'mcapRank') return state.sortDesc ? (va - vb) : (vb - va);
    return state.sortDesc ? (vb - va) : (va - vb);
  });
}

function renderKPIs(filtered) {
  document.getElementById('countBadge').textContent = `${filtered.length} Spot candidates`;
  const byScore = [...filtered].sort((a, b) => b.score - a.score);
  if (!byScore.length) return;
  const top1 = byScore[0];
  document.getElementById('kpiTop1').textContent = `${top1.symbol} (${top1.score.toFixed(1)}/100)`;
  document.getElementById('kpiTop1Sub').textContent = `r=${top1.rFull.toFixed(3)} • 30D=${top1.r30.toFixed(3)} • +10% Rate=${top1.w10.toFixed(1)}%`;

  const tierA = byScore.filter(r => r.score >= 70).length;
  document.getElementById('kpiTierA').textContent = `${tierA} Tokens`;

  const top20 = byScore.slice(0, 20);
  const avgW10 = top20.reduce((s, r) => s + r.w10, 0) / top20.length;
  const avgW5 = top20.reduce((s, r) => s + r.w5, 0) / top20.length;
  document.getElementById('kpiTop20Hit').textContent = `${avgW10.toFixed(1)}%`;
  document.getElementById('kpiTop20HitSub').textContent = `Avg +5% hit rate across Top 20: ${avgW5.toFixed(1)}%`;

  const avgUb = top20.reduce((s, r) => s + r.upBeta, 0) / top20.length;
  document.getElementById('kpiTop20Beta').textContent = `${avgUb.toFixed(2)}x`;
}

function renderStackedChart(filtered) {
  const container = document.getElementById('stackedContainer');
  if (!container) return;

  const ranked = [...filtered].sort((a, b) => b.score - a.score);
  document.getElementById('stackedSub').textContent = `Showing all ${ranked.length} filtered tokens (scroll to browse)`;
  if (!ranked.length) {
    container.innerHTML = '<div class="text-xs text-[var(--muted-foreground)] py-8 text-center">No tokens match filters</div>';
    return;
  }

  container.innerHTML = ranked.map((r, idx) => {
    return `<div class="flex items-center gap-2 px-2 py-1 rounded hover:bg-[var(--secondary)]/50 text-xs">
      <span class="w-9 text-right text-[var(--muted-foreground)] shrink-0">#${idx + 1}</span>
      <span class="w-20 font-semibold truncate text-[var(--foreground)] shrink-0" title="${r.name}">${r.symbol}</span>
      <div class="flex-1 h-3.5 bg-[var(--background)] rounded overflow-hidden flex">
        <div style="width:${r.sR.toFixed(2)}%;background:#3b82f6" title="Full r: ${r.sR.toFixed(1)}"></div>
        <div style="width:${r.sR30.toFixed(2)}%;background:#06b6d4" title="30D r: ${r.sR30.toFixed(1)}"></div>
        <div style="width:${r.sW10.toFixed(2)}%;background:#10b981" title="+10% Hit: ${r.sW10.toFixed(1)}"></div>
        <div style="width:${r.sUb.toFixed(2)}%;background:#f59e0b" title="Up-Beta: ${r.sUb.toFixed(1)}"></div>
        <div style="width:${r.sW5.toFixed(2)}%;background:#a855f7" title="+5% Consist: ${r.sW5.toFixed(1)}"></div>
      </div>
      <span class="w-12 text-right font-semibold text-emerald-400 shrink-0">${r.score.toFixed(1)}</span>
    </div>`;
  }).join('');
}

function renderTable(filtered) {
  const sorted = sortRows(filtered);
  const totalPages = Math.max(1, Math.ceil(sorted.length / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;
  const start = (state.page - 1) * state.pageSize;
  const pageRows = sorted.slice(start, start + state.pageSize);
  document.getElementById('pageInfo').textContent = `Page ${state.page} / ${totalPages} (${sorted.length} tokens)`;

  document.getElementById('watchlistBody').innerHTML = pageRows.map((r, i) => {
    const rank = start + i + 1;
    const tierBadge = r.score >= 70
      ? '<span class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold">Tier A</span>'
      : r.score >= 60
      ? '<span class="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-semibold">Tier B</span>'
      : '<span class="px-2 py-0.5 rounded-full bg-[var(--secondary)] text-[var(--muted-foreground)]">Tier C</span>';
    const exBadges = [
      r.hasBinance ? '<span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400">BN</span>' : '',
      r.hasBybit ? '<span class="px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-400">BB</span>' : '',
    ].join(' ');
    return `<tr class="hover:bg-[var(--secondary)]/40">
      <td class="py-2 px-2 text-[var(--muted-foreground)]">${rank}</td>
      <td class="py-2 px-2">${tierBadge}</td>
      <td class="py-2 px-2 text-[var(--muted-foreground)]">${r.mcapRank < 999999 ? '#' + r.mcapRank : '--'}</td>
      <td class="py-2 px-2"><span class="font-semibold text-[var(--foreground)]">${r.symbol}</span> <span class="text-[var(--muted-foreground)]">${r.name !== r.symbol ? r.name.slice(0, 15) : ''}</span></td>
      <td class="py-2 px-2">${exBadges}</td>
      <td class="py-2 px-2 text-right">${fmtPrice(r.price)}</td>
      <td class="py-2 px-2 text-right font-bold text-emerald-400">${r.score.toFixed(1)}</td>
      <td class="py-2 px-2 text-right">${r.rFull.toFixed(3)}</td>
      <td class="py-2 px-2 text-right">${r.r30.toFixed(3)}</td>
      <td class="py-2 px-2 text-right">${r.upBeta.toFixed(2)}x</td>
      <td class="py-2 px-2 text-right font-semibold">${r.w10.toFixed(1)}% (${r.wins10}/${r.nEvents})</td>
      <td class="py-2 px-2 text-right">${r.w5.toFixed(1)}%</td>
      <td class="py-2 px-2 text-right text-emerald-400">${fmtPct(r.medMove)}</td>
    </tr>`;
  }).join('');
}

function exportCsv() {
  const sorted = sortRows(getFiltered());
  const header = ['Rank', 'Tier', 'MCap_Rank', 'Symbol', 'Name', 'Price_USD', 'Follow_Score', 'Full_r', 'Roll30D_r', 'Upside_Beta', 'Win10_Pct', 'Wins10', 'Events', 'Win5_Pct', 'Median_Event_Move_Pct'];
  const lines = [header.join(',')];
  sorted.forEach((r, idx) => {
    const tier = r.score >= 70 ? 'A' : r.score >= 60 ? 'B' : 'C';
    lines.push([idx + 1, tier, r.mcapRank < 999999 ? r.mcapRank : '', r.symbol, `"${(r.name || '').replace(/"/g, '""')}"`, r.price, r.score.toFixed(2), r.rFull, r.r30, r.upBeta, r.w10.toFixed(2), r.wins10, r.nEvents, r.w5.toFixed(2), r.medMove.toFixed(2)].join(','));
  });
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'btc_next_rally_watchlist_spot.csv'; a.click();
  URL.revokeObjectURL(url);
}

function renderAll() {
  const f = getFiltered();
  renderKPIs(f);
  renderStackedChart(f);
  renderTable(f);
}

document.getElementById('searchInput').oninput = e => { state.search = e.target.value; state.page = 1; renderAll(); };
document.getElementById('exchangeSelect').onchange = e => { state.exchange = e.target.value; state.page = 1; renderAll(); };
document.getElementById('capSelect').onchange = e => { state.cap = e.target.value; state.page = 1; renderAll(); };
document.getElementById('tierSelect').onchange = e => { state.tier = e.target.value; state.page = 1; renderAll(); };
document.getElementById('hideWrappedChk').onchange = e => { state.hideWrapped = e.target.checked; state.page = 1; renderAll(); };
document.getElementById('exportCsvBtn').onclick = exportCsv;
document.getElementById('prevPageBtn').onclick = () => { if (state.page > 1) { state.page--; renderTable(getFiltered()); } };
document.getElementById('nextPageBtn').onclick = () => { state.page++; renderTable(getFiltered()); };
document.querySelectorAll('th[data-sort]').forEach(th => {
  th.onclick = () => {
    const k = th.getAttribute('data-sort');
    if (state.sortKey === k) state.sortDesc = !state.sortDesc;
    else { state.sortKey = k; state.sortDesc = k !== 'mcapRank'; }
    state.page = 1; renderTable(getFiltered());
  };
});
window.onresize = () => renderAll();

renderAll();
</script>
</body>
</html>
"""


def main():
    report = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    dates = report["dates"]
    btc = report["series"]["BTC"]
    btc_log = [math.log(btc[i] / btc[i - 1]) for i in range(1, len(dates))]
    btc_ev = [i for i in range(1, len(dates) - 1) if (btc[i] - btc[i - 1]) / btc[i - 1] * 100 >= 2.0]

    items = []
    for t in report["tokens"]:
        sym = t["symbol"]
        if sym == "BTC" or t["is_stable"] or not t["full_history"]:
            continue
        s = report["series"][sym]
        if any(v is None or v <= 0 for v in s):
            continue

        tok_log = [math.log(s[i] / s[i - 1]) for i in range(1, len(dates))]
        r_full = t["pearson_log"] or 0.0
        r_30 = t["roll_30d"] or 0.0

        up_pairs = [(tl, bl) for tl, bl in zip(tok_log, btc_log) if bl > 0]
        mb = sum(b for _, b in up_pairs) / len(up_pairs)
        mt = sum(a for a, _ in up_pairs) / len(up_pairs)
        var_b = sum((b - mb) ** 2 for _, b in up_pairs)
        up_beta = sum((a - mt) * (b - mb) for a, b in up_pairs) / var_b if var_b > 0 else 0.0

        moves = [max((s[i] - s[i - 1]) / s[i - 1] * 100, (s[i + 1] - s[i - 1]) / s[i - 1] * 100) for i in btc_ev]
        wins10 = sum(1 for m in moves if m >= 10.0)
        wins5 = sum(1 for m in moves if m >= 5.0)
        w10 = wins10 / len(moves) * 100.0
        w5 = wins5 / len(moves) * 100.0
        med_move = sorted(moves)[len(moves) // 2]

        s_r = max(0.0, min(1.0, r_full)) * 25.0
        s_r30 = max(0.0, min(1.0, r_30)) * 25.0
        s_w10 = min(1.0, w10 / 65.0) * 25.0
        s_ub = max(0.0, min(1.0, up_beta / 2.0)) * 15.0
        s_w5 = min(1.0, w5 / 90.0) * 10.0
        score = s_r + s_r30 + s_w10 + s_ub + s_w5

        items.append(
            {
                "symbol": sym,
                "name": t["name"],
                "mcapRank": t["mcap_rank"] if t["mcap_rank"] else 999999,
                "isWrapped": sym in WRAPPED_AND_EQUITIES,
                "hasBinance": t["has_binance"],
                "hasBybit": t["has_bybit"],
                "price": t["end_price"],
                "score": round(score, 2),
                "sR": round(s_r, 2),
                "sR30": round(s_r30, 2),
                "sW10": round(s_w10, 2),
                "sUb": round(s_ub, 2),
                "sW5": round(s_w5, 2),
                "rFull": round(r_full, 4),
                "r30": round(r_30, 4),
                "upBeta": round(up_beta, 3),
                "w10": round(w10, 2),
                "wins10": wins10,
                "nEvents": len(moves),
                "w5": round(w5, 2),
                "medMove": round(med_move, 2),
            }
        )

    items.sort(key=lambda x: x["score"], reverse=True)
    pure = [x for x in items if not x["isWrapped"]]
    print(f"Total Spot Watchlist candidates: {len(items)} ({len(pure)} pure altcoins)")
    print("TOP 25 PURE SPOT ALTCOINS PREDICTED TO FOLLOW NEXT BTC RALLY:")
    for idx, x in enumerate(pure[:25], 1):
        rk = f"#{x['mcapRank']}" if x["mcapRank"] < 999999 else "--"
        print(
            f"{idx:2d}. {x['symbol']:9s} ({rk:>5s}) | Score={x['score']:5.1f} | "
            f"r={x['rFull']:.3f} | r30={x['r30']:.3f} | UpB={x['upBeta']:.2f} | "
            f"+10%={x['wins10']}/{x['nEvents']} ({x['w10']:4.1f}%) | +5%={x['w5']:4.1f}% | Med={x['medMove']:+.1f}%"
        )

    period_label = f"{report['start_date']} -> {report['end_date']} ({report['total_days']}d)"
    html = HTML_TEMPLATE.replace("__ITEMS_JSON__", json.dumps(items, separators=(",", ":")))
    html = html.replace("__PERIOD_LABEL__", period_label)
    html = html.replace("__GENERATED_AT__", report["generated_at_utc"])

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(html, encoding="utf-8")

    standalone_vars = (
        "<style>:root{--background:#0b0f17;--card:#131a26;--foreground:#e5e7eb;"
        "--muted-foreground:#9ca3af;--border:#243044;--primary:#3b82f6;"
        "--primary-foreground:#ffffff;--secondary:#1e293b;--secondary-foreground:#e2e8f0;}</style>"
    )
    local_html = html.replace("</head>", f"  {standalone_vars}\n</head>")
    LOCAL_HTML_PATH.write_text(local_html, encoding="utf-8")
    print(f"\nBuilt Predictive Watchlist at:\n  - {ARTIFACT_PATH}\n  - {LOCAL_HTML_PATH}")


if __name__ == "__main__":
    main()
