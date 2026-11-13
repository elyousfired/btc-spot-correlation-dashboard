#!/usr/bin/env python3
"""
Builds Page 2: BTC +2% -> Token +10% Event Study & Win-Rate Screener (Spot Only)
from data/all_cex_correlation_report.json.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "all_cex_correlation_report.json"
ARTIFACT_PATH = Path(
    r"C:\Users\red1e\.gemini\antigravity\brain\fc84f6c8-80d9-40b0-aa9e-07bc551807d8\btc_spot_event_study.html"
)
LOCAL_HTML_PATH = BASE_DIR / "btc_event_study.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BTC +2% → Token +10% Win-Rate Screener (Spot)</title>
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
        <a href="btc_event_study.html" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)]">
          BTC +2% &rarr; Token +10% Event Study
        </a>
        <a href="btc_predictive_watchlist.html" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] text-[var(--muted-foreground)] border border-[var(--border)] hover:text-[var(--foreground)]">
          Next-Rally Predictive Watchlist
        </a>
      </div>
      <span id="navPeriodBadge" class="text-xs font-medium text-[var(--muted-foreground)] tabular-nums"></span>
    </nav>

    <!-- Header & Controls -->
    <header class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-4">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)]">SPOT ONLY &bull; Binance Spot + Bybit Spot</span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">Event-Study Backtest</span>
          </div>
          <h1 class="text-xl md:text-2xl font-bold tracking-tight text-[var(--foreground)]">When BTC Pumps &ge; +2%, Which Tokens Hit &ge; +10%?</h1>
          <p class="text-sm text-[var(--muted-foreground)] mt-1">Counts every BTC &ge; +X% day since July 1, 2026 and computes each Spot token&rsquo;s win rate (Wins / BTC Events), average move, and date-by-date hit log.</p>
        </div>

        <!-- Strategy Parameter Controls -->
        <div class="flex flex-wrap items-end gap-3">
          <div>
            <label for="btcThreshInput" class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">BTC Trigger (&ge; %)</label>
            <input id="btcThreshInput" type="number" step="0.5" min="0.5" max="20" value="2.0" class="px-3 py-1.5 rounded-lg text-sm bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] w-24 tabular-nums" />
          </div>
          <div>
            <label for="tokTargetInput" class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Token Target (&ge; %)</label>
            <input id="tokTargetInput" type="number" step="1" min="1" max="100" value="10.0" class="px-3 py-1.5 rounded-lg text-sm bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] w-24 tabular-nums" />
          </div>
          <div>
            <label for="windowSelect" class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Timing Window</label>
            <select id="windowSelect" class="px-3 py-1.5 rounded-lg text-sm bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]">
              <option value="cum_48h">Same Day or Next Day (t .. t+1)</option>
              <option value="after_48h">After BTC Close (Next 48h: t+1..t+2)</option>
              <option value="same_day">Same Day Only (Day t)</option>
              <option value="next_day">Next Day Only (Day t+1)</option>
            </select>
          </div>
          <div>
            <label for="startDateInput" class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Start Date</label>
            <input id="startDateInput" type="date" class="px-3 py-1.5 rounded-lg text-sm bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)]" />
          </div>
        </div>
      </div>

      <!-- Filter Bar -->
      <div class="pt-3 border-t border-[var(--border)] flex flex-wrap items-center gap-3">
        <input id="searchInput" type="text" placeholder="Search ticker or name..." class="px-3 py-1.5 rounded-lg text-xs bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] w-52" />
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
        <label class="flex items-center gap-1.5 text-xs text-[var(--foreground)] cursor-pointer select-none">
          <input id="fullHistoryChk" type="checkbox" checked class="rounded" />
          <span>Full Period Only (All BTC Events)</span>
        </label>
        <label class="flex items-center gap-1.5 text-xs text-[var(--foreground)] cursor-pointer select-none">
          <input id="hideStableChk" type="checkbox" checked class="rounded" />
          <span>Hide Stablecoins</span>
        </label>
        <label class="flex items-center gap-1.5 text-xs text-[var(--foreground)] cursor-pointer select-none">
          <input id="onlyWinnersChk" type="checkbox" checked class="rounded" />
          <span>Only Tokens With &ge; 1 Hit</span>
        </label>
        <button id="exportCsvBtn" class="ml-auto px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)] hover:opacity-90 cursor-pointer">
          Export List CSV
        </button>
      </div>
    </header>

    <!-- KPI Cards -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">BTC Trigger Days (&ge; Target %)</p>
        <div id="kpiEventCount" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiEventSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">#1 Highest Win Rate Token</p>
        <div id="kpiTopToken" class="mt-2 text-2xl font-bold tabular-nums text-emerald-400">--</div>
        <p id="kpiTopTokenSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Tokens Hitting Target (&ge; 1x)</p>
        <div id="kpiHitTokens" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiHitTokensSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
        <p class="text-xs font-medium text-[var(--muted-foreground)]">Spot Market Avg Move on Events</p>
        <div id="kpiAvgMove" class="mt-2 text-2xl font-bold tabular-nums text-[var(--foreground)]">--</div>
        <p id="kpiAvgMoveSub" class="text-xs text-[var(--muted-foreground)] mt-1">--</p>
      </div>
    </section>

    <!-- BTC Trigger Dates Strip -->
    <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
        <h2 class="text-sm font-semibold text-[var(--foreground)]">Detected BTC Trigger Days</h2>
        <span class="text-xs text-[var(--muted-foreground)]">Exact UTC dates where BTC daily close-to-close return &ge; threshold</span>
      </div>
      <div id="btcDatesList" class="flex flex-wrap gap-2 text-xs tabular-nums"></div>
    </section>

    <!-- Top 25 Bar Chart + Audit Drawer -->
    <section class="grid grid-cols-1 xl:grid-cols-12 gap-5">
      <div class="xl:col-span-6 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col">
        <div class="mb-3">
          <h2 class="text-base font-semibold text-[var(--foreground)]">Top 25 Tokens by Win Rate %</h2>
          <p class="text-xs text-[var(--muted-foreground)]">Click any bar to audit every BTC trigger day for that token</p>
        </div>
        <canvas id="winBarCanvas" class="w-full h-[540px] cursor-pointer"></canvas>
      </div>

      <!-- Event-by-Event Audit Panel -->
      <div class="xl:col-span-6 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm flex flex-col space-y-3">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
          <div>
            <h2 id="auditTitle" class="text-base font-semibold text-[var(--foreground)]">Event-by-Event Audit</h2>
            <p id="auditSub" class="text-xs text-[var(--muted-foreground)]">--</p>
          </div>
          <select id="auditTokenSelect" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] max-w-[200px]"></select>
        </div>
        <div class="overflow-x-auto flex-1">
          <table class="w-full text-left border-collapse text-xs tabular-nums">
            <thead>
              <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)]">
                <th class="py-2 px-2">BTC Event Date</th>
                <th class="py-2 px-2 text-right">BTC Move</th>
                <th class="py-2 px-2 text-right">Same Day (t)</th>
                <th class="py-2 px-2 text-right">Next Day (t+1)</th>
                <th class="py-2 px-2 text-right">Window Move</th>
                <th class="py-2 px-2 text-center">Result</th>
              </tr>
            </thead>
            <tbody id="auditTableBody" class="divide-y divide-[var(--border)]"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Full Ranked List Table -->
    <section class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 shadow-sm space-y-3">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 class="text-base font-semibold text-[var(--foreground)]">Complete Ranked Token List (Win Rate &amp; Hit Count)</h2>
          <p id="listSubtitle" class="text-xs text-[var(--muted-foreground)]">Click any row to inspect its exact date-by-date hits above</p>
        </div>
        <div class="flex items-center gap-2 text-xs">
          <button id="prevPageBtn" class="px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--background)] cursor-pointer">Prev</button>
          <span id="pageInfo" class="tabular-nums text-[var(--muted-foreground)]">Page 1</span>
          <button id="nextPageBtn" class="px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--background)] cursor-pointer">Next</button>
          <select id="pageSizeSelect" class="px-2 py-1 rounded border border-[var(--border)] bg-[var(--background)]">
            <option value="50">50 / page</option>
            <option value="100" selected>100 / page</option>
            <option value="1000">Show All</option>
          </select>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs tabular-nums">
          <thead>
            <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)]">
              <th class="py-2 px-2">#</th>
              <th class="py-2 px-2 cursor-pointer" data-sort="mcapRank">MCap</th>
              <th class="py-2 px-2 cursor-pointer" data-sort="symbol">Token</th>
              <th class="py-2 px-2">Spot</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="wins">Wins / Total</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="winRate">Win Rate %</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="sameDayRate">Same-Day %</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="after48Rate">Post-Close 48h %</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="avgMove">Avg Move</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="maxMove">Best Move</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="minMove">Worst Move</th>
              <th class="py-2 px-2 text-right cursor-pointer" data-sort="pearsonLog">BTC Corr (r)</th>
            </tr>
          </thead>
          <tbody id="listTableBody" class="divide-y divide-[var(--border)]"></tbody>
        </table>
      </div>
    </section>

    <footer class="text-xs text-[var(--muted-foreground)] flex flex-wrap items-center justify-between gap-2 pb-4">
      <span>Sources: Binance Spot + Bybit Spot + CoinGecko Top 1000 MCap &bull; Generated __GENERATED_AT__</span>
      <span>Note: Historical event-study backtest on UTC daily closes; not financial advice.</span>
    </footer>
  </div>

<script>
const RAW = __REPORT_JSON__;
const allDates = RAW.dates;
const seriesMap = RAW.series;
const tokenMetaList = RAW.tokens;

let state = {
  startDate: RAW.start_date,
  btcThresh: 2.0,
  tokTarget: 10.0,
  windowMode: 'cum_48h',
  search: '',
  exchange: 'ALL',
  cap: 'ALL',
  fullHistoryOnly: true,
  hideStable: true,
  onlyWinners: true,
  sortKey: 'winRate',
  sortDesc: true,
  page: 1,
  pageSize: 100,
  selectedSymbol: null,
  btcEvents: [],
  results: [],
  barHitBoxes: [],
};

function fmtPct(v) { return v == null ? '--' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%'; }

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
  const h = cssHeight || rect.height || 400;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w, h };
}

function evalTokenEvent(arr, idx, target) {
  // Returns { sameDay, nextDay, cum48, after48, activeRet } or null if missing
  if (idx < 1 || !arr[idx - 1] || !arr[idx]) return null;
  const sameDay = ((arr[idx] - arr[idx - 1]) / arr[idx - 1]) * 100;
  const hasNext = idx + 1 < allDates.length && arr[idx + 1] != null && arr[idx + 1] > 0;
  const hasDay2 = idx + 2 < allDates.length && arr[idx + 2] != null && arr[idx + 2] > 0;

  const nextDay = hasNext ? ((arr[idx + 1] - arr[idx]) / arr[idx]) * 100 : null;
  const cum48 = hasNext ? Math.max(sameDay, ((arr[idx + 1] - arr[idx - 1]) / arr[idx - 1]) * 100) : sameDay;
  let after48 = null;
  if (hasNext && hasDay2) {
    after48 = Math.max(nextDay, ((arr[idx + 2] - arr[idx]) / arr[idx]) * 100);
  } else if (hasNext) {
    after48 = nextDay;
  }
  return { sameDay, nextDay, cum48, after48 };
}

function recomputeStudy() {
  const btcArr = seriesMap['BTC'];
  const startIdx = Math.max(1, allDates.findIndex(d => d >= state.startDate));
  const btcEvents = [];
  for (let i = startIdx; i < allDates.length; i++) {
    if (!btcArr[i - 1] || !btcArr[i]) continue;
    const ret = ((btcArr[i] - btcArr[i - 1]) / btcArr[i - 1]) * 100;
    if (ret >= state.btcThresh) {
      btcEvents.push({ idx: i, date: allDates[i], btcRet: ret });
    }
  }
  state.btcEvents = btcEvents;
  document.getElementById('navPeriodBadge').textContent = `${allDates[startIdx - 1]} → ${allDates[allDates.length - 1]} (${allDates.length}d)`;

  const results = [];
  for (const meta of tokenMetaList) {
    if (meta.symbol === 'BTC') continue;
    const arr = seriesMap[meta.symbol];
    if (!arr) continue;

    let wins = 0, tot = 0;
    let sameWins = 0, sameTot = 0;
    let afterWins = 0, afterTot = 0;
    const moves = [];
    const auditLogs = [];

    for (const ev of btcEvents) {
      const m = evalTokenEvent(arr, ev.idx, state.tokTarget);
      if (!m) continue;

      let activeMove = null;
      if (state.windowMode === 'same_day') activeMove = m.sameDay;
      else if (state.windowMode === 'next_day') activeMove = m.nextDay;
      else if (state.windowMode === 'after_48h') activeMove = m.after48;
      else activeMove = m.cum48;

      if (m.sameDay != null) { sameTot++; if (m.sameDay >= state.tokTarget) sameWins++; }
      if (m.after48 != null) { afterTot++; if (m.after48 >= state.tokTarget) afterWins++; }

      if (activeMove != null) {
        tot++;
        moves.push(activeMove);
        const hit = activeMove >= state.tokTarget;
        if (hit) wins++;
        auditLogs.push({
          date: ev.date,
          btcRet: ev.btcRet,
          sameDay: m.sameDay,
          nextDay: m.nextDay,
          windowMove: activeMove,
          hit,
        });
      }
    }

    if (tot === 0) continue;
    const winRate = (wins / tot) * 100;
    const avgMove = moves.reduce((a, b) => a + b, 0) / moves.length;
    results.push({
      ...meta,
      mcapRank: meta.mcap_rank ?? 999999,
      wins,
      tot,
      winRate,
      sameDayRate: sameTot ? (sameWins / sameTot) * 100 : 0,
      after48Rate: afterTot ? (afterWins / afterTot) * 100 : 0,
      avgMove,
      maxMove: Math.max(...moves),
      minMove: Math.min(...moves),
      fullEvents: tot === btcEvents.length,
      auditLogs,
    });
  }

  state.results = results;
}

function getFiltered() {
  const q = state.search.trim().toLowerCase();
  return state.results.filter(r => {
    if (state.hideStable && r.is_stable) return false;
    if (state.fullHistoryOnly && !r.fullEvents) return false;
    if (state.onlyWinners && r.wins === 0) return false;
    if (state.exchange === 'BINANCE' && !r.has_binance) return false;
    if (state.exchange === 'BYBIT' && !r.has_bybit) return false;
    if (state.exchange === 'BOTH' && !(r.has_binance && r.has_bybit)) return false;
    if (state.cap === 'TOP50' && !(r.mcap_rank && r.mcap_rank <= 50)) return false;
    if (state.cap === 'TOP100' && !(r.mcap_rank && r.mcap_rank <= 100)) return false;
    if (state.cap === 'TOP250' && !(r.mcap_rank && r.mcap_rank <= 250)) return false;
    if (q && !r.symbol.toLowerCase().includes(q) && !(r.name || '').toLowerCase().includes(q)) return false;
    return true;
  });
}

function sortRows(rows) {
  const k = state.sortKey;
  return [...rows].sort((a, b) => {
    if (k === 'winRate') {
      if (b.winRate !== a.winRate) return state.sortDesc ? b.winRate - a.winRate : a.winRate - b.winRate;
      if (b.wins !== a.wins) return state.sortDesc ? b.wins - a.wins : a.wins - b.wins;
      return state.sortDesc ? b.avgMove - a.avgMove : a.avgMove - b.avgMove;
    }
    const va = a[k], vb = b[k];
    if (typeof va === 'string') return state.sortDesc ? vb.localeCompare(va) : va.localeCompare(vb);
    if (k === 'mcapRank') return state.sortDesc ? (va - vb) : (vb - va);
    return state.sortDesc ? ((vb ?? -999) - (va ?? -999)) : ((va ?? 999) - (vb ?? 999));
  });
}

function renderKPIs(filtered) {
  const evs = state.btcEvents;
  const avgBtc = evs.length ? evs.reduce((s, e) => s + e.btcRet, 0) / evs.length : 0;
  document.getElementById('kpiEventCount').textContent = `${evs.length} Days`;
  document.getElementById('kpiEventSub').textContent = evs.length ? `Avg BTC jump on trigger days: ${fmtPct(avgBtc)}` : 'No days match threshold';

  const ranked = sortRows(filtered);
  if (ranked.length) {
    const top = [...filtered].sort((a, b) => (b.winRate - a.winRate) || (b.avgMove - a.avgMove))[0];
    document.getElementById('kpiTopToken').textContent = `${top.symbol} (${top.winRate.toFixed(1)}%)`;
    document.getElementById('kpiTopTokenSub').textContent = `${top.wins}/${top.tot} hits • Avg move: ${fmtPct(top.avgMove)}`;
  } else {
    document.getElementById('kpiTopToken').textContent = '--';
    document.getElementById('kpiTopTokenSub').textContent = 'No tokens match filters';
  }

  // Count across non-stable full-event universe
  const baseUniverse = state.results.filter(r => (!state.hideStable || !r.is_stable) && (!state.fullHistoryOnly || r.fullEvents));
  const withHit = baseUniverse.filter(r => r.wins >= 1).length;
  const above50 = baseUniverse.filter(r => r.winRate >= 50).length;
  document.getElementById('kpiHitTokens').textContent = `${withHit} / ${baseUniverse.length}`;
  document.getElementById('kpiHitTokensSub').textContent = `${above50} tokens have ≥ 50% win rate`;

  const meanMove = baseUniverse.length ? baseUniverse.reduce((s, r) => s + r.avgMove, 0) / baseUniverse.length : 0;
  document.getElementById('kpiAvgMove').textContent = fmtPct(meanMove);
  document.getElementById('kpiAvgMoveSub').textContent = `Mean Spot altcoin move across ${baseUniverse.length} tokens`;

  // BTC trigger date pills
  document.getElementById('btcDatesList').innerHTML = evs.map(e =>
    `<span class="px-2.5 py-1 rounded-lg bg-[var(--background)] border border-[var(--border)]">
      <span class="text-[var(--muted-foreground)]">${e.date}</span>
      <span class="font-semibold text-emerald-400 ml-1">${fmtPct(e.btcRet)}</span>
    </span>`
  ).join('');
}

function renderBarChart(filtered) {
  const canvas = document.getElementById('winBarCanvas');
  const h = 540;
  const { ctx, w } = setupCanvas(canvas, h);
  const theme = getThemeColors();
  ctx.clearRect(0, 0, w, h);

  const top25 = [...filtered]
    .sort((a, b) => (b.winRate - a.winRate) || (b.wins - a.wins) || (b.avgMove - a.avgMove))
    .slice(0, 25);

  if (!top25.length) return;
  if (!state.selectedSymbol || !filtered.some(r => r.symbol === state.selectedSymbol)) {
    state.selectedSymbol = top25[0].symbol;
  }

  const padL = 82, padR = 115, padT = 10, padB = 22;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const maxRate = Math.max(50, ...top25.map(r => r.winRate));
  const xOf = v => padL + (v / maxRate) * plotW;

  ctx.font = '12px sans-serif';
  [0, 25, 50, 75, 100].filter(t => t <= maxRate + 5).forEach(t => {
    const x = xOf(t);
    ctx.strokeStyle = theme.border; ctx.lineWidth = 0.6;
    ctx.beginPath(); ctx.moveTo(x, padT); ctx.lineTo(x, padT + plotH); ctx.stroke();
    ctx.fillStyle = theme.muted; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(t + '%', x, padT + plotH + 4);
  });

  state.barHitBoxes = [];
  const step = plotH / top25.length;
  const barH = Math.min(15, step * 0.68);

  top25.forEach((r, idx) => {
    const cy = padT + idx * step + step / 2;
    const bw = Math.max(3, xOf(r.winRate) - padL);
    const isSel = r.symbol === state.selectedSymbol;

    if (isSel) {
      ctx.fillStyle = theme.isLight ? 'rgba(59,130,246,0.12)' : 'rgba(59,130,246,0.20)';
      ctx.fillRect(4, cy - step / 2 + 1, w - 8, step - 2);
    }

    ctx.fillStyle = r.winRate >= 50 ? '#10b981' : r.winRate >= 30 ? '#3b82f6' : '#f59e0b';
    ctx.beginPath(); ctx.roundRect(padL, cy - barH / 2, bw, barH, 3); ctx.fill();

    ctx.fillStyle = isSel ? '#3b82f6' : theme.fg;
    ctx.font = (isSel ? 'bold ' : '') + '12px sans-serif';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(r.symbol, padL - 8, cy);

    ctx.fillStyle = theme.fg;
    ctx.textAlign = 'left';
    ctx.fillText(`${r.winRate.toFixed(1)}% (${r.wins}/${r.tot})`, padL + bw + 6, cy);

    state.barHitBoxes.push({ y1: cy - step / 2, y2: cy + step / 2, symbol: r.symbol });
  });
}

function renderAuditPanel() {
  const tok = state.results.find(r => r.symbol === state.selectedSymbol) || state.results[0];
  if (!tok) return;

  const sel = document.getElementById('auditTokenSelect');
  if (sel.value !== tok.symbol) sel.value = tok.symbol;

  document.getElementById('auditTitle').textContent = `Event Audit: ${tok.symbol} (${tok.name})`;
  document.getElementById('auditSub').textContent =
    `Success: ${tok.wins}/${tok.tot} (${tok.winRate.toFixed(1)}%) | Avg Move: ${fmtPct(tok.avgMove)} | Corr r=${tok.pearsonLog.toFixed(3)}`;

  document.getElementById('auditTableBody').innerHTML = tok.auditLogs.map(log => {
    const winCls = log.hit ? 'text-emerald-400 font-semibold' : 'text-[var(--foreground)]';
    const badge = log.hit
      ? '<span class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold">HIT &ge; ' + state.tokTarget + '%</span>'
      : '<span class="px-2 py-0.5 rounded-full bg-[var(--secondary)] text-[var(--muted-foreground)]">MISS</span>';
    return `<tr>
      <td class="py-1.5 px-2">${log.date}</td>
      <td class="py-1.5 px-2 text-right text-emerald-400">${fmtPct(log.btcRet)}</td>
      <td class="py-1.5 px-2 text-right">${fmtPct(log.sameDay)}</td>
      <td class="py-1.5 px-2 text-right">${fmtPct(log.nextDay)}</td>
      <td class="py-1.5 px-2 text-right ${winCls}">${fmtPct(log.windowMove)}</td>
      <td class="py-1.5 px-2 text-center">${badge}</td>
    </tr>`;
  }).join('');
}

function renderTable(filtered) {
  const sorted = sortRows(filtered);
  const totalPages = Math.max(1, Math.ceil(sorted.length / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;
  const start = (state.page - 1) * state.pageSize;
  const pageRows = sorted.slice(start, start + state.pageSize);

  document.getElementById('pageInfo').textContent = `Page ${state.page} / ${totalPages} (${sorted.length} tokens)`;
  document.getElementById('listSubtitle').textContent =
    `Showing ${sorted.length} Spot tokens ranked by Win Rate (Target ≥ +${state.tokTarget}% when BTC ≥ +${state.btcThresh}%)`;

  const tbody = document.getElementById('listTableBody');
  tbody.innerHTML = pageRows.map((r, i) => {
    const rankNum = start + i + 1;
    const isSel = r.symbol === state.selectedSymbol;
    const rowCls = isSel ? 'bg-blue-500/15 cursor-pointer' : 'hover:bg-[var(--secondary)]/40 cursor-pointer';
    const exBadges = [
      r.has_binance ? '<span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400">BN</span>' : '',
      r.has_bybit ? '<span class="px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-400">BB</span>' : '',
    ].join(' ');
    const rateColor = r.winRate >= 50 ? 'text-emerald-400 font-bold' : r.winRate >= 30 ? 'text-blue-400 font-semibold' : 'text-[var(--foreground)]';

    return `<tr class="${rowCls}" data-symbol="${r.symbol}">
      <td class="py-2 px-2 text-[var(--muted-foreground)]">${rankNum}</td>
      <td class="py-2 px-2 text-[var(--muted-foreground)]">${r.mcap_rank ? '#' + r.mcap_rank : '--'}</td>
      <td class="py-2 px-2"><span class="font-semibold text-[var(--foreground)]">${r.symbol}</span> <span class="text-[var(--muted-foreground)]">${r.name !== r.symbol ? r.name.slice(0, 15) : ''}</span></td>
      <td class="py-2 px-2">${exBadges}</td>
      <td class="py-2 px-2 text-right font-semibold">${r.wins} / ${r.tot}</td>
      <td class="py-2 px-2 text-right ${rateColor}">${r.winRate.toFixed(1)}%</td>
      <td class="py-2 px-2 text-right">${r.sameDayRate.toFixed(1)}%</td>
      <td class="py-2 px-2 text-right">${r.after48Rate.toFixed(1)}%</td>
      <td class="py-2 px-2 text-right ${r.avgMove >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${fmtPct(r.avgMove)}</td>
      <td class="py-2 px-2 text-right text-emerald-400">${fmtPct(r.maxMove)}</td>
      <td class="py-2 px-2 text-right text-rose-400">${fmtPct(r.minMove)}</td>
      <td class="py-2 px-2 text-right">${r.pearsonLog >= 0 ? '+' : ''}${r.pearsonLog.toFixed(3)}</td>
    </tr>`;
  }).join('');

  tbody.querySelectorAll('tr[data-symbol]').forEach(tr => {
    tr.onclick = () => {
      state.selectedSymbol = tr.getAttribute('data-symbol');
      const f = getFiltered();
      renderBarChart(f);
      renderTable(f);
      renderAuditPanel();
    };
  });
}

function populateAuditSelect(filtered) {
  const sel = document.getElementById('auditTokenSelect');
  const sorted = sortRows(filtered);
  sel.innerHTML = sorted.map(r => `<option value="${r.symbol}">${r.symbol} (${r.wins}/${r.tot} • ${r.winRate.toFixed(0)}%)</option>`).join('');
  if (state.selectedSymbol && sorted.some(r => r.symbol === state.selectedSymbol)) {
    sel.value = state.selectedSymbol;
  }
}

function renderAll() {
  const filtered = getFiltered();
  renderKPIs(filtered);
  renderBarChart(filtered);
  populateAuditSelect(filtered);
  renderAuditPanel();
  renderTable(filtered);
}

function exportCsv() {
  const sorted = sortRows(getFiltered());
  const header = ['Rank', 'MCap_Rank', 'Symbol', 'Name', 'Exchanges', 'Wins', 'Total_Events', 'Win_Rate_Pct', 'SameDay_WinRate_Pct', 'PostClose48h_WinRate_Pct', 'Avg_Move_Pct', 'Best_Move_Pct', 'Worst_Move_Pct', 'BTC_Pearson_r'];
  const lines = [header.join(',')];
  sorted.forEach((r, idx) => {
    lines.push([
      idx + 1,
      r.mcap_rank || '',
      r.symbol,
      `"${(r.name || '').replace(/"/g, '""')}"`,
      `"${r.exchanges.join(' ')}"`,
      r.wins,
      r.tot,
      r.winRate.toFixed(2),
      r.sameDayRate.toFixed(2),
      r.after48Rate.toFixed(2),
      r.avgMove.toFixed(2),
      r.maxMove.toFixed(2),
      r.minMove.toFixed(2),
      r.pearsonLog.toFixed(4),
    ].join(','));
  });
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `btc_${state.btcThresh}pct_token_${state.tokTarget}pct_${state.windowMode}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function initUI() {
  const startInp = document.getElementById('startDateInput');
  startInp.min = RAW.start_date; startInp.max = RAW.end_date; startInp.value = state.startDate;

  document.getElementById('btcThreshInput').onchange = e => {
    state.btcThresh = Math.max(0.1, Number(e.target.value) || 2.0);
    state.page = 1; recomputeStudy(); renderAll();
  };
  document.getElementById('tokTargetInput').onchange = e => {
    state.tokTarget = Math.max(0.5, Number(e.target.value) || 10.0);
    state.page = 1; recomputeStudy(); renderAll();
  };
  document.getElementById('windowSelect').onchange = e => {
    state.windowMode = e.target.value; state.page = 1; recomputeStudy(); renderAll();
  };
  startInp.onchange = () => {
    if (startInp.value) { state.startDate = startInp.value; state.page = 1; recomputeStudy(); renderAll(); }
  };
  document.getElementById('searchInput').oninput = e => { state.search = e.target.value; state.page = 1; renderAll(); };
  document.getElementById('exchangeSelect').onchange = e => { state.exchange = e.target.value; state.page = 1; renderAll(); };
  document.getElementById('capSelect').onchange = e => { state.cap = e.target.value; state.page = 1; renderAll(); };
  document.getElementById('fullHistoryChk').onchange = e => { state.fullHistoryOnly = e.target.checked; state.page = 1; renderAll(); };
  document.getElementById('hideStableChk').onchange = e => { state.hideStable = e.target.checked; state.page = 1; renderAll(); };
  document.getElementById('onlyWinnersChk').onchange = e => { state.onlyWinners = e.target.checked; state.page = 1; renderAll(); };
  document.getElementById('auditTokenSelect').onchange = e => {
    state.selectedSymbol = e.target.value;
    const f = getFiltered();
    renderBarChart(f); renderTable(f); renderAuditPanel();
  };
  document.getElementById('exportCsvBtn').onclick = exportCsv;

  document.getElementById('prevPageBtn').onclick = () => { if (state.page > 1) { state.page--; renderTable(getFiltered()); } };
  document.getElementById('nextPageBtn').onclick = () => { state.page++; renderTable(getFiltered()); };
  document.getElementById('pageSizeSelect').onchange = e => { state.pageSize = Number(e.target.value); state.page = 1; renderTable(getFiltered()); };

  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.onclick = () => {
      const k = th.getAttribute('data-sort');
      if (state.sortKey === k) state.sortDesc = !state.sortDesc;
      else { state.sortKey = k; state.sortDesc = k !== 'mcapRank'; }
      state.page = 1;
      renderTable(getFiltered());
    };
  });

  document.getElementById('winBarCanvas').onclick = e => {
    const rect = e.target.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hit = state.barHitBoxes.find(b => y >= b.y1 && y <= b.y2);
    if (hit) {
      state.selectedSymbol = hit.symbol;
      const f = getFiltered();
      renderBarChart(f); renderTable(f); renderAuditPanel();
    }
  };

  window.onresize = () => renderAll();
}

recomputeStudy();
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
            "is_stable": t["is_stable"],
            "exchanges": t["exchanges"],
            "has_binance": t["has_binance"],
            "has_bybit": t["has_bybit"],
            "pearsonLog": t["pearson_log"],
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
    print(f"Built BTC Event Study page ({len(html):,} bytes) at:\n  - {ARTIFACT_PATH}\n  - {LOCAL_HTML_PATH}")


if __name__ == "__main__":
    main()
