// admin/candles_ingest.js
// Descarga velas OHLCV desde exchange real via ccxt

document.addEventListener('DOMContentLoaded', function () {
  loadSymbols();
  loadTimeframes();
  document.getElementById('btn-fetch').addEventListener('click', fetchCandles);
});

async function loadSymbols() {
  try {
    const res = await fetch('/symbols?is_active=true', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('sel-symbol');
    sel.innerHTML = '<option value="">Selecciona un símbolo...</option>';
    (json.data || []).forEach(function (s) {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = s.symbol + ' (' + (s.asset_class || '') + ')';
      sel.appendChild(opt);
    });
  } catch {}
}

async function loadTimeframes() {
  try {
    const res = await fetch('/timeframes', { credentials: 'include' });
    const json = await res.json();
    if (!res.ok) return;
    const sel = document.getElementById('sel-timeframe');
    sel.innerHTML = '<option value="">Selecciona un timeframe...</option>';
    (json.data || []).forEach(function (tf) {
      const opt = document.createElement('option');
      opt.value = tf.id;
      opt.textContent = tf.code;
      sel.appendChild(opt);
    });
  } catch {}
}

async function fetchCandles() {
  clearAlert();

  const symbolId = document.getElementById('sel-symbol').value;
  const timeframeId = document.getElementById('sel-timeframe').value;
  const limit = parseInt(document.getElementById('sel-limit').value, 10);

  if (!symbolId) { showAlert('Selecciona un símbolo.', 'error'); return; }
  if (!timeframeId) { showAlert('Selecciona un timeframe.', 'error'); return; }

  setBtnLoading(true);
  document.getElementById('result-box').classList.add('hidden');

  try {
    const res = await fetch('/candles/fetch', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol_id: parseInt(symbolId, 10),
        timeframe_id: parseInt(timeframeId, 10),
        limit: limit,
      }),
    });

    const json = await res.json();

    if (!res.ok) {
      showAlert(json.msg || 'Error al descargar velas.', 'error');
      return;
    }

    const d = json.data;
    document.getElementById('res-exchange').textContent = d.exchange || '—';
    document.getElementById('res-symbol').textContent = d.symbol || '—';
    document.getElementById('res-timeframe').textContent = d.timeframe || '—';
    document.getElementById('res-fetched').textContent = d.rows_fetched || 0;
    document.getElementById('result-box').classList.remove('hidden');
    showAlert(json.msg, 'success');

  } catch {
    showAlert('Error de conexión.', 'error');
  } finally {
    setBtnLoading(false);
  }
}

function setBtnLoading(loading) {
  const btn = document.getElementById('btn-fetch');
  const txt = document.getElementById('btn-fetch-text');
  const spin = document.getElementById('btn-fetch-spinner');
  btn.disabled = loading;
  txt.textContent = loading ? 'Descargando...' : 'Descargar del exchange';
  spin.classList.toggle('hidden', !loading);
}

function showAlert(msg, type) {
  const el = document.getElementById('alert-msg');
  el.textContent = msg;
  el.className = 'alert alert--' + (type === 'error' ? 'error' : 'success') + ' show';
}

function clearAlert() {
  const el = document.getElementById('alert-msg');
  el.className = 'alert hidden';
  el.textContent = '';
}
