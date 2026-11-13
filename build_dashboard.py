#!/usr/bin/env python3
"""
Builds the self-contained interactive BTC-Token Correlation Dashboard HTML
from data/correlation_report.json (CoinGecko historical data).
Uses only allowlisted Tailwind CDN + semantic theme variables + native Canvas charts.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "correlation_report.json"
ARTIFACT_PATH = Path(
    r"C:\Users\red1e\.gemini\antigravity\brain\fc84f6c8-80d9-40b0-aa9e-07bc551807d8\btc_token_correlation_dashboard.html"
)
LOCAL_HTML_PATH = BASE_DIR / "dashboard.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BTC–Token Correlation Dashboard (CoinGecko)</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    canvas { display: block; width: 100%; }
    .tabular-nums { font-variant-numeric: tabular-nums; }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased p-4 md:p-6">
  <div class="max-w-7xl mx-auto space-y-5">

    <!-- Header -->
    <header class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
      <div>
        <div class="flex flex-wrap items-center gap-2 mb-1">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)]">CoinGecko Public API v3</span>
          <span id="periodBadge" class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--primary)] text-[var(--primary-foreground)]"></span>
        </div>
        <h1 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]">BTC – Token Correlation Quant Dashboard</h1>
        <p class="text-sm text-[var(--muted-foreground)] mt-1">Daily UTC price series aligned from July 1, 2026. Computes dynamic Pearson, Spearman, Beta (&beta;), R&sup2;, and rolling 14D/30D correlations.</p>
      </div>

      <!-- Global Controls -->
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
            <option value="priceLevel">Price-Level Pearson</option>
          </select>
        </div>
        <button id="resetDateBtn" class="px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] hover:opacity-90 cursor-pointer">Reset 01/07/2026</button>
      </div>
    </header>

    <!-- KPI Cards -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Most Correlated with BTC</p>
        <div id="kpiMaxCorr" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiMaxCorrSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Most Decoupled / Lowest Corr</p>
        <div id="kpiMinCorr" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiMinCorrSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Highest Beta (&beta;) vs BTC</p>
        <div id="kpiMaxBeta" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiMaxBetaSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">BTC Period Return & Avg Basket r</p>
        <div id="kpiBtcSummary" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiBtcSummarySub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
    </section>

    <!-- Ranking Chart + Table -->
    <section class="grid grid-cols-1 xl:grid-cols-12 gap-5">
      <!-- Bar Chart -->
      <div class="xl:col-span-5 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col">
        <div class="flex items-center justify-between gap-2 mb-3">
          <div>
            <h2 class="text-base font-semibold text-[var(--foreground)]">BTC–Token Correlation Ranking</h2>
            <p id="barSubtitle" class="text-xs text-[var(--muted-foreground)]">Click any bar or row to inspect token details</p>
          </div>
        </div>
        <div class="relative flex-1 min-h-[420px]">
          <canvas id="barCanvas" class="w-full h-[440px] cursor-pointer"></canvas>
        </div>
      </div>

      <!-- Data Table -->
      <div class="xl:col-span-7 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <div>
            <h2 class="text-base font-semibold text-[var(--foreground)]">Quantitative Metrics Matrix</h2>
            <p class="text-xs text-[var(--muted-foreground)]">Sorted by active metric; click column headers to sort</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <input id="searchInput" type="text" placeholder="Search symbol/name..." class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] w-40" />
            <select id="sectorSelect" class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
              <option value="ALL">All Sectors</option>
            </select>
          </div>
        </div>
        <div class="overflow-x-auto flex-1">
          <table class="w-full text-left border-collapse text-xs">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)]">
                <th class="py-2 px-2 font-semibold cursor-pointer" data-sort="symbol">Token</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="endPrice">Price (USD)</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="periodReturnPct">Return %</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="activeCorr">Corr (r)</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="spearmanLog">Spearman</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="beta">Beta (&beta;)</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="rSquared">R&sup2;</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="latestRoll30">30D Roll</th>
                <th class="py-2 px-2 font-semibold text-right cursor-pointer" data-sort="annVolPct">Vol (Ann.)</th>
              </tr>
            </thead>
            <tbody id="metricsTableBody" class="divide-y divide-[var(--border)] tabular-nums"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Token Deep-Dive Charts -->
    <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-4">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
        <div>
          <h2 id="deepDiveTitle" class="text-lg font-semibold text-[var(--foreground)]">Token Deep-Dive: BTC vs ETH</h2>
          <p id="deepDiveSub" class="text-xs text-[var(--muted-foreground)]">Inspect rolling correlation stability, indexed performance (Base 100), and daily return beta regression</p>
        </div>
        <div class="flex items-center gap-2">
          <label for="tokenSelect" class="text-xs font-medium text-[var(--muted-foreground)]">Inspect Token:</label>
          <select id="tokenSelect" class="px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]"></select>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <!-- Rolling Correlation -->
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold text-[var(--foreground)]">Rolling Correlation vs BTC</h3>
            <div class="flex items-center gap-3 text-xs text-[var(--muted-foreground)]">
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#3b82f6]"></span>30D</span>
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#f59e0b]"></span>14D</span>
            </div>
          </div>
          <canvas id="rollingCanvas" class="w-full h-[250px]"></canvas>
          <p id="rollingHoverInfo" class="text-xs text-[var(--muted-foreground)] mt-2 h-4 tabular-nums">Hover over chart to inspect daily rolling values</p>
        </div>

        <!-- Normalized Performance -->
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold text-[var(--foreground)]">Normalized Price (Base = 100)</h3>
            <div class="flex items-center gap-3 text-xs text-[var(--muted-foreground)]">
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#f97316]"></span>BTC</span>
              <span class="flex items-center gap-1"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#10b981]"></span><span id="perfLegendToken">Token</span></span>
            </div>
          </div>
          <canvas id="perfCanvas" class="w-full h-[250px]"></canvas>
          <p id="perfHoverInfo" class="text-xs text-[var(--muted-foreground)] mt-2 h-4 tabular-nums">Hover over chart to compare Base-100 performance</p>
        </div>

        <!-- Scatter Regression -->
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-semibold text-[var(--foreground)]">Daily Log Returns Scatter & OLS</h3>
            <span id="scatterStatsBadge" class="text-xs font-medium text-[var(--muted-foreground)] tabular-nums"></span>
          </div>
          <canvas id="scatterCanvas" class="w-full h-[250px]"></canvas>
          <p id="scatterHoverInfo" class="text-xs text-[var(--muted-foreground)] mt-2 h-4 tabular-nums">X: BTC Daily Return % | Y: Token Daily Return %</p>
        </div>
      </div>
    </section>

    <!-- Cross-Correlation Heatmap -->
    <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div>
          <h2 class="text-base font-semibold text-[var(--foreground)]">Cross-Asset Correlation Matrix (Daily Log Returns)</h2>
          <p class="text-xs text-[var(--muted-foreground)]">Pairwise Pearson correlation across BTC and all tracked tokens in the selected date window</p>
        </div>
        <span id="heatmapHoverInfo" class="text-xs font-medium text-[var(--muted-foreground)] tabular-nums">Hover cell for exact pairwise correlation</span>
      </div>
      <div class="overflow-x-auto">
        <canvas id="heatmapCanvas" class="w-full h-[430px]"></canvas>
      </div>
    </section>

    <footer class="text-xs text-[var(--muted-foreground)] flex flex-wrap items-center justify-between gap-2 pb-4">
      <span>Data Source: CoinGecko Public API v3 &bull; UTC Daily Close Alignment &bull; Generated __GENERATED_AT__</span>
      <span>Note: Quantitative correlation analysis for research purposes only.</span>
    </footer>
  </div>

<script>
const RAW_REPORT = __REPORT_JSON__;

// Helpers for math
function pearson(x, y) {
  const n = x.length;
  if (n < 3 || n !== y.length) return null;
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
  if (x.length < 3 || x.length !== y.length) return null;
  return pearson(avgRanks(x), avgRanks(y));
}

function calcBetaAlpha(tokR, btcR) {
  const n = tokR.length;
  if (n < 3) return { beta: null, alpha: null };
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
  const alpha = mt - beta * mb;
  return { beta, alpha };
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
  return '$' + p.toFixed(4);
}

function fmtPct(v) {
  if (v == null) return '--';
  return (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
}

function fmtCorr(v) {
  if (v == null) return '--';
  return (v >= 0 ? '+' : '') + v.toFixed(3);
}

function getThemeColors() {
  const cs = getComputedStyle(document.documentElement);
  const bodyCs = getComputedStyle(document.body);
  const fg = cs.getPropertyValue('--foreground').trim() || bodyCs.color || '#e2e8f0';
  const muted = cs.getPropertyValue('--muted-foreground').trim() || '#94a3b8';
  const border = cs.getPropertyValue('--border').trim() || '#334155';
  const card = cs.getPropertyValue('--card').trim() || '#1e293b';
  const bg = cs.getPropertyValue('--background').trim() || '#0f172a';
  const isLight = document.documentElement.classList.contains('light');
  return { fg, muted, border, card, bg, isLight };
}

function setupCanvas(canvas, cssHeight) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = Math.max(300, rect.width || canvas.parentElement.clientWidth || 500);
  const h = cssHeight || rect.height || 300;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
}

// App State
const allDates = RAW_REPORT.aligned_prices.dates;
const priceSeries = RAW_REPORT.aligned_prices.series;
const tokenMetaList = RAW_REPORT.tokens.map(t => ({
  id: t.id, symbol: t.symbol, name: t.name, sector: t.sector
}));

let state = {
  startDate: RAW_REPORT.start_date,
  endDate: RAW_REPORT.end_date,
  metric: 'pearsonLog',
  search: '',
  sector: 'ALL',
  sortKey: 'activeCorr',
  sortDesc: true,
  selectedTokenId: tokenMetaList.find(t => t.id === 'ethereum')?.id || tokenMetaList[1]?.id || 'bitcoin',
  computedRows: [],
  btcRow: null,
  barHitBoxes: [],
  heatmapData: null,
};

function recomputeForWindow() {
  const dates = [];
  const indices = [];
  for (let i = 0; i < allDates.length; i++) {
    if (allDates[i] >= state.startDate && allDates[i] <= state.endDate) {
      dates.push(allDates[i]);
      indices.push(i);
    }
  }
  if (dates.length < 5) return;

  const btcPricesFull = indices.map(i => priceSeries['bitcoin'][i]);
  const rows = [];

  for (const meta of tokenMetaList) {
    const rawArr = priceSeries[meta.id];
    if (!rawArr) continue;
    const validDates = [], tokP = [], btcP = [];
    for (let k = 0; k < indices.length; k++) {
      const val = rawArr[indices[k]];
      const bVal = btcPricesFull[k];
      if (val != null && bVal != null && val > 0 && bVal > 0) {
        validDates.push(dates[k]);
        tokP.push(val);
        btcP.push(bVal);
      }
    }
    if (tokP.length < 5) continue;

    const retDates = validDates.slice(1);
    const tokLog = [], btcLog = [], tokSimp = [], btcSimp = [];
    for (let i = 1; i < tokP.length; i++) {
      tokLog.push(Math.log(tokP[i] / tokP[i - 1]));
      btcLog.push(Math.log(btcP[i] / btcP[i - 1]));
      tokSimp.push((tokP[i] - tokP[i - 1]) / tokP[i - 1]);
      btcSimp.push((btcP[i] - btcP[i - 1]) / btcP[i - 1]);
    }

    const pearsonLog = pearson(btcLog, tokLog);
    const pearsonSimple = pearson(btcSimp, tokSimp);
    const spearmanLog = spearman(btcLog, tokLog);
    const priceLevel = pearson(btcP, tokP);
    const { beta, alpha } = calcBetaAlpha(tokLog, btcLog);
    const activeMap = { pearsonLog, pearsonSimple, spearmanLog, priceLevel };
    const activeCorr = activeMap[state.metric];
    const rSquared = activeCorr != null ? activeCorr * activeCorr : null;

    const roll14 = [], roll30 = [];
    for (let i = 0; i < retDates.length; i++) {
      roll14.push(i + 1 >= 14 ? pearson(btcLog.slice(i + 1 - 14, i + 1), tokLog.slice(i + 1 - 14, i + 1)) : null);
      roll30.push(i + 1 >= 30 ? pearson(btcLog.slice(i + 1 - 30, i + 1), tokLog.slice(i + 1 - 30, i + 1)) : null);
    }

    const meanR = tokLog.reduce((a, b) => a + b, 0) / tokLog.length;
    const varR = tokLog.reduce((a, b) => a + (b - meanR) ** 2, 0) / Math.max(1, tokLog.length - 1);
    const annVolPct = Math.sqrt(varR * 365) * 100;
    const periodReturnPct = ((tokP[tokP.length - 1] - tokP[0]) / tokP[0]) * 100;
    const mddPct = maxDrawdown(tokP) * 100;
    const latestRoll30 = [...roll30].reverse().find(v => v != null) ?? null;

    rows.push({
      ...meta,
      dates: validDates,
      retDates,
      prices: tokP,
      btcPrices: btcP,
      tokLog,
      btcLog,
      endPrice: tokP[tokP.length - 1],
      periodReturnPct,
      annVolPct,
      mddPct,
      pearsonLog,
      pearsonSimple,
      spearmanLog,
      priceLevel,
      activeCorr,
      beta,
      alpha,
      rSquared,
      roll14,
      roll30,
      latestRoll30,
    });
  }

  state.btcRow = rows.find(r => r.id === 'bitcoin');
  state.computedRows = rows;
  document.getElementById('periodBadge').textContent = `${dates[0]} → ${dates[dates.length - 1]} (${dates.length}d)`;
}

function getFilteredAltRows() {
  return state.computedRows
    .filter(r => r.id !== 'bitcoin')
    .filter(r => state.sector === 'ALL' || r.sector === state.sector)
    .filter(r => {
      if (!state.search) return true;
      const q = state.search.toLowerCase();
      return r.symbol.toLowerCase().includes(q) || r.name.toLowerCase().includes(q);
    });
}

function renderKPIs() {
  const alts = state.computedRows.filter(r => r.id !== 'bitcoin' && r.activeCorr != null);
  if (!alts.length) return;
  const sortedByCorr = [...alts].sort((a, b) => b.activeCorr - a.activeCorr);
  const maxC = sortedByCorr[0];
  const minC = sortedByCorr[sortedByCorr.length - 1];
  const sortedByBeta = [...alts].filter(r => r.beta != null).sort((a, b) => b.beta - a.beta);
  const maxB = sortedByBeta[0];
  const avgCorr = alts.reduce((s, r) => s + r.activeCorr, 0) / alts.length;

  document.getElementById('kpiMaxCorr').textContent = `${maxC.symbol} (${fmtCorr(maxC.activeCorr)})`;
  document.getElementById('kpiMaxCorrSub').textContent = `R² = ${(maxC.rSquared * 100).toFixed(1)}% variance explained by BTC`;

  document.getElementById('kpiMinCorr').textContent = `${minC.symbol} (${fmtCorr(minC.activeCorr)})`;
  document.getElementById('kpiMinCorrSub').textContent = `R² = ${(minC.rSquared * 100).toFixed(1)}% • 30D Roll: ${fmtCorr(minC.latestRoll30)}`;

  document.getElementById('kpiMaxBeta').textContent = `${maxB.symbol} (${maxB.beta.toFixed(2)}x)`;
  document.getElementById('kpiMaxBetaSub').textContent = `Ann. Vol: ${maxB.annVolPct.toFixed(1)}% • Return: ${fmtPct(maxB.periodReturnPct)}`;

  const btcRet = state.btcRow ? fmtPct(state.btcRow.periodReturnPct) : '--';
  document.getElementById('kpiBtcSummary').textContent = `BTC ${btcRet}`;
  document.getElementById('kpiBtcSummarySub').textContent = `Basket Avg Corr: ${fmtCorr(avgCorr)} across ${alts.length} tokens`;
}

function renderBarChart() {
  const canvas = document.getElementById('barCanvas');
  const rows = [...getFilteredAltRows()].sort((a, b) => (b.activeCorr ?? -9) - (a.activeCorr ?? -9));
  const h = Math.max(360, rows.length * 28 + 44);
  canvas.style.height = h + 'px';
  const { ctx, w } = setupCanvas(canvas, h);
  const theme = getThemeColors();

  ctx.clearRect(0, 0, w, h);
  const padL = 62, padR = 56, padT = 16, padB = 26;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const minVal = Math.min(-0.1, ...rows.map(r => r.activeCorr ?? 0));
  const maxVal = 1.0;
  const xOf = v => padL + ((v - minVal) / (maxVal - minVal)) * plotW;
  const zeroX = xOf(0);

  // Gridlines
  ctx.font = '12px sans-serif';
  ctx.textAlign = 'center';
  const ticks = [0, 0.25, 0.5, 0.75, 1.0];
  for (const t of ticks) {
    const x = xOf(t);
    ctx.strokeStyle = theme.border;
    ctx.lineWidth = t === 0 ? 1.5 : 0.7;
    ctx.beginPath();
    ctx.moveTo(x, padT);
    ctx.lineTo(x, padT + plotH);
    ctx.stroke();
    ctx.fillStyle = theme.muted;
    ctx.fillText(t.toFixed(2), x, h - 6);
  }

  state.barHitBoxes = [];
  const rowStep = plotH / Math.max(1, rows.length);
  const barH = Math.min(18, rowStep * 0.68);

  rows.forEach((r, idx) => {
    const cy = padT + idx * rowStep + rowStep / 2;
    const val = r.activeCorr ?? 0;
    const x0 = Math.min(zeroX, xOf(val));
    const bw = Math.max(2, Math.abs(xOf(val) - zeroX));
    const isSel = r.id === state.selectedTokenId;

    if (isSel) {
      ctx.fillStyle = theme.isLight ? 'rgba(59,130,246,0.12)' : 'rgba(59,130,246,0.18)';
      ctx.fillRect(4, cy - rowStep / 2 + 1, w - 8, rowStep - 2);
    }

    // Color by correlation strength
    let color = '#10b981';
    if (val < 0) color = '#ef4444';
    else if (val < 0.4) color = '#f59e0b';
    else if (val < 0.7) color = '#3b82f6';

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(x0, cy - barH / 2, bw, barH, 4);
    ctx.fill();

    // Symbol label left
    ctx.fillStyle = isSel ? '#3b82f6' : theme.fg;
    ctx.font = (isSel ? 'bold ' : '') + '12px sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(r.symbol, padL - 8, cy);

    // Value label right
    ctx.fillStyle = theme.fg;
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(fmtCorr(val), xOf(val) + 6, cy);

    state.barHitBoxes.push({ y1: cy - rowStep / 2, y2: cy + rowStep / 2, id: r.id });
  });
}

function renderTable() {
  const tbody = document.getElementById('metricsTableBody');
  const rows = [...getFilteredAltRows()];
  const k = state.sortKey;
  rows.sort((a, b) => {
    const va = a[k], vb = b[k];
    if (typeof va === 'string') return state.sortDesc ? vb.localeCompare(va) : va.localeCompare(vb);
    return state.sortDesc ? ((vb ?? -999) - (va ?? -999)) : ((va ?? 999) - (vb ?? 999));
  });

  // Always show BTC benchmark at top
  const displayRows = state.btcRow ? [state.btcRow, ...rows] : rows;

  tbody.innerHTML = displayRows.map(r => {
    const isBtc = r.id === 'bitcoin';
    const isSel = r.id === state.selectedTokenId;
    const rowCls = isBtc
      ? 'bg-[var(--secondary)]/50 font-semibold'
      : (isSel ? 'bg-blue-500/15 cursor-pointer' : 'hover:bg-[var(--secondary)]/40 cursor-pointer');
    const retColor = r.periodReturnPct >= 0 ? 'text-emerald-500' : 'text-rose-500';
    const corrBadgeColor = (r.activeCorr ?? 0) >= 0.7 ? 'text-emerald-500 font-semibold'
      : (r.activeCorr ?? 0) >= 0.4 ? 'text-blue-400 font-semibold'
      : 'text-amber-500 font-semibold';

    return `<tr class="${rowCls}" data-token-id="${r.id}">
      <td class="py-2 px-2">
        <div class="flex items-center gap-2">
          <span class="font-semibold text-[var(--foreground)]">${r.symbol}</span>
          <span class="text-[var(--muted-foreground)]">${isBtc ? 'Benchmark' : r.sector}</span>
        </div>
      </td>
      <td class="py-2 px-2 text-right">${fmtPrice(r.endPrice)}</td>
      <td class="py-2 px-2 text-right ${retColor}">${fmtPct(r.periodReturnPct)}</td>
      <td class="py-2 px-2 text-right ${isBtc ? '' : corrBadgeColor}">${fmtCorr(r.activeCorr)}</td>
      <td class="py-2 px-2 text-right">${fmtCorr(r.spearmanLog)}</td>
      <td class="py-2 px-2 text-right">${r.beta != null ? r.beta.toFixed(2) : '--'}</td>
      <td class="py-2 px-2 text-right">${r.rSquared != null ? (r.rSquared * 100).toFixed(1) + '%' : '--'}</td>
      <td class="py-2 px-2 text-right">${fmtCorr(r.latestRoll30)}</td>
      <td class="py-2 px-2 text-right">${r.annVolPct.toFixed(1)}%</td>
    </tr>`;
  }).join('');

  tbody.querySelectorAll('tr[data-token-id]').forEach(tr => {
    tr.addEventListener('click', () => {
      const id = tr.getAttribute('data-token-id');
      if (id !== 'bitcoin') {
        state.selectedTokenId = id;
        document.getElementById('tokenSelect').value = id;
        renderAllCharts();
      }
    });
  });
}

function renderDeepDive() {
  const tok = state.computedRows.find(r => r.id === state.selectedTokenId) || state.computedRows.find(r => r.id !== 'bitcoin');
  if (!tok) return;

  document.getElementById('deepDiveTitle').textContent = `Token Deep-Dive: BTC vs ${tok.name} (${tok.symbol})`;
  document.getElementById('deepDiveSub').textContent =
    `Pearson r = ${fmtCorr(tok.pearsonLog)} | Spearman = ${fmtCorr(tok.spearmanLog)} | Beta = ${tok.beta?.toFixed(2) ?? '--'} | Period Return: ${fmtPct(tok.periodReturnPct)} vs BTC ${fmtPct(state.btcRow?.periodReturnPct)}`;
  document.getElementById('perfLegendToken').textContent = tok.symbol;
  document.getElementById('scatterStatsBadge').textContent = `β = ${tok.beta?.toFixed(2) ?? '--'} | R² = ${tok.rSquared != null ? (tok.rSquared * 100).toFixed(1) + '%' : '--'}`;

  drawRollingChart(tok);
  drawPerfChart(tok);
  drawScatterChart(tok);
}

function drawRollingChart(tok) {
  const canvas = document.getElementById('rollingCanvas');
  const { ctx, w, h } = setupCanvas(canvas, 250);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const padL = 42, padR = 16, padT = 14, padB = 24;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const dates = tok.retDates;
  const n = dates.length;

  const yMin = -0.5, yMax = 1.05;
  const xOf = i => padL + (i / Math.max(1, n - 1)) * plotW;
  const yOf = v => padT + ((yMax - v) / (yMax - yMin)) * plotH;

  ctx.font = '12px sans-serif';
  [-0.25, 0, 0.25, 0.5, 0.75, 1.0].forEach(t => {
    const y = yOf(t);
    ctx.strokeStyle = theme.border;
    ctx.lineWidth = t === 0 ? 1.4 : 0.6;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
    ctx.fillStyle = theme.muted;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(t.toFixed(2), padL - 6, y);
  });

  // X date labels
  ctx.textBaseline = 'top';
  [
    { idx: 0, align: 'left' },
    { idx: Math.floor(n / 2), align: 'center' },
    { idx: n - 1, align: 'right' }
  ].forEach(item => {
    if (dates[item.idx]) {
      ctx.textAlign = item.align;
      ctx.fillText(dates[item.idx].slice(5), xOf(item.idx), padT + plotH + 6);
    }
  });

  function plotSeries(arr, color, width) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    let started = false;
    arr.forEach((v, i) => {
      if (v == null) return;
      const x = xOf(i), y = yOf(Math.max(yMin, Math.min(yMax, v)));
      if (!started) { ctx.moveTo(x, y); started = true; }
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  plotSeries(tok.roll14, '#f59e0b', 1.6);
  plotSeries(tok.roll30, '#3b82f6', 2.4);

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const idx = Math.max(0, Math.min(n - 1, Math.round(((mx - padL) / plotW) * (n - 1))));
    const r14 = tok.roll14[idx], r30 = tok.roll30[idx];
    document.getElementById('rollingHoverInfo').textContent =
      `${dates[idx]} | 30D Corr: ${fmtCorr(r30)} | 14D Corr: ${fmtCorr(r14)}`;
  };
}

function drawPerfChart(tok) {
  const canvas = document.getElementById('perfCanvas');
  const { ctx, w, h } = setupCanvas(canvas, 250);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const dates = tok.dates;
  const btcNorm = tok.btcPrices.map(p => (p / tok.btcPrices[0]) * 100);
  const tokNorm = tok.prices.map(p => (p / tok.prices[0]) * 100);
  const allV = [...btcNorm, ...tokNorm];
  const minV = Math.min(...allV) * 0.96;
  const maxV = Math.max(...allV) * 1.04;

  const padL = 44, padR = 16, padT = 14, padB = 24;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const n = dates.length;
  const xOf = i => padL + (i / Math.max(1, n - 1)) * plotW;
  const yOf = v => padT + ((maxV - v) / Math.max(1e-6, maxV - minV)) * plotH;

  ctx.font = '12px sans-serif';
  for (let k = 0; k <= 4; k++) {
    const v = minV + (k / 4) * (maxV - minV);
    const y = yOf(v);
    ctx.strokeStyle = theme.border;
    ctx.lineWidth = 0.6;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
    ctx.fillStyle = theme.muted;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(v.toFixed(0), padL - 6, y);
  }

  // Base 100 line
  if (100 >= minV && 100 <= maxV) {
    ctx.strokeStyle = theme.muted;
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(padL, yOf(100)); ctx.lineTo(padL + plotW, yOf(100)); ctx.stroke();
    ctx.setLineDash([]);
  }

  ctx.textBaseline = 'top';
  [
    { idx: 0, align: 'left' },
    { idx: Math.floor(n / 2), align: 'center' },
    { idx: n - 1, align: 'right' }
  ].forEach(item => {
    if (dates[item.idx]) {
      ctx.textAlign = item.align;
      ctx.fillText(dates[item.idx].slice(5), xOf(item.idx), padT + plotH + 6);
    }
  });

  function drawLine(arr, color) {
    ctx.strokeStyle = color; ctx.lineWidth = 2.2;
    ctx.beginPath();
    arr.forEach((v, i) => {
      const x = xOf(i), y = yOf(v);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  drawLine(btcNorm, '#f97316');
  drawLine(tokNorm, '#10b981');

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const idx = Math.max(0, Math.min(n - 1, Math.round(((mx - padL) / plotW) * (n - 1))));
    document.getElementById('perfHoverInfo').textContent =
      `${dates[idx]} | BTC: ${btcNorm[idx].toFixed(1)} | ${tok.symbol}: ${tokNorm[idx].toFixed(1)}`;
  };
}

function drawScatterChart(tok) {
  const canvas = document.getElementById('scatterCanvas');
  const { ctx, w, h } = setupCanvas(canvas, 250);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const xs = tok.btcLog.map(v => v * 100);
  const ys = tok.tokLog.map(v => v * 100);
  const maxAbsX = Math.max(5, ...xs.map(Math.abs)) * 1.1;
  const maxAbsY = Math.max(8, ...ys.map(Math.abs)) * 1.1;

  const padL = 42, padR = 12, padT = 14, padB = 24;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const xOf = v => padL + ((v + maxAbsX) / (2 * maxAbsX)) * plotW;
  const yOf = v => padT + ((maxAbsY - v) / (2 * maxAbsY)) * plotH;

  // Axes
  ctx.strokeStyle = theme.border;
  ctx.lineWidth = 1.2;
  ctx.beginPath(); ctx.moveTo(xOf(0), padT); ctx.lineTo(xOf(0), padT + plotH); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(padL, yOf(0)); ctx.lineTo(padL + plotW, yOf(0)); ctx.stroke();

  ctx.font = '12px sans-serif';
  ctx.fillStyle = theme.muted;
  ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
  ctx.fillText(`+${maxAbsY.toFixed(0)}%`, padL - 4, padT + 6);
  ctx.fillText(`-${maxAbsY.toFixed(0)}%`, padL - 4, padT + plotH - 6);
  ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  ctx.fillText(`-${maxAbsX.toFixed(0)}%`, padL + 14, padT + plotH + 6);
  ctx.fillText(`+${maxAbsX.toFixed(0)}%`, padL + plotW - 14, padT + plotH + 6);

  // OLS Regression line
  if (tok.beta != null && tok.alpha != null) {
    const x1 = -maxAbsX * 0.9, x2 = maxAbsX * 0.9;
    const y1 = tok.alpha * 100 + tok.beta * x1;
    const y2 = tok.alpha * 100 + tok.beta * x2;
    ctx.strokeStyle = '#f97316';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(xOf(x1), yOf(y1)); ctx.lineTo(xOf(x2), yOf(y2)); ctx.stroke();
  }

  // Points
  ctx.fillStyle = 'rgba(59, 130, 246, 0.72)';
  for (let i = 0; i < xs.length; i++) {
    ctx.beginPath();
    ctx.arc(xOf(xs[i]), yOf(ys[i]), 3.2, 0, Math.PI * 2);
    ctx.fill();
  }

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    let best = -1, bestD = 144;
    for (let i = 0; i < xs.length; i++) {
      const dx = xOf(xs[i]) - mx, dy = yOf(ys[i]) - my;
      const d = dx * dx + dy * dy;
      if (d < bestD) { bestD = d; best = i; }
    }
    if (best >= 0) {
      document.getElementById('scatterHoverInfo').textContent =
        `${tok.retDates[best]} | BTC: ${fmtPct(xs[best])} | ${tok.symbol}: ${fmtPct(ys[best])}`;
    }
  };
}

function renderHeatmap() {
  const canvas = document.getElementById('heatmapCanvas');
  const rows = state.computedRows.slice(0, 12); // Top 12 for crisp readability
  const m = rows.length;
  const h = 430;
  const { ctx, w } = setupCanvas(canvas, h);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const padL = 62, padT = 34, padR = 16, padB = 14;
  const cellW = (w - padL - padR) / m;
  const cellH = (h - padT - padB) / m;

  // Compute pairwise matrix on aligned dates
  const matrix = Array.from({ length: m }, () => Array(m).fill(1));
  for (let i = 0; i < m; i++) {
    for (let j = i + 1; j < m; j++) {
      const c = pearson(rows[i].tokLog, rows[j].tokLog) ?? 0;
      matrix[i][j] = c;
      matrix[j][i] = c;
    }
  }

  ctx.font = '12px sans-serif';
  for (let i = 0; i < m; i++) {
    // Top label
    ctx.fillStyle = theme.fg;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillText(rows[i].symbol, padL + i * cellW + cellW / 2, padT - 6);

    // Left label
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(rows[i].symbol, padL - 8, padT + i * cellH + cellH / 2);

    for (let j = 0; j < m; j++) {
      const v = matrix[i][j];
      const x = padL + j * cellW;
      const y = padT + i * cellH;
      // Color scale: -1 red, 0 slate, +1 emerald
      let bg;
      if (v >= 0) {
        const alpha = 0.15 + 0.75 * Math.min(1, v);
        bg = `rgba(16, 185, 129, ${alpha.toFixed(2)})`;
      } else {
        const alpha = 0.15 + 0.75 * Math.min(1, -v);
        bg = `rgba(239, 68, 68, ${alpha.toFixed(2)})`;
      }
      ctx.fillStyle = bg;
      ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);

      if (cellW >= 42) {
        ctx.fillStyle = v > 0.55 ? '#ffffff' : theme.fg;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(v.toFixed(2), x + cellW / 2, y + cellH / 2);
      }
    }
  }

  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const j = Math.floor((mx - padL) / cellW);
    const i = Math.floor((my - padT) / cellH);
    if (i >= 0 && i < m && j >= 0 && j < m) {
      document.getElementById('heatmapHoverInfo').textContent =
        `${rows[i].symbol} vs ${rows[j].symbol}: Pearson r = ${fmtCorr(matrix[i][j])}`;
    }
  };
}

function renderAllCharts() {
  renderKPIs();
  renderBarChart();
  renderTable();
  renderDeepDive();
  renderHeatmap();
}

function initControls() {
  const startInp = document.getElementById('startDateInput');
  const endInp = document.getElementById('endDateInput');
  startInp.min = RAW_REPORT.start_date;
  startInp.max = RAW_REPORT.end_date;
  endInp.min = RAW_REPORT.start_date;
  endInp.max = RAW_REPORT.end_date;
  startInp.value = state.startDate;
  endInp.value = state.endDate;

  const sectors = [...new Set(tokenMetaList.filter(t => t.id !== 'bitcoin').map(t => t.sector))].sort();
  const sectorSel = document.getElementById('sectorSelect');
  sectors.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s; opt.textContent = s;
    sectorSel.appendChild(opt);
  });

  const tokenSel = document.getElementById('tokenSelect');
  tokenMetaList.filter(t => t.id !== 'bitcoin').forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id; opt.textContent = `${t.symbol} — ${t.name}`;
    tokenSel.appendChild(opt);
  });
  tokenSel.value = state.selectedTokenId;

  startInp.addEventListener('change', () => {
    if (startInp.value && startInp.value < endInp.value) {
      state.startDate = startInp.value;
      recomputeForWindow();
      renderAllCharts();
    }
  });
  endInp.addEventListener('change', () => {
    if (endInp.value && endInp.value > startInp.value) {
      state.endDate = endInp.value;
      recomputeForWindow();
      renderAllCharts();
    }
  });
  document.getElementById('resetDateBtn').addEventListener('click', () => {
    state.startDate = RAW_REPORT.start_date;
    state.endDate = RAW_REPORT.end_date;
    startInp.value = state.startDate;
    endInp.value = state.endDate;
    recomputeForWindow();
    renderAllCharts();
  });
  document.getElementById('metricSelect').addEventListener('change', e => {
    state.metric = e.target.value;
    recomputeForWindow();
    renderAllCharts();
  });
  document.getElementById('searchInput').addEventListener('input', e => {
    state.search = e.target.value;
    renderBarChart();
    renderTable();
  });
  sectorSel.addEventListener('change', e => {
    state.sector = e.target.value;
    renderBarChart();
    renderTable();
  });
  tokenSel.addEventListener('change', e => {
    state.selectedTokenId = e.target.value;
    renderBarChart();
    renderTable();
    renderDeepDive();
  });

  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.getAttribute('data-sort');
      if (state.sortKey === k) state.sortDesc = !state.sortDesc;
      else { state.sortKey = k; state.sortDesc = true; }
      renderTable();
    });
  });

  document.getElementById('barCanvas').addEventListener('click', e => {
    const rect = e.target.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hit = state.barHitBoxes.find(b => y >= b.y1 && y <= b.y2);
    if (hit) {
      state.selectedTokenId = hit.id;
      tokenSel.value = hit.id;
      renderBarChart();
      renderTable();
      renderDeepDive();
    }
  });

  window.addEventListener('resize', () => renderAllCharts());
}

recomputeForWindow();
initControls();
renderAllCharts();
</script>
</body>
</html>
"""


def main():
    report = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    # Strip redundant per-token large arrays before embedding since aligned_prices has full series
    slim_tokens = [
        {
            "id": t["id"],
            "symbol": t["symbol"],
            "name": t["name"],
            "sector": t["sector"],
        }
        for t in report["tokens"]
    ]
    embed_payload = {
        "generated_at_utc": report["generated_at_utc"],
        "source": report["source"],
        "start_date": report["start_date"],
        "end_date": report["end_date"],
        "total_days": report["total_days"],
        "tokens": slim_tokens,
        "aligned_prices": report["aligned_prices"],
    }
    html = HTML_TEMPLATE.replace("__REPORT_JSON__", json.dumps(embed_payload))
    html = html.replace("__GENERATED_AT__", report["generated_at_utc"])

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(html, encoding="utf-8")

    # Standalone browser copy gets clean dark theme variables when opened outside Antigravity iframe
    standalone_vars = (
        "<style>:root{--background:#0b0f17;--card:#131a26;--foreground:#e5e7eb;"
        "--muted-foreground:#9ca3af;--border:#243044;--primary:#3b82f6;"
        "--primary-foreground:#ffffff;--secondary:#1e293b;--secondary-foreground:#e2e8f0;}</style>"
    )
    local_html = html.replace("</head>", f"  {standalone_vars}\n</head>")
    LOCAL_HTML_PATH.write_text(local_html, encoding="utf-8")
    print(f"Built dashboard at:\n  - {ARTIFACT_PATH}\n  - {LOCAL_HTML_PATH}")


if __name__ == "__main__":
    main()
