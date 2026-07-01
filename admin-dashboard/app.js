// Cache elements
const els = {
  baseUrl: document.getElementById("baseUrl"),
  symbolSelect: document.getElementById("symbolSelect"),
  newsBySymbol: document.getElementById("newsBySymbol"),
  loadSymbolsBtn: document.getElementById("loadSymbolsBtn"),
  updatePriceBtn: document.getElementById("updatePriceBtn"),
  updateNewsBtn: document.getElementById("updateNewsBtn"),
  clearLogBtn: document.getElementById("clearLogBtn"),
  priceResult: document.getElementById("priceResult"),
  newsResult: document.getElementById("newsResult"),
  priceStatus: document.getElementById("priceStatus"),
  newsStatus: document.getElementById("newsStatus"),
  actionLog: document.getElementById("actionLog"),

  // Tabs
  tabDataBtn: document.getElementById("tab-data-btn"),
  tabBacktestBtn: document.getElementById("tab-backtest-btn"),
  dataTabContent: document.getElementById("data-tab-content"),
  backtestTabContent: document.getElementById("backtest-tab-content"),

  // Backtest Inputs
  backtestForm: document.getElementById("backtestForm"),
  backtestSymbol: document.getElementById("backtestSymbol"),
  vn30Option: document.getElementById("vn30Option"),
  startDate: document.getElementById("startDate"),
  endDate: document.getElementById("endDate"),
  marketSymbol: document.getElementById("marketSymbol"),
  minSignalScore: document.getElementById("minSignalScore"),
  maxHoldCandles: document.getElementById("maxHoldCandles"),
  transCost: document.getElementById("transCost"),
  lookbackDays: document.getElementById("lookbackDays"),
  useIntraday: document.getElementById("useIntraday"),
  exitOnScoreDrop: document.getElementById("exitOnScoreDrop"),
  runBacktestBtn: document.getElementById("runBacktestBtn"),

  // Mode + data selection
  backtestModeControl: document.getElementById("backtestModeControl"),
  dataSelectionPanel: document.getElementById("dataSelectionPanel"),
  dsNews: document.getElementById("dsNews"),
  dsTechCount: document.getElementById("dsTechCount"),
  dsFundCount: document.getElementById("dsFundCount"),

  // Drag and Drop
  dragDropZone: document.getElementById("dragDropZone"),
  jsonFilePicker: document.getElementById("jsonFilePicker"),

  // Progress and results (VN30)
  vn30ProgressCard: document.getElementById("vn30ProgressCard"),
  vn30Status: document.getElementById("vn30Status"),
  vn30ProgressBar: document.getElementById("vn30ProgressBar"),
  vn30Logs: document.getElementById("vn30Logs"),
  vn30ResultsCard: document.getElementById("vn30ResultsCard"),
  vn30ResultsBody: document.getElementById("vn30ResultsBody"),
  exportVn30CsvBtn: document.getElementById("exportVn30CsvBtn"),

  // Viz Wrapper
  vizWrapper: document.getElementById("vizWrapper"),
  statNetProfit: document.getElementById("statNetProfit"),
  statWinRate: document.getElementById("statWinRate"),
  statTotalTrades: document.getElementById("statTotalTrades"),
  statSharpe: document.getElementById("statSharpe"),
  vizSymbol: document.getElementById("vizSymbol"),
  chartLegend: document.getElementById("chartLegend"),
  priceChart: document.getElementById("priceChart"),
  rsiChart: document.getElementById("rsiChart"),
  macdChart: document.getElementById("macdChart"),
  tradeLogsBody: document.getElementById("tradeLogsBody"),
  tradeDetailPanel: document.getElementById("tradeDetailPanel"),
  detailIndex: document.getElementById("detailIndex"),
  detailEntryDate: document.getElementById("detailEntryDate"),
  detailExitDate: document.getElementById("detailExitDate"),
  detailEntryPrice: document.getElementById("detailEntryPrice"),
  detailExitPrice: document.getElementById("detailExitPrice"),
  detailTP: document.getElementById("detailTP"),
  detailSL: document.getElementById("detailSL"),
  detailConfidence: document.getElementById("detailConfidence"),
  detailExitReason: document.getElementById("detailExitReason"),
  cloudHistoryList: document.getElementById("cloudHistoryList"),
  refreshCloudHistoryBtn: document.getElementById("refreshCloudHistoryBtn"),

  // Comparison (Full vs Baseline) + Agent report
  comparisonCard: document.getElementById("comparisonCard"),
  comparisonBody: document.getElementById("comparisonBody"),
  agentReportCard: document.getElementById("agentReportCard"),
  agentReportCount: document.getElementById("agentReportCount"),
  agentReportList: document.getElementById("agentReportList"),
  agentReportDetail: document.getElementById("agentReportDetail"),

  // Admin auth
  adminAuthBadge: document.getElementById("adminAuthBadge"),

  // Analyze tab
  tabAnalyzeBtn: document.getElementById("tab-analyze-btn"),
  analyzeTabContent: document.getElementById("analyze-tab-content"),
  analyzeForm: document.getElementById("analyzeForm"),
  analyzeSourceControl: document.getElementById("analyzeSourceControl"),
  analyzeSymbolField: document.getElementById("analyzeSymbolField"),
  analyzeSymbol: document.getElementById("analyzeSymbol"),
  analyzeRiskPeriod: document.getElementById("analyzeRiskPeriod"),
  analyzeModeControl: document.getElementById("analyzeModeControl"),
  analyzeDataSelectionPanel: document.getElementById("analyzeDataSelectionPanel"),
  anNews: document.getElementById("anNews"),
  anTechCount: document.getElementById("anTechCount"),
  anFundCount: document.getElementById("anFundCount"),
  runAnalyzeBtn: document.getElementById("runAnalyzeBtn"),
  analyzeProgressCard: document.getElementById("analyzeProgressCard"),
  analyzeStatus: document.getElementById("analyzeStatus"),
  analyzeProgressBar: document.getElementById("analyzeProgressBar"),
  analyzeLogs: document.getElementById("analyzeLogs"),
  analyzeSingleResult: document.getElementById("analyzeSingleResult"),
  analyzeResultsCard: document.getElementById("analyzeResultsCard"),
  analyzeUniverseName: document.getElementById("analyzeUniverseName"),
  analyzeResultsBody: document.getElementById("analyzeResultsBody"),
  analyzeDetailPanel: document.getElementById("analyzeDetailPanel"),
  exportAnalyzeCsvBtn: document.getElementById("exportAnalyzeCsvBtn"),
};

// Admin auth token obtained via POST /api/auth/admin-login
let adminToken = null;
let analyzeSummaryData = [];

let symbolsLoaded = false;
let vn30SummaryData = []; // Store stats for CSV export

// 30 Tickers in VN30 Index Basket
const VN30_TICKERS = [
  "ACB", "BID", "CTG", "DGC", "FPT", "GAS", "GVR", "HDB", "HPG", "LPB",
  "MBB", "MSN", "MWG", "PLX", "SAB", "SHB", "SSB", "SSI", "STB", "TCB",
  "TPB", "VCB", "VJC", "VHM", "VIC", "VNM", "VPB", "VRE", "VIB", "VPL"
];

// Active Chart Instances (for window resize cleanup or updates)
let charts = {
  price: null,
  rsi: null,
  macd: null,
  candlestickSeries: null,
  tpSLSeries: [] // Keep references to cleanup TP/SL lines
};

// Utilities
function normalizeBaseUrl(raw) {
  return (raw || "").trim().replace(/\/+$/, "");
}

function now() {
  return new Date().toLocaleString("vi-VN");
}

function appendLog(message) {
  const li = document.createElement("li");
  li.textContent = `[${now()}] ${message}`;
  els.actionLog.prepend(li);

  while (els.actionLog.children.length > 50) {
    els.actionLog.removeChild(els.actionLog.lastChild);
  }
}

function setStatus(statusEl, type, text) {
  statusEl.classList.remove("ok", "error", "running");
  if (type) {
    statusEl.classList.add(type);
  }
  statusEl.textContent = text;
}

function formatJson(payload) {
  try {
    return JSON.stringify(payload, null, 2);
  } catch {
    return String(payload);
  }
}

function setResult(preEl, payload) {
  preEl.textContent = formatJson(payload);
}

function getSelectedSymbol() {
  return (els.symbolSelect.value || "").trim().toUpperCase();
}

function parseSymbolList(payload) {
  if (!payload || !Array.isArray(payload.data)) {
    return [];
  }
  return payload.data
    .map((item) => {
      if (typeof item === "string") {
        return item.trim().toUpperCase();
      }
      if (item && typeof item === "object" && typeof item.symbol === "string") {
        return item.symbol.trim().toUpperCase();
      }
      return "";
    })
    .filter(Boolean);
}

async function requestJson(url, options = {}, _isRetry = false) {
  const response = await fetch(url, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(adminToken ? { Authorization: `Bearer ${adminToken}` } : {}),
      ...(options.headers || {}),
    },
    ...(options.body ? { body: JSON.stringify(options.body) } : {}),
  });

  // Access token expired/revoked → re-login once and retry transparently.
  if (response.status === 401 && !_isRetry) {
    const ok = await adminLogin();
    if (ok) {
      return requestJson(url, options, true);
    }
  }

  let body;
  try {
    body = await response.json();
  } catch {
    body = { error: "Response is not valid JSON" };
  }

  if (!response.ok) {
    const message = body?.errorDesc || body?.detail || response.statusText;
    throw new Error(`HTTP ${response.status}: ${message}`);
  }

  return body;
}

// ─────────────────────────────────────────────────────────────────────────────
// ADMIN AUTO-LOGIN
// ─────────────────────────────────────────────────────────────────────────────
function setAdminAuthBadge(type, text) {
  if (!els.adminAuthBadge) return;
  els.adminAuthBadge.classList.remove("ok", "error", "running");
  if (type) els.adminAuthBadge.classList.add(type);
  els.adminAuthBadge.textContent = text;
}

async function adminLogin() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  if (!baseUrl) return false;

  setAdminAuthBadge("running", "Đang đăng nhập admin...");
  try {
    // Send without the (possibly stale) Authorization header.
    const response = await fetch(`${baseUrl}/api/auth/admin-login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
    });
    const payload = await response.json();

    if (response.ok && payload?.result && payload?.data?.token) {
      adminToken = payload.data.token;
      setAdminAuthBadge("ok", "Admin đã đăng nhập");
      appendLog("Đăng nhập admin thành công.");
      return true;
    }

    adminToken = null;
    const msg = payload?.errorDesc || response.statusText;
    setAdminAuthBadge("error", "Đăng nhập admin lỗi");
    appendLog(`Đăng nhập admin thất bại: ${msg}`);
    return false;
  } catch (error) {
    adminToken = null;
    setAdminAuthBadge("error", "Đăng nhập admin lỗi");
    appendLog(`Lỗi đăng nhập admin: ${error.message}`);
    return false;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DATA TAB ACTIONS
// ─────────────────────────────────────────────────────────────────────────────
async function loadSymbols() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  if (!baseUrl) {
    appendLog("Không thể tải mã: API Base URL đang trống.");
    return;
  }

  els.loadSymbolsBtn.disabled = true;
  setStatus(els.priceStatus, "running", "Đang tải mã...");

  try {
    const payload = await requestJson(`${baseUrl}/api/all-symbol`);
    const symbols = parseSymbolList(payload);

    els.symbolSelect.innerHTML = "";
    if (symbols.length === 0) {
      const empty = document.createElement("option");
      empty.value = "";
      empty.textContent = "-- Không có mã cổ phiếu --";
      els.symbolSelect.appendChild(empty);
      symbolsLoaded = false;
      appendLog("Tải danh sách mã thành công nhưng không có dữ liệu.");
    } else {
      for (const symbol of symbols) {
        const option = document.createElement("option");
        option.value = symbol;
        option.textContent = symbol;
        els.symbolSelect.appendChild(option);
      }
      symbolsLoaded = true;
      appendLog(`Đã tải ${symbols.length} mã cổ phiếu.`);
    }

    setStatus(els.priceStatus, "ok", "Tải mã xong");
  } catch (error) {
    setStatus(els.priceStatus, "error", "Lỗi tải mã");
    appendLog(`Lỗi tải danh sách mã: ${error.message}`);
  } finally {
    els.loadSymbolsBtn.disabled = false;
  }
}

async function updatePrice() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  const symbol = getSelectedSymbol();

  if (!baseUrl) {
    appendLog("Không thể cập nhật giá: API Base URL đang trống.");
    return;
  }
  if (!symbol) {
    appendLog("Bạn cần chọn mã cổ phiếu trước khi cập nhật giá.");
    return;
  }

  els.updatePriceBtn.disabled = true;
  setStatus(els.priceStatus, "running", "Đang cập nhật...");
  appendLog(`Gửi POST /api/price/${symbol}`);

  try {
    const payload = await requestJson(`${baseUrl}/api/price/${encodeURIComponent(symbol)}`, {
      method: "POST",
    });

    setResult(els.priceResult, payload);

    const ok = payload?.result === true || payload?.errorCode === 0;
    setStatus(els.priceStatus, ok ? "ok" : "error", ok ? "Thành công" : "Có lỗi");
    appendLog(`Cập nhật giá cho ${symbol}: ${ok ? "thành công" : "thất bại"}.`);
  } catch (error) {
    setStatus(els.priceStatus, "error", "Lỗi API");
    setResult(els.priceResult, { error: error.message });
    appendLog(`Lỗi cập nhật giá ${symbol}: ${error.message}`);
  } finally {
    els.updatePriceBtn.disabled = false;
  }
}

async function updateNews() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  const symbol = getSelectedSymbol();
  const bySymbol = els.newsBySymbol.checked;

  if (!baseUrl) {
    appendLog("Không thể cập nhật tin tức: API Base URL đang trống.");
    return;
  }

  const endpoint = bySymbol && symbol
    ? `${baseUrl}/api/articles/update?symbol=${encodeURIComponent(symbol)}`
    : `${baseUrl}/api/articles/update`;

  if (bySymbol && !symbol) {
    appendLog("Không có mã được chọn, hệ thống sẽ cập nhật tin tức toàn thị trường.");
  }

  els.updateNewsBtn.disabled = true;
  setStatus(els.newsStatus, "running", "Đang cập nhật...");
  appendLog(`Gửi POST ${endpoint.replace(baseUrl, "")}`);

  try {
    const payload = await requestJson(endpoint, {
      method: "POST",
    });

    setResult(els.newsResult, payload);

    const ok = payload?.result === true || payload?.errorCode === 0;
    setStatus(els.newsStatus, ok ? "ok" : "error", ok ? "Thành công" : "Có lỗi");
    appendLog(`Cập nhật tin tức: ${ok ? "thành công" : "thất bại"}.`);
  } catch (error) {
    setStatus(els.newsStatus, "error", "Lỗi API");
    setResult(els.newsResult, { error: error.message });
    appendLog(`Lỗi cập nhật tin tức: ${error.message}`);
  } finally {
    els.updateNewsBtn.disabled = false;
  }
}

function clearLog() {
  els.actionLog.innerHTML = "";
  appendLog("Đã xóa lịch sử log.");
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB SWITCHING
// ─────────────────────────────────────────────────────────────────────────────
function initTabs() {
  const tabs = [
    { btn: els.tabDataBtn, content: els.dataTabContent },
    { btn: els.tabBacktestBtn, content: els.backtestTabContent },
    { btn: els.tabAnalyzeBtn, content: els.analyzeTabContent },
  ];

  tabs.forEach(({ btn, content }) => {
    if (!btn || !content) return;
    btn.addEventListener("click", () => {
      tabs.forEach((t) => {
        if (!t.btn || !t.content) return;
        const active = t.btn === btn;
        t.btn.classList.toggle("active", active);
        t.content.style.display = active ? "block" : "none";
      });
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// BACKTEST EXECUTION CONTROLLER
// ─────────────────────────────────────────────────────────────────────────────
const DS_TECH_KEYS = ["ma", "boll", "rsi", "macd", "kdj"];
const DS_FUND_KEYS = ["liquidity", "leverage", "efficiency", "profitability", "valuation"];

function getBacktestMode() {
  const activeBtn = els.backtestModeControl?.querySelector(".seg-btn.active");
  return activeBtn ? activeBtn.dataset.mode : "auto";
}

function readChecks(selector, keys) {
  const result = {};
  keys.forEach((k) => {
    const el = document.querySelector(`${selector}[value="${k}"]`);
    result[k] = el ? el.checked : true;
  });
  return result;
}

function getDataSelection() {
  return {
    news: els.dsNews ? els.dsNews.checked : true,
    technical: readChecks(".ds-tech", DS_TECH_KEYS),
    fundamental: readChecks(".ds-fund", DS_FUND_KEYS),
  };
}

function getBacktestParams(symbolOverride = null) {
  return {
    symbol: symbolOverride || els.backtestSymbol.value.trim().toUpperCase() || "FPT",
    start_date: els.startDate.value || null,
    end_date: els.endDate.value || null,
    market_symbol: els.marketSymbol.value.trim().toUpperCase() || "VNINDEX",
    min_signal_score: parseInt(els.minSignalScore.value) || 3,
    max_hold_candles: parseInt(els.maxHoldCandles.value) || 20,
    transaction_cost_pct: parseFloat(els.transCost.value) || 0.0015,
    one_minute_lookback_days: parseInt(els.lookbackDays.value) || 30,
    use_intraday: els.useIntraday.checked,
    exit_on_score_drop: els.exitOnScoreDrop.checked,
    mode: getBacktestMode(),
    data_selection: getDataSelection(),
  };
}

function updateDsCounts() {
  const techOn = DS_TECH_KEYS.filter((k) => document.querySelector(`.ds-tech[value="${k}"]`)?.checked).length;
  const fundOn = DS_FUND_KEYS.filter((k) => document.querySelector(`.ds-fund[value="${k}"]`)?.checked).length;
  if (els.dsTechCount) els.dsTechCount.textContent = `${techOn}/${DS_TECH_KEYS.length}`;
  if (els.dsFundCount) els.dsFundCount.textContent = `${fundOn}/${DS_FUND_KEYS.length}`;
}

function initDataSelectionControls() {
  if (!els.backtestModeControl) return;

  els.backtestModeControl.querySelectorAll(".seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      els.backtestModeControl.querySelectorAll(".seg-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const isManual = btn.dataset.mode === "manual";
      if (els.dataSelectionPanel) {
        els.dataSelectionPanel.style.display = isManual ? "flex" : "none";
      }
    });
  });

  document.querySelectorAll(".ds-tech, .ds-fund").forEach((cb) => {
    cb.addEventListener("change", updateDsCounts);
  });
  updateDsCounts();
}

async function runBacktest() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  if (!baseUrl) {
    alert("Không thể chạy backtest: API Base URL đang trống.");
    return;
  }

  const runVn30 = els.vn30Option.checked;
  els.runBacktestBtn.disabled = true;

  if (!runVn30) {
    // SINGLE ticker run
    const params = getBacktestParams();
    if (!params.symbol) {
      alert("Vui lòng điền mã cổ phiếu.");
      els.runBacktestBtn.disabled = false;
      return;
    }

    appendLog(`Chạy backtest cho ${params.symbol}...`);
    els.runBacktestBtn.textContent = `Đang chạy backtest ${params.symbol}...`;
    els.vizWrapper.style.display = "none";
    els.vn30ProgressCard.style.display = "none";
    els.vn30ResultsCard.style.display = "none";

    try {
      const payload = await requestJson(`${baseUrl}/api/agentic/backtest`, {
        method: "POST",
        body: params,
      });

      appendLog(`Backtest cho ${params.symbol} hoàn thành!`);
      const data = payload?.data;
      if (data?.visualization_data) {
        renderVisualization(data.visualization_data);
      } else {
        alert("Không nhận được dữ liệu vẽ biểu đồ từ backend.");
      }
      loadCloudHistory();
    } catch (error) {
      appendLog(`Lỗi chạy backtest ${params.symbol}: ${error.message}`);
      alert(`Lỗi chạy backtest: ${error.message}`);
    } finally {
      els.runBacktestBtn.disabled = false;
      els.runBacktestBtn.textContent = "Chạy Backtest Pipeline";
    }
  } else {
    // VN30 BATCH run
    els.runBacktestBtn.textContent = "Đang chạy VN30 Batch...";
    els.vizWrapper.style.display = "none";
    els.vn30ProgressCard.style.display = "block";
    els.vn30ResultsCard.style.display = "block";

    els.vn30Logs.textContent = "";
    els.vn30ResultsBody.innerHTML = "";
    vn30SummaryData = [];
    updateProgressBar(0, 30);

    appendLog("Bắt đầu chạy backtest tuần tự rổ VN30 (30 mã)...");

    let completedCount = 0;
    for (let i = 0; i < VN30_TICKERS.length; i++) {
      const ticker = VN30_TICKERS[i];
      updateProgressBar(i, VN30_TICKERS.length, `Đang xử lý ${ticker} (${i + 1}/${VN30_TICKERS.length})...`);

      const params = getBacktestParams(ticker);
      appendVn30Log(`[${i + 1}/30] Khởi động chạy backtest cho ${ticker}...`);

      try {
        const payload = await requestJson(`${baseUrl}/api/agentic/backtest`, {
          method: "POST",
          body: params,
        });

        const data = payload?.data;
        if (data) {
          const metrics = data.full_metrics || {};
          const pnl = metrics.pnl?.total_return !== undefined ? (metrics.pnl.total_return * 100).toFixed(1) + "%" : "0%";
          const winRate = metrics.volume?.win_rate !== undefined ? (metrics.volume.win_rate * 100).toFixed(1) + "%" : "0%";
          const tradesCount = metrics.volume?.n_trades !== undefined ? metrics.volume.n_trades : 0;
          const sharpe = metrics.risk?.sharpe_ratio !== undefined ? metrics.risk.sharpe_ratio.toFixed(2) : "0.00";
          const vizData = data.visualization_data;

          appendVn30Log(`✅ ${ticker} thành công: Lợi nhuận ${pnl}, Sharpe ${sharpe}, Tổng giao dịch ${tradesCount}.`);

          vn30SummaryData.push({
            ticker,
            pnl,
            winRate,
            tradesCount,
            sharpe,
            status: "OK",
            vizData
          });

          addVn30TableRow(ticker, pnl, winRate, tradesCount, sharpe, "OK", vizData);
        } else {
          throw new Error("Dữ liệu rỗng");
        }
      } catch (err) {
        appendVn30Log(`❌ ${ticker} thất bại: ${err.message}`);

        vn30SummaryData.push({
          ticker,
          pnl: "N/A",
          winRate: "N/A",
          tradesCount: "N/A",
          sharpe: "N/A",
          status: "Lỗi",
          vizData: null
        });

        addVn30TableRow(ticker, "N/A", "N/A", "N/A", "N/A", "Lỗi", null, err.message);
      }

      completedCount++;
      updateProgressBar(completedCount, VN30_TICKERS.length, `Đang chạy: ${completedCount}/${VN30_TICKERS.length}`);

      // Delay briefly between sequential API calls to prevent blocking
      await new Promise(resolve => setTimeout(resolve, 300));
    }

    appendVn30Log("🎉 Đã hoàn thành toàn bộ 30 mã VN30!");
    updateProgressBar(30, 30, "Hoàn tất rổ VN30");
    appendLog("Chạy batch VN30 hoàn tất.");
    loadCloudHistory();
    els.runBacktestBtn.disabled = false;
    els.runBacktestBtn.textContent = "Chạy Backtest Pipeline";
  }
}

function updateProgressBar(current, total, label = "") {
  const percent = Math.round((current / total) * 100);
  els.vn30ProgressBar.style.width = `${percent}%`;
  els.vn30Status.textContent = label || `Đang chạy ${current}/${total} (${percent}%)`;
  if (percent === 100) {
    els.vn30Status.classList.remove("running");
    els.vn30Status.classList.add("ok");
  } else {
    els.vn30Status.classList.remove("ok");
    els.vn30Status.classList.add("running");
  }
}

function appendVn30Log(msg) {
  els.vn30Logs.textContent += `[${new Date().toLocaleTimeString("vi-VN")}] ${msg}\n`;
  els.vn30Logs.scrollTop = els.vn30Logs.scrollHeight;
}

function addVn30TableRow(ticker, pnl, winRate, trades, sharpe, status, vizData, errMsg = "") {
  const tr = document.createElement("tr");
  const pnlNum = parseFloat(pnl);
  const pnlClass = isNaN(pnlNum) ? "" : (pnlNum >= 0 ? "text-green font-semibold" : "text-red font-semibold");
  const statusClass = status === "OK" ? "badge ok" : "badge error";

  tr.innerHTML = `
    <td><strong>${ticker}</strong></td>
    <td class="${pnlClass}">${pnl}</td>
    <td>${winRate}</td>
    <td>${trades}</td>
    <td>${sharpe}</td>
    <td><span class="${statusClass}" title="${errMsg}">${status}</span></td>
    <td style="text-align: center;">
      <button class="btn btn-ghost btn-view-vn30-viz" type="button" style="padding: 4px 10px; font-size: 0.75rem;" ${status === "OK" ? "" : "disabled"}>Xem</button>
    </td>
  `;

  if (status === "OK" && vizData) {
    tr.querySelector(".btn-view-vn30-viz").addEventListener("click", () => {
      renderVisualization(vizData);
    });
  }

  els.vn30ResultsBody.appendChild(tr);
}

function exportVn30Csv() {
  if (vn30SummaryData.length === 0) return;

  let csvContent = "data:text/csv;charset=utf-8,Symbol,Net Profit,Win Rate,Total Trades,Sharpe Ratio,Status\n";
  vn30SummaryData.forEach(row => {
    csvContent += `${row.ticker},${row.pnl.replace("%", "")},${row.winRate.replace("%", "")},${row.tradesCount},${row.sharpe},${row.status}\n`;
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `VN30_Backtest_Summary_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ─────────────────────────────────────────────────────────────────────────────
// DRAG & DROP / FILE UPLOADER
// ─────────────────────────────────────────────────────────────────────────────
function initDragDrop() {
  const zone = els.dragDropZone;

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("hover");
  });

  zone.addEventListener("dragleave", () => {
    zone.classList.remove("hover");
  });

  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("hover");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processBacktestJsonFile(files[0]);
    }
  });

  els.jsonFilePicker.addEventListener("change", (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      processBacktestJsonFile(files[0]);
    }
  });
}

function processBacktestJsonFile(file) {
  if (!file.name.endsWith(".json")) {
    alert("Vui lòng tải lên file định dạng JSON (.json)");
    return;
  }

  appendLog(`Đang xử lý file tải lên: ${file.name}...`);
  const reader = new FileReader();

  reader.onload = (e) => {
    try {
      const parsedData = JSON.parse(e.target.result);

      // Basic structure validation
      if (!parsedData.symbol || !parsedData.ohlc_data || !parsedData.trades || !parsedData.metrics) {
        throw new Error("Cấu trúc file JSON không khớp với chuẩn dữ liệu Visualization.");
      }

      appendLog(`Đọc file thành công. Hiển thị biểu đồ ${parsedData.symbol}...`);
      renderVisualization(parsedData);
    } catch (err) {
      appendLog(`Lỗi giải mã JSON: ${err.message}`);
      alert(`Không thể đọc file JSON: ${err.message}`);
    }
  };

  reader.onerror = () => {
    appendLog("Lỗi đọc file từ thiết bị.");
    alert("Lỗi đọc file.");
  };

  reader.readAsText(file);
}

// ─────────────────────────────────────────────────────────────────────────────
// CLOUD BACKTEST HISTORY LOADER (SUPABASE STORAGE)
// ─────────────────────────────────────────────────────────────────────────────
// Derive a sortable timestamp for a cloud history file.
// Filename format: {symbol}_{YYYYMMDD}_{HHMMSS}_backtest.json
function cloudHistorySortKey(file) {
  const parts = (file.name || "").split("_");
  const datePart = parts[1] || "";
  const timePart = parts[2] || "";
  if (datePart.length === 8 && timePart.length === 6) {
    const iso = `${datePart.slice(0, 4)}-${datePart.slice(4, 6)}-${datePart.slice(6, 8)}T` +
                `${timePart.slice(0, 2)}:${timePart.slice(2, 4)}:${timePart.slice(4, 6)}`;
    const t = new Date(iso).getTime();
    if (!isNaN(t)) return t;
  }
  return file.created_at ? new Date(file.created_at).getTime() : 0;
}

async function loadCloudHistory() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  if (!baseUrl) return;

  els.cloudHistoryList.innerHTML = '<p class="hint">Đang tải lịch sử...</p>';

  try {
    const payload = await requestJson(`${baseUrl}/api/agentic/backtests`);

    if (payload && payload.result && Array.isArray(payload.data)) {
      els.cloudHistoryList.innerHTML = "";
      const files = [...payload.data].sort((a, b) => cloudHistorySortKey(b) - cloudHistorySortKey(a));

      if (files.length === 0) {
        els.cloudHistoryList.innerHTML = '<p class="hint">Không có lịch sử backtest trên cloud.</p>';
        return;
      }
      
      files.forEach((file) => {
        const item = document.createElement("div");
        item.className = "cloud-history-item";
        
        const parts = file.name.split("_");
        const symbol = parts[0] || "Unknown";
        const datePart = parts[1] || "";
        const timePart = parts[2] || "";
        let dateStr = "";
        if (datePart.length === 8 && timePart.length === 6) {
          dateStr = `${datePart.slice(6, 8)}/${datePart.slice(4, 6)}/${datePart.slice(0, 4)} ` +
                    `${timePart.slice(0, 2)}:${timePart.slice(2, 4)}:${timePart.slice(4, 6)}`;
        } else {
          dateStr = file.created_at ? new Date(file.created_at).toLocaleString("vi-VN") : file.name;
        }

        item.innerHTML = `
          <div class="cloud-history-info">
            <span class="cloud-history-title">${symbol}</span>
            <span class="cloud-history-date">${dateStr}</span>
          </div>
          <button class="btn btn-secondary btn-view-cloud" type="button" style="padding: 4px 10px; font-size: 0.75rem;">
            Xem
          </button>
        `;
        
        item.querySelector(".btn-view-cloud").addEventListener("click", async () => {
          appendLog(`Đang tải dữ liệu backtest ${file.name} từ Cloud...`);
          try {
            const dataResponse = await fetch(file.json_url);
            if (!dataResponse.ok) {
              throw new Error(`HTTP error ${dataResponse.status}`);
            }
            const vizData = await dataResponse.json();
            
            if (!vizData.symbol || !vizData.ohlc_data || !vizData.trades || !vizData.metrics) {
              throw new Error("Cấu trúc file JSON không khớp với chuẩn dữ liệu Visualization.");
            }
            
            appendLog(`Đọc dữ liệu Cloud thành công. Hiển thị biểu đồ ${vizData.symbol}...`);
            renderVisualization(vizData);
          } catch (err) {
            appendLog(`Lỗi tải dữ liệu Cloud: ${err.message}`);
            alert(`Lỗi tải dữ liệu Cloud: ${err.message}`);
          }
        });
        
        els.cloudHistoryList.appendChild(item);
      });
    } else {
      els.cloudHistoryList.innerHTML = '<p class="hint text-red">Lỗi định dạng dữ liệu trả về.</p>';
    }
  } catch (err) {
    els.cloudHistoryList.innerHTML = `<p class="hint text-red">Lỗi tải lịch sử: ${err.message}</p>`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// LIGHTWEIGHT CHARTS VISUALIZATION RENDERER
// ─────────────────────────────────────────────────────────────────────────────
async function renderVisualization(vizData) {
  // 1. Show panel & scroll to view
  els.vizWrapper.style.display = "block";
  els.vizWrapper.scrollIntoView({ behavior: "smooth" });

  // 2. Set Stats Summary
  const netProfit = (vizData.metrics.pnl.total_return * 100);
  els.statNetProfit.innerText = netProfit.toFixed(1) + "%";
  els.statNetProfit.className = "stat-value " + (netProfit >= 0 ? "text-green" : "text-red");

  els.statWinRate.innerText = (vizData.metrics.volume.win_rate * 100).toFixed(1) + "%";
  els.statTotalTrades.innerText = vizData.metrics.volume.n_trades;
  els.statSharpe.innerText = vizData.metrics.risk.sharpe_ratio.toFixed(2);
  els.vizSymbol.innerText = vizData.symbol;

  // 2b. Comparison table (Full vs Baseline) + Agent report panel
  renderComparison(vizData);
  renderAgentReports(vizData);

  // 3. Clear existing charts divs (destroys old graphs completely)
  els.priceChart.innerHTML = "";
  els.rsiChart.innerHTML = "";
  els.macdChart.innerHTML = "";
  els.tradeDetailPanel.style.display = "none";
  charts.tpSLSeries.forEach(s => {
    try { s.setData([]); } catch (e) { }
  });
  charts.tpSLSeries = [];

  // SAU - lấy sau khi vizWrapper đã visible
  els.vizWrapper.style.display = "block";
  els.vizWrapper.scrollIntoView({ behavior: "smooth" });

  // Thêm dòng này để đảm bảo browser đã render layout
  await new Promise(resolve => requestAnimationFrame(resolve));
  const containerWidth = els.priceChart.clientWidth || els.priceChart.offsetWidth || 600;
  const subContainerWidth = els.rsiChart.clientWidth || els.rsiChart.offsetWidth || (containerWidth / 2 - 8);

  // 4. Initialize Price Chart
  const priceChart = LightweightCharts.createChart(els.priceChart, {
    width: containerWidth,
    height: 450,
    layout: {
      backgroundColor: "#0f172a",
      textColor: "#94a3b8",
      fontFamily: "'Outfit', sans-serif",
    },
    grid: {
      vertLines: { color: "rgba(30, 41, 59, 0.5)" },
      horzLines: { color: "rgba(30, 41, 59, 0.5)" },
    },
    crosshair: { mode: 0 },
    rightPriceScale: { borderColor: "rgba(51, 65, 85, 0.5)" },
    timeScale: {
      borderColor: "rgba(51, 65, 85, 0.5)",
      timeVisible: true,
    },
  });

  const candlestickSeries = priceChart.addCandlestickSeries({
    upColor: "#10b981",
    downColor: "#ef4444",
    borderVisible: false,
    wickUpColor: "#10b981",
    wickDownColor: "#ef4444",
  });
  candlestickSeries.setData(vizData.ohlc_data);

  // Volume Overlay Series
  const volumeSeries = priceChart.addHistogramSeries({
    color: "#26a69a",
    priceFormat: { type: "volume" },
    priceScaleId: "", // Overlay
  });
  volumeSeries.priceScale().applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 },
  });
  volumeSeries.setData(vizData.volume_data);

  // Indicators: SMA 20
  const sma20Series = priceChart.addLineSeries({
    color: "#3b82f6",
    lineWidth: 1.5,
    title: "SMA 20",
  });
  sma20Series.setData(vizData.sma20_data);

  // Indicators: SMA 50
  const sma50Series = priceChart.addLineSeries({
    color: "#f59e0b",
    lineWidth: 1.5,
    title: "SMA 50",
  });
  sma50Series.setData(vizData.sma50_data);

  // 5. Initialize RSI Subchart
  const rsiChart = LightweightCharts.createChart(els.rsiChart, {
    width: subContainerWidth,
    height: 180,
    layout: {
      backgroundColor: "#0f172a",
      textColor: "#94a3b8",
      fontFamily: "'Outfit', sans-serif",
    },
    grid: {
      vertLines: { color: "rgba(30, 41, 59, 0.5)" },
      horzLines: { color: "rgba(30, 41, 59, 0.5)" },
    },
    rightPriceScale: { borderColor: "rgba(51, 65, 85, 0.5)" },
    timeScale: { borderColor: "rgba(51, 65, 85, 0.5)" },
  });

  const rsiSeries = rsiChart.addLineSeries({
    color: "#a855f7",
    lineWidth: 1.5,
  });
  rsiSeries.setData(vizData.rsi_data);

  // Add RSI standard thresholds (30 / 70)
  const rsiUpper = rsiChart.addLineSeries({
    color: "rgba(168, 85, 247, 0.25)",
    lineWidth: 1,
    lineStyle: 1, // Dashed
  });
  rsiUpper.setData(vizData.rsi_data.map(d => ({ time: d.time, value: 70 })));

  const rsiLower = rsiChart.addLineSeries({
    color: "rgba(168, 85, 247, 0.25)",
    lineWidth: 1,
    lineStyle: 1, // Dashed
  });
  rsiLower.setData(vizData.rsi_data.map(d => ({ time: d.time, value: 30 })));


  // 6. Initialize MACD Subchart
  const macdChart = LightweightCharts.createChart(els.macdChart, {
    width: subContainerWidth,
    height: 180,
    layout: {
      backgroundColor: "#0f172a",
      textColor: "#94a3b8",
      fontFamily: "'Outfit', sans-serif",
    },
    grid: {
      vertLines: { color: "rgba(30, 41, 59, 0.5)" },
      horzLines: { color: "rgba(30, 41, 59, 0.5)" },
    },
    rightPriceScale: { borderColor: "rgba(51, 65, 85, 0.5)" },
    timeScale: { borderColor: "rgba(51, 65, 85, 0.5)" },
  });

  const macdLineSeries = macdChart.addLineSeries({
    color: "#2563eb",
    lineWidth: 1,
  });
  macdLineSeries.setData(vizData.macd_line_data);

  const macdSignalSeries = macdChart.addLineSeries({
    color: "#ea580c",
    lineWidth: 1,
  });
  macdSignalSeries.setData(vizData.macd_signal_data);

  const macdHistSeries = macdChart.addHistogramSeries({
    color: "#26a69a",
  });
  macdHistSeries.setData(vizData.macd_hist_data);

  // 7. Synchronize Visible Scale / Ranges across charts using logical range for perfect alignment & smooth dragging
  let isScaling = false;
  priceChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
    if (isScaling || !range) return;
    isScaling = true;
    rsiChart.timeScale().setVisibleLogicalRange(range);
    macdChart.timeScale().setVisibleLogicalRange(range);
    isScaling = false;
  });

  rsiChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
    if (isScaling || !range) return;
    isScaling = true;
    priceChart.timeScale().setVisibleLogicalRange(range);
    macdChart.timeScale().setVisibleLogicalRange(range);
    isScaling = false;
  });

  macdChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
    if (isScaling || !range) return;
    isScaling = true;
    priceChart.timeScale().setVisibleLogicalRange(range);
    rsiChart.timeScale().setVisibleLogicalRange(range);
    isScaling = false;
  });

  // 8. Crosshair Legend Update
  priceChart.subscribeCrosshairMove((param) => {
    if (!param.time || param.point === undefined) {
      els.chartLegend.innerHTML = "O: -- | H: -- | L: -- | C: --";
      return;
    }
    const dataPoint = param.seriesData.get(candlestickSeries);
    if (dataPoint) {
      els.chartLegend.innerHTML =
        `<span class="text-slate-400">O:</span> <span class="text-slate-200 font-semibold">${dataPoint.open.toFixed(1)}</span> | ` +
        `<span class="text-slate-400">H:</span> <span class="text-slate-200 font-semibold">${dataPoint.high.toFixed(1)}</span> | ` +
        `<span class="text-slate-400">L:</span> <span class="text-slate-200 font-semibold">${dataPoint.low.toFixed(1)}</span> | ` +
        `<span class="text-slate-400">C:</span> <span class="text-slate-200 font-semibold">${dataPoint.close.toFixed(1)}</span>`;
    }
  });

  // 9. Generate Trade Markers and TP/SL Price Lines
  const markers = [];
  vizData.trades.forEach((trade) => {
    // BUY Arrow marker
    markers.push({
      time: trade.entry_time,
      position: "belowBar",
      color: "#10b981",
      shape: "arrowUp",
      text: "BUY @ " + trade.entry_price.toFixed(0),
    });

    // SELL Arrow marker
    const profitPct = (trade.return_pct * 100).toFixed(1) + "%";
    markers.push({
      time: trade.exit_time,
      position: "aboveBar",
      color: trade.return_pct >= 0 ? "#10b981" : "#ef4444",
      shape: "arrowDown",
      text: `${trade.exit_reason} (${profitPct})`,
    });

    // Horizontal TP Line block
    if (trade.take_profit) {
      const tpLine = priceChart.addLineSeries({
        color: "rgba(16, 185, 129, 0.4)",
        lineWidth: 1.5,
        lineStyle: 1, // Dashed
        priceLineVisible: false,
        lastValueVisible: false,
      });
      const tpData = trade.segment_times.map(t => ({ time: t, value: trade.take_profit }));
      tpLine.setData(tpData);
      charts.tpSLSeries.push(tpLine);
    }

    // Horizontal SL Line block
    if (trade.stop_loss) {
      const slLine = priceChart.addLineSeries({
        color: "rgba(239, 68, 68, 0.4)",
        lineWidth: 1.5,
        lineStyle: 1, // Dashed
        priceLineVisible: false,
        lastValueVisible: false,
      });
      const slData = trade.segment_times.map(t => ({ time: t, value: trade.stop_loss }));
      slLine.setData(slData);
      charts.tpSLSeries.push(slLine);
    }
  });
  candlestickSeries.setMarkers(markers);

  // 10. Populate Trade execution logs table & click handlers
  els.tradeLogsBody.innerHTML = "";
  vizData.trades.forEach((trade) => {
    const tr = document.createElement("tr");
    const returnVal = (trade.return_pct * 100).toFixed(1) + "%";
    const pnlClass = trade.return_pct >= 0 ? "text-green font-semibold" : "text-red font-semibold";

    tr.innerHTML = `
      <td style="color: var(--muted); font-weight: 600;">${trade.index}</td>
      <td>${trade.entry_date}</td>
      <td style="color: var(--muted); font-family: monospace;">${trade.exit_reason}</td>
      <td style="text-align: right;" class="${pnlClass}">${returnVal}</td>
    `;

    tr.addEventListener("click", () => {
      // Highlight selected row
      document.querySelectorAll("#tradeLogsBody tr").forEach(row => row.classList.remove("selected"));
      tr.classList.add("selected");

      // Show detail panel
      els.tradeDetailPanel.style.display = "block";
      els.detailIndex.innerText = trade.index;
      els.detailEntryDate.innerText = trade.entry_date;
      els.detailExitDate.innerText = trade.exit_date;
      els.detailEntryPrice.innerText = trade.entry_price.toLocaleString("vi-VN");
      els.detailExitPrice.innerText = trade.exit_price.toLocaleString("vi-VN");
      els.detailTP.innerText = trade.take_profit ? trade.take_profit.toLocaleString("vi-VN") : "N/A";
      els.detailSL.innerText = trade.stop_loss ? trade.stop_loss.toLocaleString("vi-VN") : "N/A";
      els.detailExitReason.innerText = trade.exit_reason;

      const confBadge = els.detailConfidence;
      confBadge.innerText = trade.confidence.toUpperCase();
      confBadge.className = "badge";
      if (trade.confidence === "high") {
        confBadge.classList.add("ok");
      } else if (trade.confidence === "medium") {
        confBadge.classList.add("running");
      } else {
        confBadge.classList.add("error");
      }

      // Zoom/Focus chart viewport around the trade dates
      const entryTime = trade.entry_time;
      const exitTime = trade.exit_time;

      priceChart.timeScale().setVisibleRange({
        from: typeof entryTime === "number" ? entryTime - (60 * 60 * 24 * 10) : getOffsetDateString(trade.entry_date, -10),
        to: typeof exitTime === "number" ? exitTime + (60 * 60 * 24 * 10) : getOffsetDateString(trade.exit_date, 10),
      });
    });

    els.tradeLogsBody.appendChild(tr);
  });

  // Save chart references to charts object
  charts.price = priceChart;
  charts.rsi = rsiChart;
  charts.macd = macdChart;
  charts.candlestickSeries = candlestickSeries;
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPARISON TABLE (Full Pipeline vs Baseline) + AGENT REPORT
// ─────────────────────────────────────────────────────────────────────────────
function fmtPct(v) {
  if (v === null || v === undefined || isNaN(v)) return "--";
  return (v * 100).toFixed(1) + "%";
}

function fmtNum(v) {
  if (v === null || v === undefined || isNaN(v)) return "--";
  return Number(v).toFixed(2);
}

function renderComparison(vizData) {
  const baseline = vizData.baseline;
  if (!baseline || !baseline.metrics || Object.keys(baseline.metrics).length === 0) {
    els.comparisonCard.style.display = "none";
    return;
  }

  const full = vizData.metrics;
  const base = baseline.metrics;

  const rows = [
    { label: "Số giao dịch", get: (m) => m?.volume?.n_trades, kind: "int" },
    { label: "Tỉ lệ thắng", get: (m) => m?.volume?.win_rate, kind: "pct" },
    { label: "Lợi nhuận ròng", get: (m) => m?.pnl?.total_return, kind: "pct" },
    { label: "Lợi nhuận TB / lệnh", get: (m) => m?.pnl?.avg_return, kind: "pct" },
    { label: "Hệ số Sharpe", get: (m) => m?.risk?.sharpe_ratio, kind: "num" },
    { label: "Max Drawdown", get: (m) => m?.risk?.max_drawdown, kind: "pct" },
    { label: "Profit Factor", get: (m) => m?.risk?.profit_factor, kind: "num" },
  ];

  els.comparisonBody.innerHTML = "";
  rows.forEach((row) => {
    const fv = row.get(full);
    const bv = row.get(base);

    let fullStr, baseStr, deltaStr, deltaClass = "";
    if (row.kind === "int") {
      fullStr = fv ?? "--";
      baseStr = bv ?? "--";
      const d = (Number(fv) || 0) - (Number(bv) || 0);
      deltaStr = (d > 0 ? "+" : "") + d;
    } else {
      const fmt = row.kind === "pct" ? fmtPct : fmtNum;
      fullStr = fmt(fv);
      baseStr = fmt(bv);
      const d = (Number(fv) || 0) - (Number(bv) || 0);
      if (row.kind === "pct") {
        deltaStr = (d > 0 ? "+" : "") + (d * 100).toFixed(1) + " pp";
      } else {
        deltaStr = (d > 0 ? "+" : "") + d.toFixed(2);
      }
      deltaClass = d > 0 ? "text-green font-semibold" : d < 0 ? "text-red font-semibold" : "";
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.label}</td>
      <td style="text-align: right;">${fullStr}</td>
      <td style="text-align: right; color: var(--muted);">${baseStr}</td>
      <td style="text-align: right;" class="${deltaClass}">${deltaStr}</td>
    `;
    els.comparisonBody.appendChild(tr);
  });

  els.comparisonCard.style.display = "block";
}

function confidenceInfo(conf) {
  if (typeof conf === "number") {
    const cls = conf >= 0.7 ? "ok" : conf >= 0.4 ? "running" : "error";
    return { text: conf.toFixed(2), cls };
  }
  const c = (conf || "").toString().toLowerCase();
  const cls = (c === "high" || c === "cao")
    ? "ok"
    : (c === "medium" || c.includes("trung"))
      ? "running"
      : "error";
  return { text: (conf || "N/A").toString().toUpperCase(), cls };
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function analysisSection(title, text) {
  if (!text) return "";
  return `<div class="agent-sub-block"><h4>${title}</h4><p class="agent-analysis-text">${escapeHtml(text)}</p></div>`;
}

function renderAgentReportDetail(report) {
  const rec = report.recommendation || "N/A";
  const conf = confidenceInfo(report.confidence);
  const analysis = report.analysis;

  const sources = Array.isArray(report.data_sources_used) && report.data_sources_used.length
    ? report.data_sources_used.join(", ")
    : "--";

  // analysis là object {technical, fundamental, news, summary} từ aggregator.
  // Phòng trường hợp file cũ lưu analysis dạng chuỗi.
  let analysisHtml;
  if (analysis && typeof analysis === "object") {
    analysisHtml =
      analysisSection("📝 Tổng hợp", analysis.summary) +
      analysisSection("📈 Kỹ thuật", analysis.technical) +
      analysisSection("📊 Cơ bản", analysis.fundamental) +
      analysisSection("📰 Tin tức", analysis.news);
    if (!analysisHtml) analysisHtml = '<p class="hint">Không có nội dung phân tích.</p>';
  } else if (typeof analysis === "string" && analysis.trim()) {
    analysisHtml = `<div class="agent-sub-block"><p class="agent-analysis-text">${escapeHtml(analysis)}</p></div>`;
  } else {
    analysisHtml = '<p class="hint">Không có nội dung phân tích.</p>';
  }

  els.agentReportDetail.innerHTML = `
    <div class="report-detail-header">
      <h3>Tín hiệu ngày ${report.date}</h3>
      <div class="report-badges">
        <span class="badge">${escapeHtml(rec)}</span>
        <span class="badge ${conf.cls}">${escapeHtml(conf.text)}</span>
      </div>
    </div>
    <ul class="detail-list">
      <li><span class="lbl">Score kỹ thuật:</span> <span class="val">${report.total_score ?? "--"}</span></li>
      <li><span class="lbl">Giá vào:</span> <span class="val">${report.entry_price ?? "--"}</span></li>
      <li><span class="lbl">Take Profit:</span> <span class="val text-green">${report.take_profit_price ?? "--"}</span></li>
      <li><span class="lbl">Stop Loss:</span> <span class="val text-red">${report.stop_loss_price ?? "--"}</span></li>
      <li><span class="lbl">Nến giữ tối đa:</span> <span class="val">${report.max_hold_candles ?? "--"}</span></li>
      <li><span class="lbl">Nguồn dữ liệu:</span> <span class="val">${escapeHtml(sources)}</span></li>
    </ul>
    ${analysisHtml}
  `;
}

function renderAgentReports(vizData) {
  // Chỉ hiển thị report cho các tín hiệu được khuyến nghị Mua.
  const reports = (Array.isArray(vizData.agent_reports) ? vizData.agent_reports : [])
    .filter((r) => r.recommendation === "Mua");

  if (reports.length === 0) {
    els.agentReportCard.style.display = "none";
    return;
  }

  els.agentReportCount.textContent = `${reports.length} lệnh mua`;
  els.agentReportList.innerHTML = "";
  els.agentReportDetail.innerHTML = '<p class="hint">Chọn một lệnh mua ở danh sách bên trái để xem report.</p>';

  reports.forEach((report) => {
    const item = document.createElement("div");
    item.className = "agent-report-item";
    const rec = report.recommendation || "N/A";
    const conf = confidenceInfo(report.confidence);

    item.innerHTML = `
      <div class="agent-report-item-main">
        <span class="agent-report-date">${report.date}</span>
        <span class="text-green font-semibold">${escapeHtml(rec)}</span>
      </div>
      <span class="badge ${conf.cls}">${escapeHtml(conf.text)}</span>
    `;

    item.addEventListener("click", () => {
      document.querySelectorAll("#agentReportList .agent-report-item").forEach((el) => el.classList.remove("selected"));
      item.classList.add("selected");
      renderAgentReportDetail(report);
    });

    els.agentReportList.appendChild(item);
  });

  els.agentReportCard.style.display = "block";
}

function getOffsetDateString(dateStr, offsetDays) {
  const date = new Date(dateStr);
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().split("T")[0];
}

// Auto resize lightweight chart canvas when panel container is resized
// window.addEventListener("resize", () => {
//   if (charts.price && els.priceChart.clientWidth) {
//     const w = els.priceChart.clientWidth;
//     charts.price.resize(w, 450);
//     if (charts.rsi) charts.rsi.resize(w, 180);
//     if (charts.macd) charts.macd.resize(w, 180);
//   }
// });
window.addEventListener("resize", () => {
  if (charts.price) {
    const w = els.priceChart.offsetWidth || els.priceChart.clientWidth;
    if (!w) return;
    charts.price.resize(w, 450);
    const subW = els.rsiChart.offsetWidth || els.rsiChart.clientWidth || (w / 2 - 8);
    if (charts.rsi) charts.rsi.resize(subW, 180);
    if (charts.macd) charts.macd.resize(subW, 180);
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// AI ANALYZE TAB (Admin) — single symbol or VN30/VN100 basket
// ─────────────────────────────────────────────────────────────────────────────
const AN_TECH_KEYS = ["ma", "boll", "rsi", "macd", "kdj"];
const AN_FUND_KEYS = ["liquidity", "leverage", "efficiency", "profitability", "valuation"];

function getAnalyzeSource() {
  const btn = els.analyzeSourceControl?.querySelector(".seg-btn.active");
  return btn ? btn.dataset.source : "single";
}

function getAnalyzeMode() {
  const btn = els.analyzeModeControl?.querySelector(".seg-btn.active");
  return btn ? btn.dataset.mode : "auto";
}

function getAnalyzeDataSelection() {
  return {
    news: els.anNews ? els.anNews.checked : true,
    technical: readChecks(".an-tech", AN_TECH_KEYS),
    fundamental: readChecks(".an-fund", AN_FUND_KEYS),
  };
}

function updateAnalyzeDsCounts() {
  const techOn = AN_TECH_KEYS.filter((k) => document.querySelector(`.an-tech[value="${k}"]`)?.checked).length;
  const fundOn = AN_FUND_KEYS.filter((k) => document.querySelector(`.an-fund[value="${k}"]`)?.checked).length;
  if (els.anTechCount) els.anTechCount.textContent = `${techOn}/${AN_TECH_KEYS.length}`;
  if (els.anFundCount) els.anFundCount.textContent = `${fundOn}/${AN_FUND_KEYS.length}`;
}

function buildAnalyzeBody(symbol) {
  const mode = getAnalyzeMode();
  const body = {
    mode,
    symbol,
    risk_appetite: { period: els.analyzeRiskPeriod.value },
  };
  if (mode === "manual") {
    body.data_selection = getAnalyzeDataSelection();
  }
  return body;
}

function initAnalyzeControls() {
  if (els.analyzeSourceControl) {
    els.analyzeSourceControl.querySelectorAll(".seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        els.analyzeSourceControl.querySelectorAll(".seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        // Single-symbol input only relevant for the "single" source.
        if (els.analyzeSymbolField) {
          els.analyzeSymbolField.style.display = btn.dataset.source === "single" ? "" : "none";
        }
      });
    });
  }

  if (els.analyzeModeControl) {
    els.analyzeModeControl.querySelectorAll(".seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        els.analyzeModeControl.querySelectorAll(".seg-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        if (els.analyzeDataSelectionPanel) {
          els.analyzeDataSelectionPanel.style.display = btn.dataset.mode === "manual" ? "flex" : "none";
        }
      });
    });
  }

  document.querySelectorAll(".an-tech, .an-fund").forEach((cb) => {
    cb.addEventListener("change", updateAnalyzeDsCounts);
  });
  updateAnalyzeDsCounts();
}

function recommendationBadgeClass(rec) {
  const r = (rec || "").toString();
  if (r === "Mua") return "ok";
  if (r === "Bán") return "error";
  return "running"; // Giữ / Chờ
}

function analysisBlocksHtml(rec) {
  const a = rec && rec.analysis;
  if (a && typeof a === "object") {
    return (
      analysisSection("📝 Tổng hợp", a.summary) +
      analysisSection("📈 Kỹ thuật", a.technical) +
      analysisSection("📊 Cơ bản", a.fundamental) +
      analysisSection("📰 Tin tức", a.news)
    ) || '<p class="hint">Không có nội dung phân tích.</p>';
  }
  if (typeof a === "string" && a.trim()) {
    return `<div class="agent-sub-block"><p class="agent-analysis-text">${escapeHtml(a)}</p></div>`;
  }
  return '<p class="hint">Không có nội dung phân tích.</p>';
}

function recommendationDetailHtml(symbol, rec) {
  const conf = confidenceInfo(rec.confidence);
  return `
    <div class="report-detail-header">
      <h3>${escapeHtml(symbol)}</h3>
      <div class="report-badges">
        <span class="badge ${recommendationBadgeClass(rec.recommendation)}">${escapeHtml(rec.recommendation || "N/A")}</span>
        <span class="badge ${conf.cls}">${escapeHtml(conf.text)}</span>
      </div>
    </div>
    <ul class="detail-list">
      <li><span class="lbl">Giá vào:</span> <span class="val">${rec.entry_price ?? "--"}</span></li>
      <li><span class="lbl">Take Profit:</span> <span class="val text-green">${rec.take_profit_price ?? "--"}</span></li>
      <li><span class="lbl">Stop Loss:</span> <span class="val text-red">${rec.stop_loss_price ?? "--"}</span></li>
      <li><span class="lbl">Nến giữ tối đa:</span> <span class="val">${rec.max_hold_candles ?? "--"}</span></li>
    </ul>
    ${analysisBlocksHtml(rec)}
  `;
}

function renderSingleRecommendation(symbol, rec) {
  els.analyzeSingleResult.style.display = "block";
  els.analyzeSingleResult.innerHTML = recommendationDetailHtml(symbol, rec);
  els.analyzeSingleResult.scrollIntoView({ behavior: "smooth" });
}

function addAnalyzeTableRow(symbol, rec, status, errMsg = "") {
  const tr = document.createElement("tr");
  const recText = rec ? (rec.recommendation || "N/A") : "N/A";
  const conf = rec ? confidenceInfo(rec.confidence) : { text: "--", cls: "" };
  const summary = rec && rec.analysis && rec.analysis.summary ? rec.analysis.summary : "";
  const shortSummary = summary.length > 90 ? summary.slice(0, 90) + "…" : summary;
  const statusClass = status === "ok" ? "badge ok" : "badge error";
  const recClass = rec ? `badge ${recommendationBadgeClass(recText)}` : "badge";

  tr.innerHTML = `
    <td><strong>${escapeHtml(symbol)}</strong></td>
    <td><span class="${recClass}">${escapeHtml(recText)}</span></td>
    <td><span class="badge ${conf.cls}">${escapeHtml(conf.text)}</span></td>
    <td style="max-width: 320px; color: var(--muted); font-size: 0.82rem;">${escapeHtml(shortSummary)}</td>
    <td><span class="${statusClass}" title="${escapeHtml(errMsg)}">${status === "ok" ? "OK" : "Lỗi"}</span></td>
    <td style="text-align: center;">
      <button class="btn btn-ghost btn-view-analyze" type="button" style="padding: 4px 10px; font-size: 0.75rem;" ${rec ? "" : "disabled"}>Xem</button>
    </td>
  `;

  if (rec) {
    tr.querySelector(".btn-view-analyze").addEventListener("click", () => {
      els.analyzeDetailPanel.style.display = "block";
      els.analyzeDetailPanel.innerHTML = recommendationDetailHtml(symbol, rec);
      els.analyzeDetailPanel.scrollIntoView({ behavior: "smooth" });
    });
  }

  els.analyzeResultsBody.appendChild(tr);
}

function appendAnalyzeLog(msg) {
  els.analyzeLogs.textContent += `[${new Date().toLocaleTimeString("vi-VN")}] ${msg}\n`;
  els.analyzeLogs.scrollTop = els.analyzeLogs.scrollHeight;
}

function updateAnalyzeProgress(current, total, label = "") {
  const percent = total ? Math.round((current / total) * 100) : 0;
  els.analyzeProgressBar.style.width = `${percent}%`;
  els.analyzeStatus.textContent = label || `Đang chạy ${current}/${total} (${percent}%)`;
  els.analyzeStatus.classList.toggle("ok", percent === 100);
  els.analyzeStatus.classList.toggle("running", percent !== 100);
}

async function runAnalyze() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  if (!baseUrl) {
    alert("Không thể phân tích: API Base URL đang trống.");
    return;
  }
  if (!adminToken) {
    const ok = await adminLogin();
    if (!ok) {
      alert("Chưa đăng nhập admin. Kiểm tra ADMIN_EMAIL/ADMIN_PASSWORD ở backend.");
      return;
    }
  }

  const source = getAnalyzeSource();
  els.runAnalyzeBtn.disabled = true;

  // Reset result panels
  els.analyzeSingleResult.style.display = "none";
  els.analyzeProgressCard.style.display = "none";
  els.analyzeResultsCard.style.display = "none";
  els.analyzeDetailPanel.style.display = "none";

  try {
    if (source === "single") {
      const symbol = (els.analyzeSymbol.value || "").trim().toUpperCase();
      if (!symbol) {
        alert("Vui lòng nhập mã cổ phiếu.");
        return;
      }
      els.runAnalyzeBtn.textContent = `Đang phân tích ${symbol}...`;
      appendLog(`Phân tích AI cho ${symbol}...`);

      const payload = await requestJson(`${baseUrl}/api/agentic/admin-analyze`, {
        method: "POST",
        body: buildAnalyzeBody(symbol),
      });
      const entry = payload?.data?.results?.[0];
      if (entry && entry.status === "ok" && entry.recommendation) {
        renderSingleRecommendation(symbol, entry.recommendation);
        appendLog(`Phân tích ${symbol} hoàn thành: ${entry.recommendation.recommendation}.`);
      } else {
        throw new Error(entry?.error || "Không nhận được kết quả phân tích.");
      }
    } else {
      // VN30 / VN100 — fetch the universe then loop per symbol with progress.
      els.analyzeProgressCard.style.display = "block";
      els.analyzeResultsCard.style.display = "block";
      els.analyzeUniverseName.textContent = source;
      els.analyzeResultsBody.innerHTML = "";
      els.analyzeLogs.textContent = "";
      analyzeSummaryData = [];
      updateAnalyzeProgress(0, 1, "Đang tải danh sách mã...");

      els.runAnalyzeBtn.textContent = `Đang tải rổ ${source}...`;
      const uniPayload = await requestJson(`${baseUrl}/api/agentic/admin-universe/${source}`);
      const symbols = uniPayload?.data?.symbols || [];
      if (symbols.length === 0) {
        throw new Error(`Rổ ${source} không có mã nào (kiểm tra bảng MarketIndex).`);
      }

      appendLog(`Bắt đầu phân tích rổ ${source} (${symbols.length} mã)...`);
      els.runAnalyzeBtn.textContent = `Đang chạy ${source}...`;

      for (let i = 0; i < symbols.length; i++) {
        const sym = symbols[i];
        updateAnalyzeProgress(i, symbols.length, `Đang xử lý ${sym} (${i + 1}/${symbols.length})...`);
        appendAnalyzeLog(`[${i + 1}/${symbols.length}] Phân tích ${sym}...`);

        try {
          const payload = await requestJson(`${baseUrl}/api/agentic/admin-analyze`, {
            method: "POST",
            body: buildAnalyzeBody(sym),
          });
          const entry = payload?.data?.results?.[0];
          if (entry && entry.status === "ok" && entry.recommendation) {
            const rec = entry.recommendation;
            addAnalyzeTableRow(sym, rec, "ok");
            analyzeSummaryData.push({ symbol: sym, rec, status: "ok" });
            appendAnalyzeLog(`✅ ${sym}: ${rec.recommendation} (tự tin ${confidenceInfo(rec.confidence).text}).`);
          } else {
            throw new Error(entry?.error || "Kết quả rỗng");
          }
        } catch (err) {
          addAnalyzeTableRow(sym, null, "error", err.message);
          analyzeSummaryData.push({ symbol: sym, rec: null, status: "error" });
          appendAnalyzeLog(`❌ ${sym} lỗi: ${err.message}`);
        }

        updateAnalyzeProgress(i + 1, symbols.length);
        await new Promise((r) => setTimeout(r, 150));
      }

      appendAnalyzeLog(`🎉 Hoàn thành rổ ${source}!`);
      updateAnalyzeProgress(symbols.length, symbols.length, `Hoàn tất rổ ${source}`);
      appendLog(`Phân tích rổ ${source} hoàn tất.`);
    }
  } catch (error) {
    appendLog(`Lỗi phân tích: ${error.message}`);
    alert(`Lỗi phân tích: ${error.message}`);
  } finally {
    els.runAnalyzeBtn.disabled = false;
    els.runAnalyzeBtn.textContent = "Chạy phân tích";
  }
}

function exportAnalyzeCsv() {
  if (analyzeSummaryData.length === 0) return;
  let csv = "data:text/csv;charset=utf-8,Symbol,Recommendation,Confidence,Status\n";
  analyzeSummaryData.forEach((row) => {
    const rec = row.rec ? (row.rec.recommendation || "") : "";
    const conf = row.rec ? confidenceInfo(row.rec.confidence).text : "";
    csv += `${row.symbol},${rec},${conf},${row.status}\n`;
  });
  const link = document.createElement("a");
  link.setAttribute("href", encodeURI(csv));
  link.setAttribute("download", `AI_Analyze_${els.analyzeUniverseName.textContent}_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ─────────────────────────────────────────────────────────────────────────────
// INITIALIZATION
// ─────────────────────────────────────────────────────────────────────────────
els.loadSymbolsBtn.addEventListener("click", loadSymbols);
els.updatePriceBtn.addEventListener("click", updatePrice);
els.updateNewsBtn.addEventListener("click", updateNews);
els.clearLogBtn.addEventListener("click", clearLog);
els.runBacktestBtn.addEventListener("click", runBacktest);
els.exportVn30CsvBtn.addEventListener("click", exportVn30Csv);
els.refreshCloudHistoryBtn.addEventListener("click", loadCloudHistory);
els.runAnalyzeBtn.addEventListener("click", runAnalyze);
els.exportAnalyzeCsvBtn.addEventListener("click", exportAnalyzeCsv);

window.addEventListener("DOMContentLoaded", async () => {
  appendLog("Dashboard đã khởi tạo.");

  // Tabs Navigation init
  initTabs();

  // Drag and drop JSON uploader init
  initDragDrop();

  // Mode (auto/manual) + data selection toggles init
  initDataSelectionControls();

  // AI analyze tab controls init
  initAnalyzeControls();

  // Auto-login as admin so protected endpoints (backtest, admin-analyze) work.
  await adminLogin();

  // Disable text symbol input if VN30 option is checked
  els.vn30Option.addEventListener("change", (e) => {
    els.backtestSymbol.disabled = e.target.checked;
    if (e.target.checked) {
      els.backtestSymbol.placeholder = "Chạy tất cả 30 mã VN30";
    } else {
      els.backtestSymbol.placeholder = "Ví dụ: FPT, VNM...";
    }
  });

  // Auto-load symbols once to reduce manual actions for admin.
  if (!symbolsLoaded) {
    loadSymbols();
  }

  // Load cloud backtest history
  loadCloudHistory();
});
