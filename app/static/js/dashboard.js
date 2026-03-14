/* ======================================================================
   dashboard.js — Dashboard principal
   - Carga datos del usuario, mercado, cuentas y estrategias
   - Dibuja gráfica de precio BTC/USDT con Canvas
   ====================================================================== */

'use strict';

// ── Utilidades ────────────────────────────────────────────────────────

function fmtPrice(n) {
  if (n == null) return '—';
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function capitalize(str) {
  if (!str) return '—';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Régimen badge ─────────────────────────────────────────────────────

const REGIME_LABEL = { trend_up: 'Tendencia alcista', trend_down: 'Tendencia bajista', sideways: 'Mercado lateral' };
const REGIME_COLOR = { trend_up: '#22c55e', trend_down: '#ef4444', sideways: '#f0b429' };

function regimeBadge(regime) {
  if (!regime) return '';
  const color = REGIME_COLOR[regime] || '#64748b';
  const label = REGIME_LABEL[regime] || regime;
  return `<span style="
    font-size:0.7rem;padding:2px 8px;border-radius:10px;
    background:${color}22;color:${color};font-weight:600;
    border:1px solid ${color}44;
  ">${label}</span>`;
}

// ── Canvas chart ──────────────────────────────────────────────────────

function drawPriceChart(candles) {
  const canvas = document.getElementById('price-canvas');
  const empty  = document.getElementById('chart-empty');

  if (!candles.length) {
    canvas.style.display = 'none';
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');
  canvas.style.display = 'block';

  const dpr    = window.devicePixelRatio || 1;
  const W      = canvas.parentElement.clientWidth;
  const H      = 200;
  canvas.width  = W * dpr;
  canvas.height = H * dpr;
  canvas.style.height = H + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const closes = candles.map(c => parseFloat(c.close));
  const minP   = Math.min(...closes);
  const maxP   = Math.max(...closes);
  const range  = maxP - minP || 1;

  const pad = { top: 16, right: 16, bottom: 36, left: 64 };
  const cW   = W - pad.left - pad.right;
  const cH   = H - pad.top  - pad.bottom;

  const xOf = i => pad.left + (i / (closes.length - 1)) * cW;
  const yOf = p => pad.top  + (1 - (p - minP) / range) * cH;

  // Background
  ctx.clearRect(0, 0, W, H);

  // Grid lines (4 horizontal)
  ctx.strokeStyle = 'rgba(37,45,66,0.8)';
  ctx.lineWidth   = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (i / 4) * cH;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(W - pad.right, y);
    ctx.stroke();
  }

  // Y-axis labels
  ctx.fillStyle   = '#64748b';
  ctx.font        = '10px JetBrains Mono, monospace';
  ctx.textAlign   = 'right';
  ctx.textBaseline = 'middle';
  for (let i = 0; i <= 4; i++) {
    const p = maxP - (i / 4) * range;
    const y = pad.top + (i / 4) * cH;
    ctx.fillText('$' + p.toLocaleString('en-US', { maximumFractionDigits: 0 }), pad.left - 6, y);
  }

  // X-axis labels (first, middle, last)
  ctx.textAlign   = 'center';
  ctx.textBaseline = 'top';
  const xIdxs = [0, Math.floor(closes.length / 2), closes.length - 1];
  xIdxs.forEach(i => {
    const ts  = candles[i].ts;
    const dt  = new Date(ts);
    const lbl = dt.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
    ctx.fillText(lbl, xOf(i), H - pad.bottom + 8);
  });

  // Gradient fill under line
  const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + cH);
  const isUp = closes[closes.length - 1] >= closes[0];
  const lineColor = isUp ? '#22c55e' : '#ef4444';
  grad.addColorStop(0, isUp ? 'rgba(34,197,94,0.18)' : 'rgba(239,68,68,0.18)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');

  ctx.beginPath();
  ctx.moveTo(xOf(0), yOf(closes[0]));
  for (let i = 1; i < closes.length; i++) ctx.lineTo(xOf(i), yOf(closes[i]));
  ctx.lineTo(xOf(closes.length - 1), H - pad.bottom);
  ctx.lineTo(xOf(0), H - pad.bottom);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Price line
  ctx.beginPath();
  ctx.strokeStyle = lineColor;
  ctx.lineWidth   = 1.5;
  ctx.lineJoin    = 'round';
  ctx.moveTo(xOf(0), yOf(closes[0]));
  for (let i = 1; i < closes.length; i++) ctx.lineTo(xOf(i), yOf(closes[i]));
  ctx.stroke();

  // Last price dot
  const lx = xOf(closes.length - 1);
  const ly = yOf(closes[closes.length - 1]);
  ctx.beginPath();
  ctx.arc(lx, ly, 3.5, 0, Math.PI * 2);
  ctx.fillStyle = lineColor;
  ctx.fill();
}

// ── API helpers ───────────────────────────────────────────────────────

async function get(url) {
  const res = await fetch(url, { credentials: 'include' });
  if (res.status === 401) { window.location.href = '/login'; throw new Error('401'); }
  return res.json();
}

// ── Loaders ───────────────────────────────────────────────────────────

async function loadMe() {
  const json = await get('/users/me');
  if (!json.data) throw new Error('no user');
  return json.data;
}

async function loadStrategies() {
  try {
    const json = await get('/api/strategies');
    const list = Array.isArray(json.data) ? json.data : [];
    const trend = list.filter(s => s.parameters?.strategy_type === 'trend_following').length;
    const mr    = list.filter(s => s.parameters?.strategy_type === 'mean_reversion').length;
    document.getElementById('strategies-value').textContent = list.length;
    document.getElementById('strategies-meta').textContent  =
      list.length ? `${trend} trend · ${mr} mean rev.` : 'Sin estrategias';
  } catch {
    document.getElementById('strategies-value').textContent = '—';
    document.getElementById('strategies-meta').textContent  = 'No disponible';
  }
}

async function loadAccounts() {
  try {
    const json  = await get('/accounts');
    const list  = Array.isArray(json.data) ? json.data : [];
    const paper = list.filter(a => a.mode === 'paper').length;
    const live  = list.filter(a => a.mode === 'live').length;
    document.getElementById('accounts-value').textContent = list.length;
    const parts = [];
    if (paper) parts.push(paper + ' paper');
    if (live)  parts.push(live  + ' live');
    document.getElementById('accounts-meta').textContent =
      parts.length ? parts.join(' · ') : 'Sin cuentas';
  } catch {
    document.getElementById('accounts-value').textContent = '—';
    document.getElementById('accounts-meta').textContent  = 'No disponible';
  }
}

async function loadMarket() {
  try {
    const [symbolsJson, timeframesJson] = await Promise.all([
      get('/symbols?is_active=true'),
      get('/timeframes'),
    ]);

    const symbols    = Array.isArray(symbolsJson.data)    ? symbolsJson.data    : [];
    const timeframes = Array.isArray(timeframesJson.data) ? timeframesJson.data : [];

    const tf1h = timeframes.find(t => t.code === '1h');
    if (!tf1h) return;

    const symBTC = symbols.find(s => s.symbol === 'BTC/USDT');
    const symETH = symbols.find(s => s.symbol === 'ETH/USDT');

    await Promise.all([
      symBTC ? loadSymbolCard(symBTC.id, tf1h.id, 'btc-price', 'btc-meta', 'card-btc', true) : setCardNoData('btc-price', 'btc-meta'),
      symETH ? loadSymbolCard(symETH.id, tf1h.id, 'eth-price', 'eth-meta', 'card-eth', false) : setCardNoData('eth-price', 'eth-meta'),
    ]);
  } catch {
    setCardNoData('btc-price', 'btc-meta');
    setCardNoData('eth-price', 'eth-meta');
  }
}

function setCardNoData(priceId, metaId) {
  document.getElementById(priceId).textContent = 'Sin datos';
  document.getElementById(metaId).textContent  = 'No hay velas en BD';
}

async function loadSymbolCard(symbolId, tfId, priceId, metaId, cardId, withChart) {
  try {
    const [candlesJson, featuresJson] = await Promise.all([
      get(`/candles?symbol_id=${symbolId}&timeframe_id=${tfId}&limit=48`),
      get(`/candle-features?symbol_id=${symbolId}&timeframe_id=${tfId}&limit=1`),
    ]);

    const candles  = Array.isArray(candlesJson.data)  ? candlesJson.data  : [];
    const features = Array.isArray(featuresJson.data) ? featuresJson.data : [];

    if (!candles.length) {
      setCardNoData(priceId, metaId);
      return;
    }

    // Ordenar por ts ascendente
    candles.sort((a, b) => new Date(a.ts) - new Date(b.ts));

    const last  = candles[candles.length - 1];
    const prev  = candles[candles.length - 2];
    const price = parseFloat(last.close);
    const chg   = prev ? ((price - parseFloat(prev.close)) / parseFloat(prev.close)) * 100 : 0;
    const isUp  = chg >= 0;

    document.getElementById(priceId).textContent = fmtPrice(price);
    document.getElementById(priceId).style.color = isUp ? 'var(--success,#22c55e)' : 'var(--error,#ef4444)';

    const regime = features[0]?.features?.regime || null;
    const chgStr = (isUp ? '+' : '') + chg.toFixed(2) + '%';

    const metaEl = document.getElementById(metaId);
    metaEl.innerHTML = `<span style="color:${isUp ? '#22c55e' : '#ef4444'}">${chgStr}</span>`;
    if (regime) metaEl.innerHTML += ' &nbsp;' + regimeBadge(regime);

    if (withChart) {
      drawPriceChart(candles);
      const badge = document.getElementById('chart-regime-badge');
      if (badge && regime) badge.innerHTML = regimeBadge(regime);
    }
  } catch {
    setCardNoData(priceId, metaId);
  }
}

// ── Render dashboard ──────────────────────────────────────────────────

function renderUser(user) {
  const name    = user.full_name || user.email.split('@')[0];
  const isAdmin = user.role_label === 'Administrador';

  document.getElementById('dash-greeting').textContent = 'Hola, ' + name;
  document.getElementById('dash-email').textContent    = user.email;

  const badge = document.getElementById('nav-role-badge');
  badge.className   = 'badge ' + (isAdmin ? 'badge--admin' : 'badge--user');
  badge.textContent = user.role_label;

  document.getElementById('info-email').textContent      = user.email;
  document.getElementById('info-role').textContent       = user.role_label;
  document.getElementById('info-status').textContent     = capitalize(user.status);
  document.getElementById('info-last-login').textContent = user.last_login_at
    ? new Date(user.last_login_at).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
    : 'Primera sesión';

  if (isAdmin) document.getElementById('admin-panel').classList.remove('hidden');

  document.getElementById('dashboard-loading').classList.add('hidden');
  document.getElementById('dashboard-content').classList.remove('hidden');

  lucide.createIcons();
}

function showError() {
  document.getElementById('dashboard-loading').classList.add('hidden');
  document.getElementById('dashboard-error').classList.remove('hidden');
}

// ── Logout ────────────────────────────────────────────────────────────

async function logout() {
  try {
    await fetch('/users/logout', { method: 'POST', credentials: 'include' });
  } finally {
    window.location.href = '/login';
  }
}

// ── Init ──────────────────────────────────────────────────────────────

function applyGridResponsive() {
  const grid = document.getElementById('dash-stats-grid');
  if (!grid) return;
  const w = window.innerWidth;
  if (w <= 480)      grid.style.gridTemplateColumns = '1fr';
  else if (w <= 900) grid.style.gridTemplateColumns = 'repeat(2,1fr)';
  else               grid.style.gridTemplateColumns = 'repeat(4,1fr)';
}

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('btn-logout-nav').addEventListener('click', logout);
  document.getElementById('btn-logout-main').addEventListener('click', logout);
  window.addEventListener('resize', applyGridResponsive);
  applyGridResponsive();

  loadMe()
    .then(user => {
      renderUser(user);
      loadStrategies();
      loadAccounts();
      loadMarket();
    })
    .catch(showError);
});
