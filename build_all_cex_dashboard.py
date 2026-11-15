#!/usr/bin/env python3
"""
Builds the Market-Wide Binance + Bybit BTC-Token Correlation Dashboard HTML
from data/all_cex_correlation_report.json.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "all_cex_correlation_report.json"
ARTIFACT_PATH = Path(
    r"C:\Users\red1e\.gemini\antigravity\brain\fc84f6c8-80d9-40b0-aa9e-07bc551807d8\btc_all_cex_correlation_dashboard.html"
)
LOCAL_HTML_PATH = BASE_DIR / "all_cex_dashboard.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BTC – All Binance & Bybit Tokens Correlation Screener</title>
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
        <a href="all_cex_dashboard.html" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)]">
          Correlation Screener (Spot)
        </a>
        <a href="btc_event_study.html" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] text-[var(--muted-foreground)] border border-[var(--border)] hover:text-[var(--foreground)]">
          BTC +2% &rarr; Token +10% Event Study
        </a>
        <a href="btc_predictive_watchlist.html" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] text-[var(--muted-foreground)] border border-[var(--border)] hover:text-[var(--foreground)]">
          Next-Rally Predictive Watchlist
        </a>
      </div>
      <span class="text-xs font-medium text-[var(--muted-foreground)]">Binance Spot + Bybit Spot</span>
    </nav>

    <!-- Header -->
    <header class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-4">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)]">SPOT ONLY &bull; Binance Spot + Bybit Spot + CoinGecko MCap</span>
            <span id="periodBadge" class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--primary)] text-[var(--primary-foreground)]"></span>
          </div>
          <h1 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]">BTC – Spot Market Correlation Screener (Binance &amp; Bybit Spot)</h1>
          <p class="text-sm text-[var(--muted-foreground)] mt-1">All active USDT Spot pairs aligned by UTC daily closes from July 1, 2026. Zero futures/perps noise.</p>
        </div>

        <!-- Date & Metric Controls -->
        <div class="flex flex-wrap items-end gap-3">
          <div>
            <label for="startDateInput" class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Start Date</label>
            <input id="startDateInput" type="date" class="px-3 py-1.5 rounded-lg text-sm bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]" />
          </div>
          <div>
            <label for="endDateInput" class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">End Date</label>
            <input id="endDateInput" type="date" class="px-3 py-1.5 rounded-lg text-sm bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]" />
          </div>
          <div>
            <label for="metricSelect" class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Correlation Metric</label>
            <select id="metricSelect" class="px-3 py-1.5 rounded-lg text-sm bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
              <option value="pearsonLog">Pearson (Log Returns)</option>
              <option value="pearsonSimple">Pearson (Simple % Returns)</option>
              <option value="spearmanLog">Spearman Rank (Log Returns)</option>
            </select>
          </div>
          <button id="resetDateBtn" class="px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] hover:opacity-90 cursor-pointer">Reset 01/07/2026</button>
        </div>
      </div>

      <!-- Filter Bar -->
      <div class="pt-3 border-t border-[var(--border)] flex flex-wrap items-center gap-3">
        <input id="searchInput" type="text" placeholder="Search ticker or name (e.g. SOL, PEPE, TAO)..." class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] w-64" />
        <select id="exchangeSelect" class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
          <option value="ALL">All Spot (Binance + Bybit)</option>
          <option value="BINANCE">Binance Spot</option>
          <option value="BYBIT">Bybit Spot</option>
          <option value="BOTH">Listed on BOTH Spot Exchanges</option>
          <option value="BN_ONLY">Binance Spot Exclusive</option>
          <option value="BB_ONLY">Bybit Spot Exclusive</option>
        </select>
        <select id="capSelect" class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
          <option value="ALL">All Market Caps</option>
          <option value="TOP50">CoinGecko Top 50</option>
          <option value="TOP100">CoinGecko Top 100</option>
          <option value="TOP250">CoinGecko Top 250</option>
          <option value="SMALL">Rank &gt; 250 or Unranked</option>
        </select>
        <label class="flex items-center gap-1.5 text-xs text-[var(--foreground)] cursor-pointer select-none">
          <input id="fullHistoryChk" type="checkbox" checked class="rounded" />
          <span>Full Period Only (Since Start Date)</span>
        </label>
        <label class="flex items-center gap-1.5 text-xs text-[var(--foreground)] cursor-pointer select-none">
          <input id="hideStableChk" type="checkbox" checked class="rounded" />
          <span>Hide Stablecoins</span>
        </label>
        <span id="filterCountBadge" class="ml-auto text-xs font-medium text-[var(--muted-foreground)] tabular-nums"></span>
      </div>
    </header>

    <!-- KPI Cards -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Market Average / Median BTC Corr</p>
        <div id="kpiAvgCorr" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiAvgCorrSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Strongest Positive Correlation</p>
        <div id="kpiMaxCorr" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiMaxCorrSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Most Decoupled / Inverse Token</p>
        <div id="kpiMinCorr" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiMinCorrSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">BTC Return &amp; Highest Beta (&beta;)</p>
        <div id="kpiBtcBeta" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiBtcBetaSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
    </section>

    <!-- Histogram + Top/Bottom Bar Ranking -->
    <section class="grid grid-cols-1 xl:grid-cols-12 gap-5">
      <div class="xl:col-span-5 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col">
        <div class="mb-3">
          <h2 class="text-base font-semibold text-[var(--foreground)]">Market-Wide Correlation Distribution</h2>
          <p class="text-xs text-[var(--muted-foreground)]">Distribution of BTC correlations across all filtered Binance &amp; Bybit tokens</p>
        </div>
        <canvas id="histCanvas" class="w-full h-[360px]"></canvas>
        <p id="histHoverInfo" class="text-xs text-[var(--muted-foreground)] mt-2 h-4 tabular-nums">Hover any bucket to inspect token count</p>
      </div>

      <div class="xl:col-span-7 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
          <div>
            <h2 class="text-base font-semibold text-[var(--foreground)]">Full Ranked Leaderboard (Click Any Bar to Inspect)</h2>
            <p id="leaderboardSub" class="text-xs text-[var(--muted-foreground)]">All filtered tokens ranked by selected mode</p>
          </div>
          <select id="rankModeSelect" class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
            <option value="HIGHEST_CORR">All Tokens: Most Correlated</option>
            <option value="LOWEST_CORR">All Tokens: Least Correlated / Negative</option>
            <option value="HIGHEST_BETA">All Tokens: Highest Beta (&beta;)</option>
            <option value="TOP_RETURN">All Tokens: Period Return %</option>
            <option value="GAIN_PER_MCAP">All Tokens: Gain % / MCap ($M)</option>
            <option value="IMPLIED_CAP_GAIN">All Tokens: Implied Cap Gain ($)</option>
          </select>
        </div>
        <div id="barListContainer" class="h-[390px] overflow-y-auto pr-2 space-y-1 tabular-nums"></div>
      </div>
    </section>

    <!-- Token Deep-Dive -->
    <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
        <div>
          <h2 id="deepDiveTitle" class="text-lg font-semibold text-[var(--foreground)]">Token Deep-Dive: BTC vs ETH</h2>
          <p id="deepDiveSub" class="text-xs text-[var(--muted-foreground)]">--</p>
        </div>
        <div class="flex items-center gap-2">
          <label for="tokenSelect" class="text-xs font-medium text-[var(--muted-foreground)]">Quick Select:</label>
          <select id="tokenSelect" class="px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] max-w-xs"></select>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold text-[var(--foreground)]">Rolling Correlation vs BTC</h3>
            <div class="flex items-center gap-3 text-xs text-[var(--muted-foreground)]">
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#3b82f6]"></span>30D</span>
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#f59e0b]"></span>14D</span>
            </div>
          </div>
          <canvas id="rollingCanvas" class="w-full h-[240px]"></canvas>
          <p id="rollingHoverInfo" class="text-xs text-[var(--muted-foreground)] mt-2 h-4 tabular-nums">Hover over chart for rolling values</p>
        </div>

        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold text-[var(--foreground)]">Normalized Price (Base = 100)</h3>
            <div class="flex items-center gap-3 text-xs text-[var(--muted-foreground)]">
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#f97316]"></span>BTC</span>
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#10b981]"></span><span id="perfLegendToken">Token</span></span>
            </div>
          </div>
          <canvas id="perfCanvas" class="w-full h-[240px]"></canvas>
          <p id="perfHoverInfo" class="text-xs text-[var(--muted-foreground)] mt-2 h-4 tabular-nums">Hover over chart to compare performance</p>
        </div>

        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold text-[var(--foreground)]">Daily Log Returns Scatter &amp; OLS</h3>
            <span id="scatterStatsBadge" class="text-xs font-medium text-[var(--muted-foreground)] tabular-nums"></span>
          </div>
          <canvas id="scatterCanvas" class="w-full h-[240px]"></canvas>
          <p id="scatterHoverInfo" class="text-xs text-[var(--muted-foreground)] mt-2 h-4 tabular-nums">X: BTC Daily Return % | Y: Token Daily Return %</p>
        </div>
      </div>
    </section>

    <!-- Full Screener Table -->
    <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 class="text-base font-semibold text-[var(--foreground)]">Complete Exchange Token Screener</h2>
          <p class="text-xs text-[var(--muted-foreground)]">Click any column header to sort; click any row to load into Deep-Dive charts above</p>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <button id="prevPageBtn" class="px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--background)] cursor-pointer">Prev</button>
          <span id="pageInfo" class="tabular-nums text-[var(--muted-foreground)]">Page 1</span>
          <button id="nextPageBtn" class="px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--background)] cursor-pointer">Next</button>
          <select id="pageSizeSelect" class="px-2 py-1 rounded border border-[var(--border)] bg-[var(--background)]">
            <option value="50">50 / page</option>
            <option value="100" selected>100 / page</option>
            <option value="250">250 / page</option>
            <option value="1000">Show All</option>
          </select>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)]">
              <th class="py-2 px-2 font-semibold cursor-pointer" data-sort="mcapRank">MCap #</th>
              <th class="py-2 px-2 font-semibold cursor-pointer" data-sort="symbol">Token</th>
              <th class="py-2 px-2 font-semibold">Exchanges</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="marketCap" title="CoinGecko Market Cap (USD)">MCap</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="nDays">Days</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="endPrice">Price (USDT)</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="periodReturnPct">Return %</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="gainPerMcap" title="Period Return % divided by Market Cap in $M">Gain / MCap</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="impliedCapGainUsd" title="Estimated USD Market Cap gained or lost over selected period">Cap Gain $</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="activeCorr" title="Full selected period starting 2026-07-01">Corr (01/07→Now)</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="spearmanLog" title="Full selected period Spearman">Spearman (Full)</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="beta">Beta (&beta;)</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="rSquared">R&sup2;</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="latestRoll30" title="Trailing 30-day rolling window for comparison">Last 30D</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="annVolPct">Vol (Ann.)</th>
              <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="mddPct">Max DD</th>
            </tr>
          </thead>
          <tbody id="metricsTableBody" class="divide-y divide-[var(--border)] tabular-nums"></tbody>
        </table>
      </div>
    </section>

    <footer class="text-xs text-[var(--muted-foreground)] flex flex-wrap items-center justify-between gap-2 pb-4">
      <span>Sources: Binance Spot &amp; Futures + Bybit Spot &amp; Linear + CoinGecko Top 1000 MCap &bull; Generated __GENERATED_AT__</span>
      <span>Note: Quantitative correlation research only; not financial advice.</span>
    </footer>
  </div>

<script>
const RAW = __REPORT_JSON__;

function pearson(x, y) {
  const n = x.length;
  if (n < 5 || n !== y.length) return null;
  let mx = 0, my = 0;
  for (let i = 0; i < n; i++) { mx += x[i]; my += y[i]; }
  mx /= n; my /= n;
  let num = 0, dx = 0, dy = 0;
  for (let i = 0; i < n; i++) {
    const a = x[i] - mx, b = y[i] - my;
    num += a * b; dx += a * a; dy += b * b;
  }
  const den = Math.sqrt(dx * dy);
  return den === 0 ? null : num / den;
}

function avgRanks(arr) {
  const idx = arr.map((v, i) => ({ v, i })).sort((a, b) => a.v - b.v);
  const ranks = new Array(arr.length);
  let i = 0;
  while (i < idx.length) {
    let j = i;
    while (j + 1 < idx.length && idx[j + 1].v === idx[i].v) j++;
    const avg = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) ranks[idx[k].i] = avg;
    i = j + 1;
  }
  return ranks;
}

function spearman(x, y) {
  if (x.length < 5 || x.length !== y.length) return null;
  return pearson(avgRanks(x), avgRanks(y));
}

function calcBetaAlpha(tokR, btcR) {
  const n = tokR.length;
  if (n < 5) return { beta: null, alpha: null };
  let mt = 0, mb = 0;
  for (let i = 0; i < n; i++) { mt += tokR[i]; mb += btcR[i]; }
  mt /= n; mb /= n;
  let cov = 0, varb = 0;
  for (let i = 0; i < n; i++) {
    cov += (tokR[i] - mt) * (btcR[i] - mb);
    varb += (btcR[i] - mb) ** 2;
  }
  if (varb === 0) return { beta: null, alpha: null };
  const beta = cov / varb;
  return { beta, alpha: mt - beta * mb };
}

function maxDrawdown(prices) {
  let peak = prices[0], mdd = 0;
  for (const p of prices) {
    if (p > peak) peak = p;
    const dd = (p - peak) / peak;
    if (dd < mdd) mdd = dd;
  }
  return mdd;
}

function fmtPrice(p) {
  if (p == null) return '--';
  if (p >= 1000) return '$' + p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (p >= 1) return '$' + p.toFixed(2);
  if (p >= 0.01) return '$' + p.toFixed(4);
  return '$' + p.toPrecision(4);
}
function fmtPct(v) { return v == null ? '--' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%'; }
function fmtCorr(v) { return v == null ? '--' : (v >= 0 ? '+' : '') + v.toFixed(3); }
function fmtMcap(v) {
  if (v == null || v <= 0) return '--';
  if (v >= 1e9) return '$' + (v / 1e9).toFixed(2) + 'B';
  if (v >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M';
  return '$' + (v / 1e3).toFixed(0) + 'K';
}
function fmtGainMcap(v) {
  if (v == null) return '--';
  const dec = Math.abs(v) >= 0.01 ? 3 : 4;
  return (v >= 0 ? '+' : '') + v.toFixed(dec) + '%/M';
}
function fmtSignedUsd(v) {
  if (v == null) return '--';
  const sign = v >= 0 ? '+' : '-';
  const a = Math.abs(v);
  if (a >= 1e9) return sign + '$' + (a / 1e9).toFixed(2) + 'B';
  if (a >= 1e6) return sign + '$' + (a / 1e6).toFixed(1) + 'M';
  if (a >= 1e3) return sign + '$' + (a / 1e3).toFixed(0) + 'K';
  return sign + '$' + a.toFixed(0);
}

function getThemeColors() {
  const cs = getComputedStyle(document.documentElement);
  const bodyCs = getComputedStyle(document.body);
  return {
    fg: cs.getPropertyValue('--foreground').trim() || bodyCs.color || '#e2e8f0',
    muted: cs.getPropertyValue('--muted-foreground').trim() || '#94a3b8',
    border: cs.getPropertyValue('--border').trim() || '#334155',
    isLight: document.documentElement.classList.contains('light'),
  };
}

function setupCanvas(canvas, cssHeight) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = Math.max(280, rect.width || canvas.parentElement.clientWidth || 450);
  const h = cssHeight || rect.height || 300;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
}

const allDates = RAW.dates;
const seriesMap = RAW.series;
const tokenMetaList = RAW.tokens;

let state = {
  startDate: RAW.start_date,
  endDate: RAW.end_date,
  metric: 'pearsonLog',
  search: '',
  exchange: 'ALL',
  cap: 'ALL',
  fullHistoryOnly: true,
  hideStable: true,
  rankMode: 'HIGHEST_CORR',
  sortKey: 'activeCorr',
  sortDesc: true,
  page: 1,
  pageSize: 100,
  selectedSymbol: 'ETH',
  computedRows: [],
  btcRow: null,
  barHitBoxes: [],
  histHitBoxes: [],
};

function recomputeAll() {
  const indices = [];
  const winDates = [];
  for (let i = 0; i < allDates.length; i++) {
    if (allDates[i] >= state.startDate && allDates[i] <= state.endDate) {
      indices.push(i);
      winDates.push(allDates[i]);
    }
  }
  if (winDates.length < 6) return;

  const btcArr = seriesMap['BTC'];
  const rows = [];

  for (const meta of tokenMetaList) {
    const arr = seriesMap[meta.symbol];
    if (!arr) continue;
    const validDates = [], tokP = [], btcP = [];
    for (let k = 0; k < indices.length; k++) {
      const idx = indices[k];
      const tv = arr[idx], bv = btcArr[idx];
      if (tv != null && bv != null && tv > 0 && bv > 0) {
        validDates.push(winDates[k]);
        tokP.push(tv);
        btcP.push(bv);
      }
    }
    if (tokP.length < 10) continue;

    const tokLog = [], btcLog = [], tokSimp = [], btcSimp = [];
    for (let i = 1; i < tokP.length; i++) {
      tokLog.push(Math.log(tokP[i] / tokP[i - 1]));
      btcLog.push(Math.log(btcP[i] / btcP[i - 1]));
      tokSimp.push((tokP[i] - tokP[i - 1]) / tokP[i - 1]);
      btcSimp.push((btcP[i] - btcP[i - 1]) / btcP[i - 1]);
    }

    const pearsonLog = pearson(btcLog, tokLog);
    if (pearsonLog == null) continue;
    const pearsonSimple = pearson(btcSimp, tokSimp);
    const spearmanLog = spearman(btcLog, tokLog);
    const { beta, alpha } = calcBetaAlpha(tokLog, btcLog);
    const activeCorr = state.metric === 'pearsonSimple' ? pearsonSimple : state.metric === 'spearmanLog' ? spearmanLog : pearsonLog;
    const rSquared = activeCorr != null ? activeCorr * activeCorr : null;
    const latestRoll30 = tokLog.length >= 30 ? pearson(btcLog.slice(-30), tokLog.slice(-30)) : null;

    const meanR = tokLog.reduce((a, b) => a + b, 0) / tokLog.length;
    const varR = tokLog.reduce((a, b) => a + (b - meanR) ** 2, 0) / Math.max(1, tokLog.length - 1);
    const annVolPct = Math.sqrt(varR * 365) * 100;
    const periodReturnPct = ((tokP[tokP.length - 1] - tokP[0]) / tokP[0]) * 100;
    const marketCap = (meta.market_cap && meta.market_cap > 0) ? meta.market_cap : null;
    const gainPerMcap = marketCap ? (periodReturnPct / (marketCap / 1e6)) : null;
    let lastFullPrice = null;
    for (let j = arr.length - 1; j >= 0; j--) {
      if (arr[j] != null && arr[j] > 0) { lastFullPrice = arr[j]; break; }
    }
    const impliedCapGainUsd = (marketCap && lastFullPrice)
      ? marketCap * ((tokP[tokP.length - 1] - tokP[0]) / lastFullPrice)
      : null;
    const mddPct = maxDrawdown(tokP) * 100;

    rows.push({
      ...meta,
      mcapRank: meta.mcap_rank ?? 999999,
      marketCap,
      gainPerMcap,
      impliedCapGainUsd,
      nDays: tokP.length,
      fullHistory: tokP.length >= winDates.length - 2,
      validDates,
      retDates: validDates.slice(1),
      tokP,
      btcP,
      tokLog,
      btcLog,
      endPrice: tokP[tokP.length - 1],
      periodReturnPct,
      annVolPct,
      mddPct,
      pearsonLog,
      pearsonSimple,
      spearmanLog,
      activeCorr,
      beta,
      alpha,
      rSquared,
      latestRoll30,
    });
  }

  state.btcRow = rows.find(r => r.symbol === 'BTC');
  state.computedRows = rows;
  document.getElementById('periodBadge').textContent = `${winDates[0]} → ${winDates[winDates.length - 1]} (${winDates.length}d)`;
}

function getFilteredAlts() {
  const q = state.search.trim().toLowerCase();
  return state.computedRows.filter(r => {
    if (r.symbol === 'BTC') return false;
    if (state.hideStable && r.is_stable) return false;
    if (state.fullHistoryOnly && !r.fullHistory) return false;
    if (state.exchange === 'BINANCE' && !r.has_binance) return false;
    if (state.exchange === 'BYBIT' && !r.has_bybit) return false;
    if (state.exchange === 'BOTH' && !(r.has_binance && r.has_bybit)) return false;
    if (state.exchange === 'BN_ONLY' && !(r.has_binance && !r.has_bybit)) return false;
    if (state.exchange === 'BB_ONLY' && !(!r.has_binance && r.has_bybit)) return false;
    if (state.cap === 'TOP50' && !(r.mcap_rank && r.mcap_rank <= 50)) return false;
    if (state.cap === 'TOP100' && !(r.mcap_rank && r.mcap_rank <= 100)) return false;
    if (state.cap === 'TOP250' && !(r.mcap_rank && r.mcap_rank <= 250)) return false;
    if (state.cap === 'SMALL' && (r.mcap_rank && r.mcap_rank <= 250)) return false;
    if (q && !r.symbol.toLowerCase().includes(q) && !(r.name || '').toLowerCase().includes(q)) return false;
    return true;
  });
}

function renderKPIs(alts) {
  document.getElementById('filterCountBadge').textContent = `Showing ${alts.length} tokens (of ${state.computedRows.length - 1} tracked)`;
  if (!alts.length) return;

  const corrs = alts.map(r => r.activeCorr).filter(v => v != null).sort((a, b) => a - b);
  const avg = corrs.reduce((s, v) => s + v, 0) / corrs.length;
  const med = corrs[Math.floor(corrs.length / 2)];
  const above05 = corrs.filter(v => v >= 0.5).length;

  document.getElementById('kpiAvgCorr').textContent = `${fmtCorr(avg)} / ${fmtCorr(med)}`;
  document.getElementById('kpiAvgCorrSub').textContent = `${above05}/${corrs.length} (${((above05 / corrs.length) * 100).toFixed(0)}%) have r ≥ 0.50`;

  const byCorr = [...alts].sort((a, b) => b.activeCorr - a.activeCorr);
  const topC = byCorr[0], lowC = byCorr[byCorr.length - 1];
  document.getElementById('kpiMaxCorr').textContent = `${topC.symbol} (${fmtCorr(topC.activeCorr)})`;
  document.getElementById('kpiMaxCorrSub').textContent = `${topC.exchanges.join(' · ')} | R²=${(topC.rSquared * 100).toFixed(1)}%`;

  document.getElementById('kpiMinCorr').textContent = `${lowC.symbol} (${fmtCorr(lowC.activeCorr)})`;
  document.getElementById('kpiMinCorrSub').textContent = `Return: ${fmtPct(lowC.periodReturnPct)} | ${lowC.exchanges.join(' · ')}`;

  const topBeta = [...alts].filter(r => r.beta != null).sort((a, b) => b.beta - a.beta)[0];
  document.getElementById('kpiBtcBeta').textContent = `BTC ${fmtPct(state.btcRow?.periodReturnPct)}`;
  document.getElementById('kpiBtcBetaSub').textContent = topBeta ? `Max β: ${topBeta.symbol} (${topBeta.beta.toFixed(2)}x, Ret ${fmtPct(topBeta.periodReturnPct)})` : '--';
}

function renderHistogram(alts) {
  const canvas = document.getElementById('histCanvas');
  const { ctx, w, h } = setupCanvas(canvas, 360);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  // Bins from -0.4 to 1.0 step 0.1
  const bins = [];
  for (let b = -4; b < 10; b++) {
    bins.push({ lo: b / 10, hi: (b + 1) / 10, count: 0, label: `${(b / 10).toFixed(1)}` });
  }
  alts.forEach(r => {
    const v = r.activeCorr;
    if (v == null) return;
    let idx = Math.floor(v * 10) + 4;
    if (v >= 1.0) idx = 13;
    idx = Math.max(0, Math.min(13, idx));
    bins[idx].count++;
  });

  const maxCount = Math.max(1, ...bins.map(b => b.count));
  const padL = 38, padR = 14, padT = 18, padB = 30;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const stepW = plotW / bins.length;
  const barW = stepW * 0.76;

  ctx.font = '12px sans-serif';
  for (let k = 0; k <= 4; k++) {
    const val = Math.round((k / 4) * maxCount);
    const y = padT + plotH - (val / maxCount) * plotH;
    ctx.strokeStyle = theme.border;
    ctx.lineWidth = 0.6;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
    ctx.fillStyle = theme.muted;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(val), padL - 6, y);
  }

  state.histHitBoxes = [];
  bins.forEach((b, i) => {
    const x = padL + i * stepW + (stepW - barW) / 2;
    const bh = (b.count / maxCount) * plotH;
    const y = padT + plotH - bh;
    ctx.fillStyle = b.lo < 0 ? '#ef4444' : b.lo < 0.4 ? '#f59e0b' : b.lo < 0.7 ? '#3b82f6' : '#10b981';
    ctx.beginPath();
    ctx.roundRect(x, y, barW, Math.max(2, bh), [4, 4, 0, 0]);
    ctx.fill();

    if (b.count > 0) {
      ctx.fillStyle = theme.fg;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(String(b.count), x + barW / 2, y - 3);
    }
    if (i % 2 === 0) {
      ctx.fillStyle = theme.muted;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(b.label, x + barW / 2, padT + plotH + 8);
    }
    state.histHitBoxes.push({ x1: x, x2: x + barW, bin: b });
  });

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const hit = state.histHitBoxes.find(b => mx >= b.x1 && mx <= b.x2);
    if (hit) {
      document.getElementById('histHoverInfo').textContent =
        `Range [${hit.bin.lo.toFixed(1)}, ${hit.bin.hi.toFixed(1)}): ${hit.bin.count} tokens`;
    }
  };
}

function renderBarChart(alts) {
  const container = document.getElementById('barListContainer');
  if (!container) return;

  let subset = [...alts];
  let modeVal = r => r.activeCorr ?? 0;
  let fmtFn = fmtCorr;

  if (state.rankMode === 'HIGHEST_CORR') {
    subset.sort((a, b) => (b.activeCorr ?? -9) - (a.activeCorr ?? -9));
  } else if (state.rankMode === 'LOWEST_CORR') {
    subset.sort((a, b) => (a.activeCorr ?? 9) - (b.activeCorr ?? 9));
  } else if (state.rankMode === 'HIGHEST_BETA') {
    subset.sort((a, b) => (b.beta ?? -9) - (a.beta ?? -9));
    modeVal = r => r.beta ?? 0;
    fmtFn = v => v.toFixed(2) + 'x';
  } else if (state.rankMode === 'TOP_RETURN') {
    subset.sort((a, b) => b.periodReturnPct - a.periodReturnPct);
    modeVal = r => r.periodReturnPct;
    fmtFn = fmtPct;
  } else if (state.rankMode === 'GAIN_PER_MCAP') {
    subset = subset.filter(r => r.gainPerMcap != null);
    subset.sort((a, b) => b.gainPerMcap - a.gainPerMcap);
    modeVal = r => r.gainPerMcap;
    fmtFn = fmtGainMcap;
  } else if (state.rankMode === 'IMPLIED_CAP_GAIN') {
    subset = subset.filter(r => r.impliedCapGainUsd != null);
    subset.sort((a, b) => b.impliedCapGainUsd - a.impliedCapGainUsd);
    modeVal = r => r.impliedCapGainUsd;
    fmtFn = fmtSignedUsd;
  }

  document.getElementById('leaderboardSub').textContent = state.rankMode === 'GAIN_PER_MCAP'
    ? `Showing ${subset.length} tokens with known Market Cap (Period Return % / MCap $M)`
    : state.rankMode === 'IMPLIED_CAP_GAIN'
    ? `Showing ${subset.length} tokens by estimated USD Cap Gain (${state.startDate} → ${state.endDate})`
    : `Showing all ${subset.length} filtered tokens (scroll to browse)`;
  if (!subset.length) {
    container.innerHTML = '<div class="text-xs text-[var(--muted-foreground)] py-8 text-center">No tokens match filters</div>';
    return;
  }

  const maxAbs = Math.max(0.001, ...subset.map(r => Math.abs(modeVal(r))));

  container.innerHTML = subset.map((r, idx) => {
    const v = modeVal(r);
    const pct = Math.min(100, Math.max(2, (Math.abs(v) / maxAbs) * 100));
    const isSel = r.symbol === state.selectedSymbol;
    const barColor = v < 0 ? 'bg-rose-500'
      : state.rankMode === 'LOWEST_CORR' ? 'bg-amber-500'
      : state.rankMode === 'GAIN_PER_MCAP' ? 'bg-violet-500'
      : state.rankMode === 'IMPLIED_CAP_GAIN' ? 'bg-cyan-500'
      : 'bg-emerald-500';
    const rowBg = isSel ? 'bg-blue-500/20 border-blue-500/40' : 'hover:bg-[var(--secondary)]/50 border-transparent';
    const valColor = v < 0 ? 'text-rose-400' : 'text-[var(--foreground)]';
    const subTag = (state.rankMode === 'GAIN_PER_MCAP' || state.rankMode === 'IMPLIED_CAP_GAIN')
      ? `<span class="w-28 text-right text-[11px] text-[var(--muted-foreground)] shrink-0">${fmtPct(r.periodReturnPct)} / ${fmtMcap(r.marketCap)}</span>`
      : '';

    return `<div data-symbol="${r.symbol}" class="flex items-center gap-2 px-2 py-1 rounded border ${rowBg} cursor-pointer text-xs">
      <span class="w-9 text-right text-[var(--muted-foreground)] shrink-0">#${idx + 1}</span>
      <span class="w-20 font-semibold truncate ${isSel ? 'text-blue-400' : 'text-[var(--foreground)]'} shrink-0" title="${r.name}">${r.symbol}</span>
      <div class="flex-1 h-3.5 bg-[var(--background)] rounded overflow-hidden">
        <div class="${barColor} h-full rounded" style="width:${pct.toFixed(1)}%"></div>
      </div>
      ${subTag}
      <span class="w-24 text-right font-medium ${valColor} shrink-0">${fmtFn(v)}</span>
    </div>`;
  }).join('');

  container.querySelectorAll('[data-symbol]').forEach(el => {
    el.onclick = () => {
      const sym = el.getAttribute('data-symbol');
      state.selectedSymbol = sym;
      document.getElementById('tokenSelect').value = sym;
      renderBarChart(getFilteredAlts());
      renderTable(getFilteredAlts());
      renderDeepDive();
    };
  });
}

function renderTable(alts) {
  const k = state.sortKey;
  const sorted = [...alts].sort((a, b) => {
    const va = a[k], vb = b[k];
    if (typeof va === 'string') return state.sortDesc ? vb.localeCompare(va) : va.localeCompare(vb);
    if (k === 'mcapRank') return state.sortDesc ? (va - vb) : (vb - va);
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    return state.sortDesc ? (vb - va) : (va - vb);
  });

  const totalPages = Math.max(1, Math.ceil(sorted.length / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;
  const start = (state.page - 1) * state.pageSize;
  const pageRows = sorted.slice(start, start + state.pageSize);
  const displayRows = (state.page === 1 && state.btcRow) ? [state.btcRow, ...pageRows] : pageRows;

  document.getElementById('pageInfo').textContent = `Page ${state.page} / ${totalPages} (${sorted.length} alts)`;

  const tbody = document.getElementById('metricsTableBody');
  tbody.innerHTML = displayRows.map(r => {
    const isBtc = r.symbol === 'BTC';
    const isSel = r.symbol === state.selectedSymbol;
    const rowCls = isBtc
      ? 'bg-[var(--secondary)]/60 font-semibold'
      : (isSel ? 'bg-blue-500/15 cursor-pointer' : 'hover:bg-[var(--secondary)]/40 cursor-pointer');
    const retColor = r.periodReturnPct >= 0 ? 'text-emerald-500' : 'text-rose-500';
    const corrColor = (r.activeCorr ?? 0) >= 0.7 ? 'text-emerald-500 font-semibold'
      : (r.activeCorr ?? 0) >= 0.4 ? 'text-blue-400 font-semibold'
      : (r.activeCorr ?? 0) < 0 ? 'text-rose-500 font-semibold' : 'text-amber-500 font-semibold';
    const exBadges = [
      r.has_binance ? '<span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400">BN</span>' : '',
      r.has_bybit ? '<span class="px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-400">BB</span>' : '',
    ].join(' ');

    return `<tr class="${rowCls}" data-symbol="${r.symbol}">
      <td class="py-2 px-2 text-[var(--muted-foreground)]">${r.mcap_rank ? '#' + r.mcap_rank : '--'}</td>
      <td class="py-2 px-2"><span class="font-semibold text-[var(--foreground)]">${r.symbol}</span> <span class="text-[var(--muted-foreground)]">${r.name !== r.symbol ? r.name.slice(0, 16) : ''}</span></td>
      <td class="py-2 px-2">${exBadges}</td>
      <td class="py-2 px-2 text-right text-[var(--muted-foreground)]">${fmtMcap(r.marketCap)}</td>
      <td class="py-2 px-2 text-right">${r.nDays}d</td>
      <td class="py-2 px-2 text-right">${fmtPrice(r.endPrice)}</td>
      <td class="py-2 px-2 text-right ${retColor}">${fmtPct(r.periodReturnPct)}</td>
      <td class="py-2 px-2 text-right ${r.gainPerMcap != null && r.gainPerMcap > 0 ? 'text-violet-400 font-medium' : r.gainPerMcap != null ? 'text-rose-400' : 'text-[var(--muted-foreground)]'}">${fmtGainMcap(r.gainPerMcap)}</td>
      <td class="py-2 px-2 text-right ${r.impliedCapGainUsd != null && r.impliedCapGainUsd > 0 ? 'text-cyan-400 font-medium' : r.impliedCapGainUsd != null ? 'text-rose-400' : 'text-[var(--muted-foreground)]'}">${fmtSignedUsd(r.impliedCapGainUsd)}</td>
      <td class="py-2 px-2 text-right ${isBtc ? '' : corrColor}">${fmtCorr(r.activeCorr)}</td>
      <td class="py-2 px-2 text-right">${fmtCorr(r.spearmanLog)}</td>
      <td class="py-2 px-2 text-right">${r.beta != null ? r.beta.toFixed(2) : '--'}</td>
      <td class="py-2 px-2 text-right">${r.rSquared != null ? (r.rSquared * 100).toFixed(1) + '%' : '--'}</td>
      <td class="py-2 px-2 text-right">${fmtCorr(r.latestRoll30)}</td>
      <td class="py-2 px-2 text-right">${r.annVolPct.toFixed(1)}%</td>
      <td class="py-2 px-2 text-right text-rose-400">${r.mddPct.toFixed(1)}%</td>
    </tr>`;
  }).join('');

  tbody.querySelectorAll('tr[data-symbol]').forEach(tr => {
    tr.addEventListener('click', () => {
      const sym = tr.getAttribute('data-symbol');
      if (sym !== 'BTC') {
        state.selectedSymbol = sym;
        document.getElementById('tokenSelect').value = sym;
        renderBarChart(getFilteredAlts());
        renderTable(getFilteredAlts());
        renderDeepDive();
      }
    });
  });
}

function renderDeepDive() {
  const tok = state.computedRows.find(r => r.symbol === state.selectedSymbol) || state.computedRows.find(r => r.symbol !== 'BTC');
  if (!tok) return;

  document.getElementById('deepDiveTitle').textContent = `Token Deep-Dive: BTC vs ${tok.symbol} (${tok.name})`;
  document.getElementById('deepDiveSub').textContent =
    `${tok.exchanges.join(' · ')} | MCap=${fmtMcap(tok.marketCap)} | Gain/MCap=${fmtGainMcap(tok.gainPerMcap)} | CapGain=${fmtSignedUsd(tok.impliedCapGainUsd)} | ${tok.nDays}d (${tok.validDates[0]} → ${tok.validDates[tok.validDates.length - 1]}) | Pearson r=${fmtCorr(tok.pearsonLog)} | Beta=${tok.beta?.toFixed(2) ?? '--'} | Ret: ${fmtPct(tok.periodReturnPct)}`;
  document.getElementById('perfLegendToken').textContent = tok.symbol;
  document.getElementById('scatterStatsBadge').textContent = `β = ${tok.beta?.toFixed(2) ?? '--'} | R² = ${tok.rSquared != null ? (tok.rSquared * 100).toFixed(1) + '%' : '--'}`;

  // Rolling 14D / 30D
  const roll14 = [], roll30 = [];
  for (let i = 0; i < tok.retDates.length; i++) {
    roll14.push(i + 1 >= 14 ? pearson(tok.btcLog.slice(i + 1 - 14, i + 1), tok.tokLog.slice(i + 1 - 14, i + 1)) : null);
    roll30.push(i + 1 >= 30 ? pearson(tok.btcLog.slice(i + 1 - 30, i + 1), tok.tokLog.slice(i + 1 - 30, i + 1)) : null);
  }
  drawRollingChart(tok, roll14, roll30);
  drawPerfChart(tok);
  drawScatterChart(tok);
}

function drawRollingChart(tok, roll14, roll30) {
  const canvas = document.getElementById('rollingCanvas');
  const { ctx, w, h } = setupCanvas(canvas, 240);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const padL = 42, padR = 16, padT = 12, padB = 24;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const dates = tok.retDates, n = dates.length;
  const yMin = -0.6, yMax = 1.05;
  const xOf = i => padL + (i / Math.max(1, n - 1)) * plotW;
  const yOf = v => padT + ((yMax - v) / (yMax - yMin)) * plotH;

  ctx.font = '12px sans-serif';
  [-0.5, 0, 0.5, 1.0].forEach(t => {
    const y = yOf(t);
    ctx.strokeStyle = theme.border;
    ctx.lineWidth = t === 0 ? 1.4 : 0.6;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
    ctx.fillStyle = theme.muted; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(t.toFixed(1), padL - 6, y);
  });

  ctx.textBaseline = 'top';
  [{ i: 0, a: 'left' }, { i: Math.floor(n / 2), a: 'center' }, { i: n - 1, a: 'right' }].forEach(o => {
    if (dates[o.i]) { ctx.textAlign = o.a; ctx.fillText(dates[o.i].slice(5), xOf(o.i), padT + plotH + 6); }
  });

  function plot(arr, col, lw) {
    ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath();
    let st = false;
    arr.forEach((v, i) => {
      if (v == null) return;
      const x = xOf(i), y = yOf(Math.max(yMin, Math.min(yMax, v)));
      if (!st) { ctx.moveTo(x, y); st = true; } else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  plot(roll14, '#f59e0b', 1.5);
  plot(roll30, '#3b82f6', 2.3);

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const idx = Math.max(0, Math.min(n - 1, Math.round(((e.clientX - rect.left - padL) / plotW) * (n - 1))));
    document.getElementById('rollingHoverInfo').textContent = `${dates[idx]} | 30D: ${fmtCorr(roll30[idx])} | 14D: ${fmtCorr(roll14[idx])}`;
  };
}

function drawPerfChart(tok) {
  const canvas = document.getElementById('perfCanvas');
  const { ctx, w, h } = setupCanvas(canvas, 240);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const dates = tok.validDates, n = dates.length;
  const btcNorm = tok.btcP.map(p => (p / tok.btcP[0]) * 100);
  const tokNorm = tok.tokP.map(p => (p / tok.tokP[0]) * 100);
  const allV = [...btcNorm, ...tokNorm];
  const minV = Math.min(...allV) * 0.95, maxV = Math.max(...allV) * 1.05;

  const padL = 44, padR = 16, padT = 12, padB = 24;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const xOf = i => padL + (i / Math.max(1, n - 1)) * plotW;
  const yOf = v => padT + ((maxV - v) / Math.max(1e-6, maxV - minV)) * plotH;

  ctx.font = '12px sans-serif';
  for (let k = 0; k <= 4; k++) {
    const v = minV + (k / 4) * (maxV - minV), y = yOf(v);
    ctx.strokeStyle = theme.border; ctx.lineWidth = 0.6;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
    ctx.fillStyle = theme.muted; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(v.toFixed(0), padL - 6, y);
  }
  ctx.textBaseline = 'top';
  [{ i: 0, a: 'left' }, { i: Math.floor(n / 2), a: 'center' }, { i: n - 1, a: 'right' }].forEach(o => {
    if (dates[o.i]) { ctx.textAlign = o.a; ctx.fillText(dates[o.i].slice(5), xOf(o.i), padT + plotH + 6); }
  });

  function drawL(arr, col) {
    ctx.strokeStyle = col; ctx.lineWidth = 2.1; ctx.beginPath();
    arr.forEach((v, i) => { if (i === 0) ctx.moveTo(xOf(i), yOf(v)); else ctx.lineTo(xOf(i), yOf(v)); });
    ctx.stroke();
  }
  drawL(btcNorm, '#f97316');
  drawL(tokNorm, '#10b981');

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const idx = Math.max(0, Math.min(n - 1, Math.round(((e.clientX - rect.left - padL) / plotW) * (n - 1))));
    document.getElementById('perfHoverInfo').textContent = `${dates[idx]} | BTC: ${btcNorm[idx].toFixed(1)} | ${tok.symbol}: ${tokNorm[idx].toFixed(1)}`;
  };
}

function drawScatterChart(tok) {
  const canvas = document.getElementById('scatterCanvas');
  const { ctx, w, h } = setupCanvas(canvas, 240);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const xs = tok.btcLog.map(v => v * 100), ys = tok.tokLog.map(v => v * 100);
  const maxAbsX = Math.max(5, ...xs.map(Math.abs)) * 1.1;
  const maxAbsY = Math.max(8, ...ys.map(Math.abs)) * 1.1;
  const padL = 42, padR = 14, padT = 12, padB = 24;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const xOf = v => padL + ((v + maxAbsX) / (2 * maxAbsX)) * plotW;
  const yOf = v => padT + ((maxAbsY - v) / (2 * maxAbsY)) * plotH;

  ctx.strokeStyle = theme.border; ctx.lineWidth = 1.2;
  ctx.beginPath(); ctx.moveTo(xOf(0), padT); ctx.lineTo(xOf(0), padT + plotH); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(padL, yOf(0)); ctx.lineTo(padL + plotW, yOf(0)); ctx.stroke();

  ctx.font = '12px sans-serif'; ctx.fillStyle = theme.muted;
  ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
  ctx.fillText(`+${maxAbsY.toFixed(0)}%`, padL - 4, padT + 6);
  ctx.fillText(`-${maxAbsY.toFixed(0)}%`, padL - 4, padT + plotH - 6);
  ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  ctx.fillText(`-${maxAbsX.toFixed(0)}%`, padL + 14, padT + plotH + 6);
  ctx.fillText(`+${maxAbsX.toFixed(0)}%`, padL + plotW - 14, padT + plotH + 6);

  if (tok.beta != null && tok.alpha != null) {
    const x1 = -maxAbsX * 0.9, x2 = maxAbsX * 0.9;
    ctx.strokeStyle = '#f97316'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(xOf(x1), yOf(tok.alpha * 100 + tok.beta * x1)); ctx.lineTo(xOf(x2), yOf(tok.alpha * 100 + tok.beta * x2)); ctx.stroke();
  }
  ctx.fillStyle = 'rgba(59, 130, 246, 0.72)';
  for (let i = 0; i < xs.length; i++) {
    ctx.beginPath(); ctx.arc(xOf(xs[i]), yOf(ys[i]), 3, 0, Math.PI * 2); ctx.fill();
  }

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    let best = -1, bestD = 144;
    for (let i = 0; i < xs.length; i++) {
      const d = (xOf(xs[i]) - mx) ** 2 + (yOf(ys[i]) - my) ** 2;
      if (d < bestD) { bestD = d; best = i; }
    }
    if (best >= 0) {
      document.getElementById('scatterHoverInfo').textContent = `${tok.retDates[best]} | BTC: ${fmtPct(xs[best])} | ${tok.symbol}: ${fmtPct(ys[best])}`;
    }
  };
}

function renderAll() {
  const alts = getFilteredAlts();
  renderKPIs(alts);
  renderHistogram(alts);
  renderBarChart(alts);
  renderTable(alts);
  renderDeepDive();
}

function initUI() {
  const startInp = document.getElementById('startDateInput');
  const endInp = document.getElementById('endDateInput');
  startInp.min = RAW.start_date; startInp.max = RAW.end_date;
  endInp.min = RAW.start_date; endInp.max = RAW.end_date;
  startInp.value = state.startDate; endInp.value = state.endDate;

  const tokenSel = document.getElementById('tokenSelect');
  tokenMetaList.filter(t => t.symbol !== 'BTC').sort((a, b) => (a.mcap_rank ?? 999999) - (b.mcap_rank ?? 999999)).forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.symbol;
    opt.textContent = `${t.symbol}${t.mcap_rank ? ' (#' + t.mcap_rank + ')' : ''} — ${t.name}`;
    tokenSel.appendChild(opt);
  });
  tokenSel.value = state.selectedSymbol;

  startInp.onchange = () => { if (startInp.value < endInp.value) { state.startDate = startInp.value; state.page = 1; recomputeAll(); renderAll(); } };
  endInp.onchange = () => { if (endInp.value > startInp.value) { state.endDate = endInp.value; state.page = 1; recomputeAll(); renderAll(); } };
  document.getElementById('resetDateBtn').onclick = () => {
    state.startDate = RAW.start_date; state.endDate = RAW.end_date;
    startInp.value = state.startDate; endInp.value = state.endDate;
    state.page = 1; recomputeAll(); renderAll();
  };
  document.getElementById('metricSelect').onchange = e => { state.metric = e.target.value; recomputeAll(); renderAll(); };
  document.getElementById('searchInput').oninput = e => { state.search = e.target.value; state.page = 1; renderAll(); };
  document.getElementById('exchangeSelect').onchange = e => { state.exchange = e.target.value; state.page = 1; renderAll(); };
  document.getElementById('capSelect').onchange = e => { state.cap = e.target.value; state.page = 1; renderAll(); };
  document.getElementById('fullHistoryChk').onchange = e => { state.fullHistoryOnly = e.target.checked; state.page = 1; renderAll(); };
  document.getElementById('hideStableChk').onchange = e => { state.hideStable = e.target.checked; state.page = 1; renderAll(); };
  document.getElementById('rankModeSelect').onchange = e => { state.rankMode = e.target.value; renderBarChart(getFilteredAlts()); };
  tokenSel.onchange = e => { state.selectedSymbol = e.target.value; renderBarChart(getFilteredAlts()); renderTable(getFilteredAlts()); renderDeepDive(); };

  document.getElementById('prevPageBtn').onclick = () => { if (state.page > 1) { state.page--; renderTable(getFilteredAlts()); } };
  document.getElementById('nextPageBtn').onclick = () => { state.page++; renderTable(getFilteredAlts()); };
  document.getElementById('pageSizeSelect').onchange = e => { state.pageSize = Number(e.target.value); state.page = 1; renderTable(getFilteredAlts()); };

  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.onclick = () => {
      const k = th.getAttribute('data-sort');
      if (state.sortKey === k) state.sortDesc = !state.sortDesc;
      else { state.sortKey = k; state.sortDesc = k !== 'mcapRank'; }
      state.page = 1;
      renderTable(getFilteredAlts());
    };
  });

  window.onresize = () => renderAll();
}

recomputeAll();
initUI();
renderAll();
</script>
</body>
</html>
"""


def main():
    report = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    slim_tokens = [
        {
            "symbol": t["symbol"],
            "name": t["name"],
            "mcap_rank": t["mcap_rank"],
            "market_cap": t.get("market_cap"),
            "is_stable": t["is_stable"],
            "exchanges": t["exchanges"],
            "has_binance": t["has_binance"],
            "has_bybit": t["has_bybit"],
            "has_spot": t["has_spot"],
            "has_perp": t["has_perp"],
        }
        for t in report["tokens"]
    ]
    embed_payload = {
        "generated_at_utc": report["generated_at_utc"],
        "start_date": report["start_date"],
        "end_date": report["end_date"],
        "dates": report["dates"],
        "tokens": slim_tokens,
        "series": report["series"],
    }
    html = HTML_TEMPLATE.replace("__REPORT_JSON__", json.dumps(embed_payload, separators=(",", ":")))
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
    print(f"Built full CEX dashboard ({len(html):,} bytes) at:\n  - {ARTIFACT_PATH}\n  - {LOCAL_HTML_PATH}")


if __name__ == "__main__":
    main()
