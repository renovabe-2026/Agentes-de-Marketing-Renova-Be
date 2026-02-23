/* ── Renova Be Marketing Dashboard — Frontend ──────────────────────────── */
"use strict";

// ── Config ──────────────────────────────────────────────────────────────────
const AUTO_REFRESH_MS = 5 * 60 * 1000; // 5 minutos
const CHART_COLORS = {
  fb:     { border: '#1877f2', bg: 'rgba(24,119,242,.15)' },
  gg:     { border: '#ea4335', bg: 'rgba(234,67,53,.15)' },
  sh:     { border: '#96bf48', bg: 'rgba(150,191,72,.15)' },
  spend:  { border: '#f59e0b', bg: 'rgba(245,158,11,.15)' },
  rev:    { border: '#22c55e', bg: 'rgba(34,197,94,.15)' },
  sess:   { border: '#14b8a6', bg: 'rgba(20,184,166,.15)' },
};

// ── State ───────────────────────────────────────────────────────────────────
let currentSection = 'overview';
let currentDays    = 7;
let customDateFrom = null;
let customDateTo   = null;
let refreshTimer   = null;

// Chart instances (to destroy before re-creating)
const charts = {};

// ── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initDateControls();
  loadSection('overview');
  scheduleAutoRefresh();
});

// ── Navigation ───────────────────────────────────────────────────────────────
function initNav() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const section = link.dataset.section;
      switchSection(section);
    });
  });
}

function switchSection(name) {
  currentSection = name;

  // Update sidebar active state
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.querySelector(`.nav-link[data-section="${name}"]`)?.classList.add('active');

  // Show correct section
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById(`section-${name}`)?.classList.add('active');

  // Update title
  const titles = {
    overview: 'Visão Geral',
    facebook: 'Facebook Ads',
    google:   'Google Ads',
    ga4:      'GA4',
    shopify:  'Shopify',
  };
  document.getElementById('section-title').textContent = titles[name] || name;

  loadSection(name);
}

// ── Date Controls ────────────────────────────────────────────────────────────
function initDateControls() {
  // Preset buttons
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentDays    = parseInt(btn.dataset.days);
      customDateFrom = null;
      customDateTo   = null;
      loadSection(currentSection);
    });
  });

  // Custom date range
  document.getElementById('apply-dates').addEventListener('click', () => {
    const from = document.getElementById('date-from').value;
    const to   = document.getElementById('date-to').value;
    if (from && to && from <= to) {
      customDateFrom = from;
      customDateTo   = to;
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      loadSection(currentSection);
    }
  });

  // Manual refresh button
  document.getElementById('refresh-btn').addEventListener('click', () => {
    loadSection(currentSection);
  });
}

function getQueryParams() {
  if (customDateFrom && customDateTo) {
    return `date_from=${customDateFrom}&date_to=${customDateTo}`;
  }
  return `days=${currentDays}`;
}

// ── Auto Refresh ─────────────────────────────────────────────────────────────
function scheduleAutoRefresh() {
  clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    loadSection(currentSection);
  }, AUTO_REFRESH_MS);
}

// ── Load Section ─────────────────────────────────────────────────────────────
function loadSection(name) {
  setRefreshSpinning(true);
  const loaders = {
    overview: loadOverview,
    facebook: loadFacebook,
    google:   loadGoogle,
    ga4:      loadGA4,
    shopify:  loadShopify,
  };
  const fn = loaders[name];
  if (fn) fn().finally(() => setRefreshSpinning(false));
}

// ── API Fetch Helper ─────────────────────────────────────────────────────────
async function apiFetch(endpoint) {
  const params = getQueryParams();
  const res = await fetch(`${endpoint}?${params}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function setRefreshSpinning(on) {
  const btn = document.getElementById('refresh-btn');
  btn.classList.toggle('spinning', on);
}

function showErrors(errors) {
  const banner = document.getElementById('error-banner');
  if (!errors || errors.length === 0) {
    banner.classList.add('hidden');
    return;
  }
  banner.classList.remove('hidden');
  banner.innerHTML = '<strong>Atenção:</strong> ' +
    errors.map(e => `${e.source}: ${e.message}`).join(' · ');
}

function updateLastRefreshed(period) {
  const now = new Date().toLocaleTimeString('pt-BR');
  document.getElementById('last-updated').textContent = `Atualizado às ${now}`;
  if (period) {
    document.getElementById('period-label').textContent =
      `${fmtDate(period.from)} → ${fmtDate(period.to)} (${period.days || '–'} dias)`;
  }
}

// ── Format Helpers ────────────────────────────────────────────────────────────
function fmtBRL(v)  { return 'R$ ' + Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function fmtN(v)    { return Number(v || 0).toLocaleString('pt-BR'); }
function fmtPct(v)  { return Number(v || 0).toFixed(2) + '%'; }
function fmtX(v)    { return Number(v || 0).toFixed(2) + 'x'; }
function fmtDate(d) { if (!d) return '–'; const [y,m,day] = d.split('-'); return `${day}/${m}/${y}`; }

function roas_class(v) {
  if (v >= 3)  return 'roas-high';
  if (v >= 1.5) return 'roas-mid';
  return 'roas-low';
}

// ── Chart Utilities ───────────────────────────────────────────────────────────
const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11 } } } },
  scales: {
    x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: '#1e2330' } },
    y: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: '#1e2330' } },
  },
};

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

function createLineChart(id, labels, datasets) {
  destroyChart(id);
  const ctx = document.getElementById(id)?.getContext('2d');
  if (!ctx) return;
  charts[id] = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      ...CHART_DEFAULTS,
      plugins: { ...CHART_DEFAULTS.plugins, tooltip: { mode: 'index', intersect: false } },
      scales: { ...CHART_DEFAULTS.scales },
    },
  });
}

function createBarChart(id, labels, datasets, opts = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id)?.getContext('2d');
  if (!ctx) return;
  charts[id] = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: { ...CHART_DEFAULTS, ...opts },
  });
}

function createDoughnutChart(id, labels, data, colors) {
  destroyChart(id);
  const ctx = document.getElementById(id)?.getContext('2d');
  if (!ctx) return;
  charts[id] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors, borderWidth: 0 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 12 } },
      },
    },
  });
}

function dailyToChartData(trend) {
  return {
    labels: trend.map(r => fmtDate(r.date)),
    values: trend.map(r => r.value),
  };
}

// ── OVERVIEW ─────────────────────────────────────────────────────────────────
async function loadOverview() {
  try {
    const d = await apiFetch('/api/overview');
    const ov = d.overview;
    const fb = d.facebook;
    const gg = d.google;
    const sh = d.shopify;
    const ga = d.ga4;

    // KPI cards
    setText('kpi-revenue',  fmtBRL(ov.total_revenue));
    setText('kpi-spend',    fmtBRL(ov.total_spend));
    setText('kpi-roas',     fmtX(ov.total_roas));
    setText('kpi-orders',   fmtN(ov.total_orders));
    setText('kpi-aov',      fmtBRL(ov.aov));
    setText('kpi-sessions', fmtN(ov.sessions));
    setText('kpi-new-users',fmtN(ov.new_users));
    setText('kpi-cac',      fmtBRL(ov.cac));

    // Channel mini-cards — Facebook
    setText('fb-roas-badge', `ROAS ${fmtX(fb.roas)}`);
    setText('ov-fb-spend',  fmtBRL(fb.spend));
    setText('ov-fb-clicks', fmtN(fb.clicks));
    setText('ov-fb-ctr',    fmtPct(fb.ctr));
    setText('ov-fb-cpa',    fmtBRL(fb.cpa));

    // Channel mini-cards — Google
    setText('gg-roas-badge', `ROAS ${fmtX(gg.roas)}`);
    setText('ov-gg-spend',  fmtBRL(gg.spend));
    setText('ov-gg-clicks', fmtN(gg.clicks));
    setText('ov-gg-ctr',    fmtPct(gg.ctr));
    setText('ov-gg-cpa',    fmtBRL(gg.cpa));

    // Channel mini-cards — Shopify
    setText('sh-conv-badge', `AOV ${fmtBRL(sh.aov)}`);
    setText('ov-sh-revenue', fmtBRL(sh.revenue));
    setText('ov-sh-orders',  fmtN(sh.orders));
    setText('ov-sh-aov',     fmtBRL(sh.aov));
    setText('ov-sh-new',     fmtN(sh.new_customers));

    // Channel mini-cards — GA4
    setText('ga-cr-badge', `CR ${fmtPct(ga.conversion_rate)}`);
    setText('ov-ga-sessions', fmtN(ga.sessions));
    setText('ov-ga-users',    fmtN(ga.users));
    setText('ov-ga-new',      fmtN(ga.new_users));
    setText('ov-ga-conv',     fmtN(ga.conversions));

    // Charts — Spend por canal
    createBarChart('chart-channel-spend',
      ['Facebook Ads', 'Google Ads'],
      [{
        label: 'Investimento (R$)',
        data: [fb.spend, gg.spend],
        backgroundColor: [CHART_COLORS.fb.border, CHART_COLORS.gg.border],
        borderRadius: 6,
      }],
      { plugins: { legend: { display: false } } }
    );

    // Charts — ROAS por canal
    createBarChart('chart-channel-roas',
      ['Facebook Ads', 'Google Ads'],
      [{
        label: 'ROAS',
        data: [fb.roas, gg.roas],
        backgroundColor: [CHART_COLORS.rev.border, CHART_COLORS.spend.border],
        borderRadius: 6,
      }],
      { plugins: { legend: { display: false } } }
    );

    showErrors(d.errors);
    updateLastRefreshed(d.period);
  } catch (err) {
    showErrors([{ source: 'API', message: err.message }]);
  }
}

// ── FACEBOOK ADS ──────────────────────────────────────────────────────────────
async function loadFacebook() {
  try {
    const d = await apiFetch('/api/facebook');
    const s = d.summary;

    setText('fb-spend',       fmtBRL(s.spend));
    setText('fb-roas',        fmtX(s.roas));
    setText('fb-conversions', fmtN(s.conversions));
    setText('fb-ctr',         fmtPct(s.ctr));
    setText('fb-cpa',         fmtBRL(s.cpa));

    // Daily chart
    const spendTrend = dailyToChartData(d.daily_spend);
    const revTrend   = dailyToChartData(d.daily_revenue);
    createLineChart('chart-fb-daily', spendTrend.labels, [
      { label: 'Investimento (R$)', data: spendTrend.values, borderColor: CHART_COLORS.spend.border, backgroundColor: CHART_COLORS.spend.bg, fill: true, tension: .4, pointRadius: 2 },
      { label: 'Receita (R$)',      data: revTrend.values,   borderColor: CHART_COLORS.rev.border,   backgroundColor: CHART_COLORS.rev.bg,   fill: true, tension: .4, pointRadius: 2 },
    ]);

    // Campaigns bar chart (top 6)
    const top = d.campaigns.slice(0, 6);
    createBarChart('chart-fb-campaigns',
      top.map(c => truncate(c.campaign_name, 18)),
      [{ label: 'Investimento', data: top.map(c => c.spend), backgroundColor: CHART_COLORS.fb.border, borderRadius: 4 }],
      { indexAxis: 'y', plugins: { legend: { display: false } } }
    );

    // Table
    renderCampaignTable('fb-campaigns-body', d.campaigns);
    updateLastRefreshed();
  } catch (err) {
    showErrors([{ source: 'Facebook Ads', message: err.message }]);
  }
}

// ── GOOGLE ADS ───────────────────────────────────────────────────────────────
async function loadGoogle() {
  try {
    const d = await apiFetch('/api/google');
    const s = d.summary;

    setText('gg-spend',       fmtBRL(s.spend));
    setText('gg-roas',        fmtX(s.roas));
    setText('gg-conversions', fmtN(s.conversions));
    setText('gg-ctr',         fmtPct(s.ctr));
    setText('gg-cpa',         fmtBRL(s.cpa));

    const spendTrend = dailyToChartData(d.daily_spend);
    const revTrend   = dailyToChartData(d.daily_revenue);
    createLineChart('chart-gg-daily', spendTrend.labels, [
      { label: 'Investimento (R$)', data: spendTrend.values, borderColor: CHART_COLORS.spend.border, backgroundColor: CHART_COLORS.spend.bg, fill: true, tension: .4, pointRadius: 2 },
      { label: 'Receita (R$)',      data: revTrend.values,   borderColor: CHART_COLORS.rev.border,   backgroundColor: CHART_COLORS.rev.bg,   fill: true, tension: .4, pointRadius: 2 },
    ]);

    const top = d.campaigns.slice(0, 6);
    createBarChart('chart-gg-campaigns',
      top.map(c => truncate(c.campaign_name, 18)),
      [{ label: 'Investimento', data: top.map(c => c.spend), backgroundColor: CHART_COLORS.gg.border, borderRadius: 4 }],
      { indexAxis: 'y', plugins: { legend: { display: false } } }
    );

    renderCampaignTable('gg-campaigns-body', d.campaigns);
    updateLastRefreshed();
  } catch (err) {
    showErrors([{ source: 'Google Ads', message: err.message }]);
  }
}

// ── GA4 ───────────────────────────────────────────────────────────────────────
async function loadGA4() {
  try {
    const d = await apiFetch('/api/ga4');
    const s = d.summary;

    setText('ga4-sessions',  fmtN(s.sessions));
    setText('ga4-users',     fmtN(s.users));
    setText('ga4-new-users', fmtN(s.new_users));
    setText('ga4-conversions', fmtN(s.conversions));
    setText('ga4-cr',        fmtPct(s.conversion_rate));

    // Daily sessions chart
    const sess = dailyToChartData(d.daily_sessions);
    createLineChart('chart-ga4-daily', sess.labels, [
      { label: 'Sessões', data: sess.values, borderColor: CHART_COLORS.sess.border, backgroundColor: CHART_COLORS.sess.bg, fill: true, tension: .4, pointRadius: 2 },
    ]);

    // Channels doughnut
    const channels = d.channels.slice(0, 8);
    const palette = ['#3b82f6','#a855f7','#14b8a6','#f59e0b','#ec4899','#22c55e','#f97316','#64748b'];
    createDoughnutChart('chart-ga4-channels',
      channels.map(c => c.channel),
      channels.map(c => c.sessions),
      palette,
    );

    // Channels table
    const tbody = document.getElementById('ga4-channels-body');
    if (tbody) {
      tbody.innerHTML = channels.map(c => `
        <tr>
          <td>${c.channel}</td>
          <td>${fmtN(c.sessions)}</td>
          <td>${fmtN(c.users)}</td>
          <td>${fmtN(c.conversions)}</td>
        </tr>
      `).join('') || '<tr><td colspan="4" class="loading-row">Sem dados</td></tr>';
    }

    updateLastRefreshed();
  } catch (err) {
    showErrors([{ source: 'GA4', message: err.message }]);
  }
}

// ── SHOPIFY ───────────────────────────────────────────────────────────────────
async function loadShopify() {
  try {
    const d = await apiFetch('/api/shopify');
    const s = d.summary;

    setText('sh-revenue',  fmtBRL(s.revenue));
    setText('sh-orders',   fmtN(s.orders));
    setText('sh-aov',      fmtBRL(s.aov));
    setText('sh-new-cust', fmtN(s.new_customers));
    setText('sh-ret-cust', fmtN(s.returning_customers));

    // Revenue daily chart
    const rev = dailyToChartData(d.daily_revenue);
    createLineChart('chart-sh-revenue', rev.labels, [
      { label: 'Receita (R$)', data: rev.values, borderColor: CHART_COLORS.sh.border, backgroundColor: CHART_COLORS.sh.bg, fill: true, tension: .4, pointRadius: 2 },
    ]);

    // Orders daily chart
    const ord = dailyToChartData(d.daily_orders);
    createBarChart('chart-sh-orders',
      ord.labels,
      [{ label: 'Pedidos', data: ord.values, backgroundColor: CHART_COLORS.sh.border, borderRadius: 4 }],
    );

    updateLastRefreshed();
  } catch (err) {
    showErrors([{ source: 'Shopify', message: err.message }]);
  }
}

// ── Render Helpers ────────────────────────────────────────────────────────────
function renderCampaignTable(tbodyId, campaigns) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;

  if (!campaigns || campaigns.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="loading-row">Sem dados para o período.</td></tr>';
    return;
  }

  tbody.innerHTML = campaigns.map(c => `
    <tr>
      <td title="${c.campaign_name}">${truncate(c.campaign_name, 35)}</td>
      <td>${fmtBRL(c.spend)}</td>
      <td>${fmtN(c.impressions)}</td>
      <td>${fmtN(c.clicks)}</td>
      <td>${fmtPct(c.ctr)}</td>
      <td>${fmtBRL(c.cpc)}</td>
      <td>${fmtN(c.conversions)}</td>
      <td>${fmtBRL(c.revenue)}</td>
      <td class="${roas_class(c.roas)}">${fmtX(c.roas)}</td>
    </tr>
  `).join('');
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '…' : str;
}
