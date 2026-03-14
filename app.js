/**
 * app.js — Adjusted EPS Analyzer 全フロントエンドロジック
 * 依存: Chart.js, jQuery, DataTables, Bootstrap 5
 */

// ═══════════════════════════════════════════════════════════
// グローバル状態
// ═══════════════════════════════════════════════════════════
let APP = {
  indexData:   null,   // data/index.json
  tickerCache: {},     // {ticker: {latest, history, ttm}}
  currentTicker: null,
  currentPeriod: "Q",  // Q / A / TTM
  charts: {},          // Chart インスタンス管理
  dt: null,            // DataTable インスタンス
};

// ═══════════════════════════════════════════════════════════
// 初期化
// ═══════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  initTooltips();
  initNavButtons();
  initSearch();
  initValInputs();

  try {
    await loadIndexData();
  } catch(e) {
    showError("data/index.json の読み込みに失敗しました。<br>GitHub Actions を実行してデータを生成してください。", e);
  }

  hideLoading();
  navigate("dashboard");
});

// ─── index.json ロード ────────────────────────────────────
async function loadIndexData() {
  const res = await fetch("data/index.json");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  APP.indexData = await res.json();

  // ダッシュボード更新日時
  document.getElementById("last-updated").textContent =
    `最終更新: ${new Date(APP.indexData.updated_at).toLocaleString("ja-JP")}`;

  // 銘柄選択プルダウンを設定
  const sel = document.getElementById("detail-ticker-select");
  (APP.indexData.tickers || []).forEach(t => {
    sel.innerHTML += `<option value="${t.ticker}">${t.ticker}</option>`;
  });

  // 設定画面のティッカーバッジ
  const settingsDiv = document.getElementById("settings-tickers");
  (APP.indexData.tickers || []).forEach(t => {
    settingsDiv.innerHTML += `
      <span class="bg-blue-900 text-blue-200 px-2 py-0.5 rounded text-xs">${t.ticker}</span>`;
  });
}

// ═══════════════════════════════════════════════════════════
// ナビゲーション
// ═══════════════════════════════════════════════════════════
function navigate(page) {
  document.querySelectorAll(".page-section").forEach(s => s.classList.remove("active"));
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.add("active");

  // ナビボタンのアクティブ状態
  document.querySelectorAll(".nav-btn").forEach(b => {
    b.classList.toggle("bg-blue-700", b.dataset.page === page);
    b.classList.toggle("text-white",  b.dataset.page === page);
  });

  // ページ別初期化
  if (page === "dashboard") renderDashboard();
  if (page === "list")      renderList();
  if (page === "forecast")  updateForecastChart();
}

// ─── スタイル用クラス付きナビボタン初期化 ─────────────────
function initNavButtons() {
  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.classList.add(
      "px-3", "py-1.5", "rounded", "text-sm",
      "hover:bg-gray-700", "transition-colors", "text-gray-300"
    );
  });
}

// ═══════════════════════════════════════════════════════════
// ① ダッシュボード
// ═══════════════════════════════════════════════════════════
function renderDashboard() {
  if (!APP.indexData) return;
  const tickers = APP.indexData.tickers || [];

  // Top 5 YoY 成長率カード
  const top5 = [...tickers]
    .filter(t => t.yoy_growth_pct != null)
    .sort((a,b) => b.yoy_growth_pct - a.yoy_growth_pct)
    .slice(0, 5);
  renderTop5Cards(top5);

  // 健全銘柄
  const healthy = tickers.filter(t => ["Excellent","Good"].includes(t.health));
  renderHealthyCards(healthy);

  // 全銘柄グリッド
  renderAllTickerCards(tickers);
}

function renderTop5Cards(list) {
  const el = document.getElementById("top5-cards");
  el.innerHTML = list.length === 0
    ? `<p class="text-gray-500 col-span-5">データ不足 — 5件以上の四半期データが必要です</p>`
    : list.map(t => `
      <div class="bg-gray-800 rounded-xl p-4 cursor-pointer hover:bg-gray-700 transition"
           onclick="openDetailFor('${t.ticker}')">
        <p class="text-xl font-bold text-blue-400">${t.ticker}</p>
        <p class="text-sm text-gray-400">${t.latest_period || "N/A"}</p>
        <p class="text-2xl font-bold mt-2 ${t.yoy_growth_pct >= 0 ? 'text-green-400':'text-red-400'}">
          ${t.yoy_growth_pct >= 0 ? '+':''}${(t.yoy_growth_pct||0).toFixed(1)}%
        </p>
        <p class="text-xs text-gray-500 mt-1">実質EPS YoY</p>
        ${healthBadge(t.health)}
      </div>`).join("");
}

function renderHealthyCards(list) {
  const el = document.getElementById("healthy-cards");
  el.innerHTML = list.length === 0
    ? `<p class="text-gray-500 col-span-6">今週の対象なし</p>`
    : list.map(t => `
      <div class="bg-gray-800 rounded-lg p-3 cursor-pointer hover:bg-gray-700 transition text-center"
           onclick="openDetailFor('${t.ticker}')">
        <p class="font-bold text-blue-400">${t.ticker}</p>
        ${healthBadge(t.health)}
        <p class="text-xs text-gray-400 mt-1">EPS ${fmt(t.adjusted_eps)}</p>
      </div>`).join("");
}

function renderAllTickerCards(list) {
  const el = document.getElementById("all-ticker-cards");
  el.innerHTML = list.map(t => `
    <div class="bg-gray-800 rounded-lg p-3 cursor-pointer hover:bg-gray-700 transition"
         onclick="openDetailFor('${t.ticker}')">
      <p class="font-semibold text-white">${t.ticker}</p>
      ${healthBadge(t.health)}
      <p class="text-xs text-gray-400 mt-1">実質EPS ${fmt(t.adjusted_eps)}</p>
    </div>`).join("");
}

// ═══════════════════════════════════════════════════════════
// ② 銘柄一覧（DataTables）
// ═══════════════════════════════════════════════════════════
function renderList() {
  if (!APP.indexData) return;
  const tickers = APP.indexData.tickers || [];

  const tbody = document.getElementById("tickers-tbody");
  tbody.innerHTML = tickers.map(t => `
    <tr class="cursor-pointer" onclick="openDetailFor('${t.ticker}')">
      <td class="text-blue-400 font-semibold">${t.ticker}</td>
      <td class="text-gray-400">${t.latest_period || "N/A"}</td>
      <td class="${(t.gaap_eps||0) >= 0 ? 'text-green-400':'text-red-400'}">${fmt(t.gaap_eps)}</td>
      <td class="${(t.adjusted_eps||0) >= 0 ? 'text-green-400':'text-red-400'} font-semibold">${fmt(t.adjusted_eps)}</td>
      <td class="${(t.ttm_adjusted_eps||0) >= 0 ? 'text-green-300':'text-red-400'}">${fmt(t.ttm_adjusted_eps)}</td>
      <td class="${(t.yoy_growth_pct||0) >= 0 ? 'text-green-400':'text-red-400'}">
        ${t.yoy_growth_pct != null ? ((t.yoy_growth_pct>=0?'+':'') + t.yoy_growth_pct.toFixed(1)+'%') : '—'}
      </td>
      <td>${healthBadge(t.health)}</td>
    </tr>`).join("");

  // DataTable 初期化（再初期化防止）
  if (APP.dt) { APP.dt.destroy(); APP.dt = null; }
  APP.dt = $("#tickers-table").DataTable({
    pageLength: 20,
    order: [[5, "desc"]],
    language: {
      url: "https://cdn.datatables.net/plug-ins/1.13.8/i18n/ja.json",
    },
    dom: 'Bfrtip',
    buttons: ['excelHtml5'],
  });
}

function exportTableToExcel() {
  if (APP.dt) APP.dt.button('.buttons-excel').trigger();
}

// ═══════════════════════════════════════════════════════════
// ③ 個別銘柄分析
// ═══════════════════════════════════════════════════════════
async function openDetailFor(ticker) {
  navigate("detail");
  document.getElementById("detail-ticker-select").value = ticker;
  await loadDetailPage(ticker);
}

async function loadDetailPage(ticker) {
  ticker = ticker || document.getElementById("detail-ticker-select").value;
  if (!ticker) return;
  APP.currentTicker = ticker;

  setLoading(true, `${ticker} のデータを読み込み中...`);

  try {
    // latest.json + history.json + ttm.json を並列取得
    const [latest, history, ttm] = await Promise.all([
      fetchJson(`data/${ticker}/latest.json`).catch(() => null),
      fetchJson(`data/${ticker}/history.json`).catch(() => null),
      fetchJson(`data/${ticker}/ttm.json`).catch(() => null),
    ]);

    APP.tickerCache[ticker] = { latest, history, ttm };
    renderDetailPage(ticker);

  } catch(e) {
    showError(`${ticker} のデータ取得に失敗しました。`, e);
  } finally {
    setLoading(false);
  }
}

function renderDetailPage(ticker) {
  const cache  = APP.tickerCache[ticker];
  const latest = cache?.latest;

  if (!latest) {
    document.getElementById("detail-content").classList.add("hidden");
    document.getElementById("detail-empty").classList.remove("hidden");
    return;
  }

  document.getElementById("detail-content").classList.remove("hidden");
  document.getElementById("detail-empty").classList.add("hidden");

  // ヘッダー
  document.getElementById("detail-ticker-name").textContent = ticker;
  document.getElementById("detail-period").textContent =
    `${latest.period_of_report || ""} (${latest.period_type || ""}) 申告日: ${latest.filed_at || "N/A"}`;
  document.getElementById("detail-gaap-eps").textContent = fmt(latest.gaap_eps);
  document.getElementById("detail-adj-eps").textContent  = fmt(latest.adjusted_eps);
  document.getElementById("detail-shares").textContent =
    formatShares(latest.diluted_shares_used);

  // 健全性バッジ
  const hel = latest.ai_analysis?.health || "Unknown";
  const badge = document.getElementById("detail-health-badge");
  badge.textContent  = healthLabel(hel);
  badge.className    = `text-xl font-bold px-3 py-1 rounded-full badge-${hel}`;

  // AI コメント
  document.getElementById("detail-ai-text").textContent =
    latest.ai_analysis?.comment || "AI 分析データなし";

  // ウォーターフォールチャート（最新期）
  renderWaterfallChart(latest);

  // 調整内訳アコーディオン
  renderAdjustmentsAccordion(latest.adjustments || []);

  // EPS 推移グラフ（デフォルト: Quarterly）
  switchPeriod(APP.currentPeriod);

  // バリュエーション入力値を設定
  const annualEps = latest.period_type === "A" ? latest.adjusted_eps :
                    (cache.ttm?.adjusted_eps || latest.adjusted_eps * 4);
  document.getElementById("val-eps").value = (annualEps || 0).toFixed(4);
  updateValuation();
}

// ─── 期間タブ切替 ─────────────────────────────────────────
function switchPeriod(period) {
  APP.currentPeriod = period;
  document.querySelectorAll(".period-tab").forEach(t => {
    const active = t.dataset.period === period;
    t.classList.toggle("bg-blue-700", active);
    t.classList.toggle("text-white",  active);
    t.classList.toggle("text-gray-400", !active);
    if (active) t.classList.add("active"); else t.classList.remove("active");
  });

  const ticker = APP.currentTicker;
  if (!ticker) return;
  const cache = APP.tickerCache[ticker];

  let data = [];
  if (period === "TTM" && cache?.ttm) {
    data = [cache.ttm];
  } else if (cache?.history?.filings) {
    data = cache.history.filings.filter(f => f.period_type === period);
  }

  renderEpsChart(data, period);
}

// ─── EPS 推移グラフ ───────────────────────────────────────
function renderEpsChart(filings, period) {
  const sorted = [...filings].sort((a,b) =>
    (a.period_of_report || "").localeCompare(b.period_of_report || ""));
  const labels   = sorted.map(f => f.period_of_report?.slice(0,7) || "");
  const gaapData = sorted.map(f => f.gaap_eps ?? null);
  const adjData  = sorted.map(f => f.adjusted_eps ?? null);

  destroyChart("eps-chart");
  const ctx = document.getElementById("eps-chart")?.getContext("2d");
  if (!ctx) return;
  APP.charts["eps-chart"] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "GAAP EPS",  data: gaapData, borderColor: "#ef4444", backgroundColor: "rgba(239,68,68,.1)",  tension: 0.3, pointRadius: 4 },
        { label: "実質 EPS", data: adjData,  borderColor: "#22c55e", backgroundColor: "rgba(34,197,94,.15)", tension: 0.3, pointRadius: 4 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { labels: { color: "#9ca3af" } } },
      scales: {
        x: { ticks: { color: "#6b7280" }, grid: { color: "#374151" } },
        y: { ticks: { color: "#6b7280" }, grid: { color: "#374151" } },
      }
    }
  });
}

// ─── ウォーターフォールチャート ────────────────────────────
function renderWaterfallChart(filing) {
  destroyChart("waterfall-chart");
  const ctx = document.getElementById("waterfall-chart")?.getContext("2d");
  if (!ctx) return;

  const adjustments = filing.adjustments || [];
  const gaapEps     = filing.gaap_eps    || 0;

  // ウォーターフォールデータ生成
  const labels = ["GAAP EPS"];
  const starts = [0];          // 浮動棒の bottom
  const sizes  = [gaapEps];    // 浮動棒の size (height)
  const colors = [gaapEps >= 0 ? "#3b82f6" : "#ef4444"];

  let running = gaapEps;
  adjustments.forEach(adj => {
    const delta = (adj.net_amount || 0) * (adj.direction === "subtract" ? -1 : 1) / (filing.diluted_shares_used || 1);
    labels.push(adj.item_name || "調整");
    if (delta >= 0) {
      starts.push(running);
      sizes.push(delta);
      colors.push("#22c55e");
    } else {
      starts.push(running + delta);
      sizes.push(-delta);
      colors.push("#ef4444");
    }
    running += delta;
  });
  labels.push("実質 EPS");
  starts.push(0);
  sizes.push(running);
  colors.push(running >= 0 ? "#16a34a" : "#dc2626");

  APP.charts["waterfall-chart"] = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "EPS",
        data: sizes.map((s, i) => ({ x: labels[i], y: s })),
        backgroundColor: colors,
        // 浮動バーは Chart.js の floating bar で実装
        barPercentage: 0.6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const idx = ctx.dataIndex;
              const val = running && idx === labels.length - 1 ? running : (starts[idx] + sizes[idx]).toFixed(4);
              return `EPS: ${parseFloat(val).toFixed(4)}`;
            }
          }
        }
      },
      scales: {
        x: { ticks: { color: "#6b7280", maxRotation: 45 }, grid: { color: "#374151" } },
        y: { ticks: { color: "#6b7280" }, grid: { color: "#374151" } },
        // 浮動棒グラフ用に min を明示しない（Chart.js 4.x）
      }
    }
  });

  // 注: Chart.js 4.x では真のウォーターフォールには floating bars が必要
  // 上記はシンプル版。本格的には stacked bar + 透明バー overlay で実装
}

// ─── 調整内訳アコーディオン ───────────────────────────────
function renderAdjustmentsAccordion(adjustments) {
  const el = document.getElementById("adjustments-accordion");
  if (!adjustments.length) {
    el.innerHTML = `<p class="text-gray-500 text-sm p-3">調整項目なし（または未取得）</p>`;
    return;
  }

  // カテゴリ別グループ化
  const groups = {};
  adjustments.forEach(adj => {
    const cat = adj.category || "その他";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(adj);
  });

  el.innerHTML = Object.entries(groups).map(([cat, items], gi) => {
    const catTotal = items.reduce((s, a) => {
      const delta = (a.net_amount || 0);
      return s + (a.direction === "add_back" ? delta : -delta);
    }, 0);
    const rows = items.map(adj => `
      <tr>
        <td class="py-1 pr-3 text-gray-300 text-xs">
          <button class="text-left text-blue-400 hover:underline text-xs"
            onclick="showSnippet('${escHtml(adj.item_name)}', '${escHtml(adj.context_snippet||"N/A")}')">
            ${escHtml(adj.item_name)}
          </button>
        </td>
        <td class="text-gray-400 text-xs">${adj.direction === "add_back" ? "➕除外" : "➖差引"}</td>
        <td class="text-gray-400 text-xs">${fmtM(adj.amount)}</td>
        <td class="${(adj.net_amount||0) >= 0 ? 'text-green-400':'text-red-400'} text-xs font-mono">${fmtM(adj.net_amount)}</td>
        <td class="text-gray-500 text-xs">${confidenceBadge(adj.ai_confidence)}</td>
        <td class="text-gray-400 text-xs">${escHtml(adj.reason || "")}</td>
      </tr>`).join("");

    return `
    <div class="accordion-item mb-1">
      <h2 class="accordion-header">
        <button class="accordion-button collapsed py-2 px-3 text-sm" type="button"
          data-bs-toggle="collapse" data-bs-target="#cat-${gi}">
          <span class="font-semibold mr-3">${escHtml(cat)}</span>
          <span class="text-xs ${catTotal >= 0 ? 'text-green-400':'text-red-400'} ml-auto mr-2">
            ${catTotal >= 0 ? '+':''}${fmtM(catTotal)} (税後合計)
          </span>
        </button>
      </h2>
      <div id="cat-${gi}" class="accordion-collapse collapse">
        <div class="accordion-body p-3">
          <table class="w-full text-xs">
            <thead>
              <tr class="text-gray-500">
                <th class="text-left">項目 (📄=根拠)</th>
                <th>方向</th>
                <th>税前額</th>
                <th>税後額</th>
                <th>信頼度</th>
                <th>理由</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    </div>`;
  }).join("");
}

// ─── スニペットポップオーバー ─────────────────────────────
function showSnippet(itemName, snippet) {
  document.getElementById("snippet-item-name").textContent = itemName;
  document.getElementById("snippet-text").textContent = snippet;
  new bootstrap.Modal(document.getElementById("snippetModal")).show();
}

// ═══════════════════════════════════════════════════════════
// ④ 予測画面
// ═══════════════════════════════════════════════════════════
let _fcTimer = null;
function updateForecastChart() {
  clearTimeout(_fcTimer);
  _fcTimer = setTimeout(_doForecast, 300); // デバウンス 0.3s
}

function _doForecast() {
  const eps    = parseFloat(document.getElementById("fc-eps")?.value    || 0);
  const per    = parseFloat(document.getElementById("fc-per")?.value    || 25);
  const growth = parseFloat(document.getElementById("fc-growth")?.value || 20) / 100;
  const years  = parseInt(  document.getElementById("fc-years")?.value  || 5);

  if (!eps || eps <= 0) return;

  const labels = []; const epsList = []; const priceList = [];
  for (let y = 0; y <= years; y++) {
    const futureEps   = eps * Math.pow(1 + growth, y);
    const futurePrice = futureEps * per;
    labels.push(y === 0 ? "現在" : `+${y}年`);
    epsList.push(parseFloat(futureEps.toFixed(4)));
    priceList.push(parseFloat(futurePrice.toFixed(2)));
  }

  document.getElementById("fc-result").innerHTML =
    `<strong>${years}年後の予測:</strong> EPS ${epsList[years].toFixed(4)} USD
     → 理論株価 <span class="text-yellow-300 text-lg font-bold">$${priceList[years].toFixed(2)}</span>
     (PER ${per}× 想定)`;

  destroyChart("fc-chart");
  const ctx = document.getElementById("fc-chart")?.getContext("2d");
  if (!ctx) return;
  APP.charts["fc-chart"] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "理論株価 ($)", data: priceList, borderColor: "#f59e0b", backgroundColor: "rgba(245,158,11,.1)", yAxisID: "y1", tension: 0.3 },
        { label: "実質EPS",      data: epsList,   borderColor: "#22c55e", backgroundColor: "rgba(34,197,94,.1)",  yAxisID: "y2", tension: 0.3 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { labels: { color: "#9ca3af" } } },
      scales: {
        x:  { ticks: { color: "#6b7280" }, grid: { color: "#374151" } },
        y1: { position: "left",  ticks: { color: "#f59e0b" }, grid: { color: "#374151" }, title: { display: true, text: "株価 ($)", color: "#f59e0b" } },
        y2: { position: "right", ticks: { color: "#22c55e" }, grid: { drawOnChartArea: false }, title: { display: true, text: "EPS", color: "#22c55e" } },
      }
    }
  });
}

// ─── バリュエーション (個別分析画面 右サイド) ─────────────
let _valTimer = null;
function initValInputs() {
  ["val-eps","val-per","val-growth","val-years"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", () => {
      clearTimeout(_valTimer);
      _valTimer = setTimeout(updateValuation, 300);
    });
  });
}

function updateValuation() {
  const eps    = parseFloat(document.getElementById("val-eps")?.value    || 0);
  const per    = parseFloat(document.getElementById("val-per")?.value    || 25);
  const growth = parseFloat(document.getElementById("val-growth")?.value || 20) / 100;
  const years  = parseInt(  document.getElementById("val-years")?.value  || 3);

  if (!eps || eps <= 0) return;
  const futureEps   = eps * Math.pow(1 + growth, years);
  const futurePrice = futureEps * per;

  document.getElementById("val-result").innerHTML =
    `${years}年後の実質EPS: <strong>${futureEps.toFixed(4)}</strong>
     → 理論株価: <span class="text-yellow-300 font-bold text-lg">$${futurePrice.toFixed(2)}</span>`;

  // val-chart
  destroyChart("val-chart");
  const ctx = document.getElementById("val-chart")?.getContext("2d");
  if (!ctx) return;
  const labels = Array.from({length: years+1}, (_,i) => i === 0 ? "現在" : `+${i}年`);
  const prices = labels.map((_,i) => parseFloat((eps * Math.pow(1+growth,i) * per).toFixed(2)));
  APP.charts["val-chart"] = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "理論株価 ($)", data: prices, backgroundColor: "rgba(245,158,11,.7)" }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#6b7280" }, grid: { color: "#374151" } },
        y: { ticks: { color: "#6b7280", callback: v => `$${v}` }, grid: { color: "#374151" } },
      }
    }
  });
}

// ═══════════════════════════════════════════════════════════
// グローバル検索 (オートコンプリート)
// ═══════════════════════════════════════════════════════════
function initSearch() {
  const input    = document.getElementById("global-search");
  const dropdown = document.getElementById("search-dropdown");
  if (!input) return;

  input.addEventListener("input", () => {
    const q = input.value.trim().toUpperCase();
    if (!q || !APP.indexData) { dropdown.classList.add("hidden"); return; }
    const matches = (APP.indexData.tickers || []).filter(t =>
      t.ticker.includes(q)
    ).slice(0, 8);
    if (!matches.length) { dropdown.classList.add("hidden"); return; }
    dropdown.innerHTML = matches.map(t => `
      <div class="px-3 py-2 hover:bg-gray-700 cursor-pointer text-sm flex items-center gap-2"
           onclick="openDetailFor('${t.ticker}'); document.getElementById('global-search').value=''; document.getElementById('search-dropdown').classList.add('hidden');">
        <span class="font-semibold text-blue-400">${t.ticker}</span>
        ${healthBadge(t.health)}
        <span class="text-gray-400 text-xs ml-auto">EPS ${fmt(t.adjusted_eps)}</span>
      </div>`).join("");
    dropdown.classList.remove("hidden");
  });

  document.addEventListener("click", e => {
    if (!input.contains(e.target) && !dropdown.contains(e.target))
      dropdown.classList.add("hidden");
  });
}

// ═══════════════════════════════════════════════════════════
// テーマ切替
// ═══════════════════════════════════════════════════════════
function initTheme() {
  const stored = localStorage.getItem("theme") || "dark";
  applyTheme(stored);
}

function toggleTheme() {
  const isDark = document.documentElement.classList.contains("dark");
  applyTheme(isDark ? "light" : "dark");
}

function applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.classList.add("dark");
    document.getElementById("theme-toggle").textContent = "☀️ ライト";
  } else {
    document.documentElement.classList.remove("dark");
    document.getElementById("theme-toggle").textContent = "🌙 ダーク";
  }
  localStorage.setItem("theme", theme);
}

// ═══════════════════════════════════════════════════════════
// ユーティリティ
// ═══════════════════════════════════════════════════════════

// Tooltip 初期化
function initTooltips() {
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));
}

// EPS 数値フォーマット
function fmt(v) {
  if (v == null || isNaN(v)) return "—";
  return parseFloat(v).toFixed(4);
}

// 金額フォーマット (M/B 単位)
function fmtM(v) {
  if (v == null || isNaN(v)) return "—";
  const n = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (n >= 1e9) return `${sign}${(n/1e9).toFixed(2)}B`;
  if (n >= 1e6) return `${sign}${(n/1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${sign}${(n/1e3).toFixed(0)}K`;
  return `${sign}${n.toFixed(0)}`;
}

// 株式数フォーマット
function formatShares(v) {
  if (!v) return "—";
  return fmtM(v) + " 株";
}

// 健全性バッジ HTML
function healthBadge(health) {
  const label = healthLabel(health);
  return `<span class="inline-block text-xs px-2 py-0.5 rounded-full badge-${health||'Unknown'}">${label}</span>`;
}

function healthLabel(health) {
  return {
    Excellent: "✅ Excellent",
    Good:      "🟢 Good",
    Caution:   "⚠️ Caution",
    Warning:   "🔴 Warning",
    Error:     "❌ Error",
  }[health] || "— Unknown";
}

// 信頼度バッジ
function confidenceBadge(conf) {
  return conf === "high"
    ? `<span class="text-green-400">● 高</span>`
    : `<span class="text-yellow-500">○ 低</span>`;
}

// HTML エスケープ
function escHtml(s) {
  if (!s) return "";
  return String(s)
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;")
    .replace(/'/g,"&#039;");
}

// JSON フェッチ
async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Fetch failed: ${path} (${res.status})`);
  return res.json();
}

// Chart 破棄
function destroyChart(id) {
  if (APP.charts[id]) {
    APP.charts[id].destroy();
    delete APP.charts[id];
  }
}

// ローディング表示
function setLoading(show, msg = "読み込み中...") {
  const overlay = document.getElementById("loading-overlay");
  const msgEl   = document.getElementById("loading-msg");
  if (overlay) overlay.style.display = show ? "flex" : "none";
  if (msgEl)   msgEl.textContent = msg;
}

function hideLoading() { setLoading(false); }

// エラー表示
function showError(msg, err) {
  console.error(msg, err);
  alert(msg);
}
