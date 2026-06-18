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
};

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

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options.headers || {}),
    },
    ...(options.body ? { body: JSON.stringify(options.body) } : {}),
  });

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
  els.tabDataBtn.addEventListener("click", () => {
    els.tabDataBtn.classList.add("active");
    els.tabBacktestBtn.classList.remove("active");
    els.dataTabContent.style.display = "block";
    els.backtestTabContent.style.display = "none";
  });

  els.tabBacktestBtn.addEventListener("click", () => {
    els.tabBacktestBtn.classList.add("active");
    els.tabDataBtn.classList.remove("active");
    els.backtestTabContent.style.display = "block";
    els.dataTabContent.style.display = "none";
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// BACKTEST EXECUTION CONTROLLER
// ─────────────────────────────────────────────────────────────────────────────
const DS_TECH_KEYS = ["ma", "boll", "rsi", "macd", "kdj"];
const DS_FUND_KEYS = ["valuation", "profitability", "growth", "financial_health", "cash_flow"];

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
async function loadCloudHistory() {
  const baseUrl = normalizeBaseUrl(els.baseUrl.value);
  if (!baseUrl) return;

  els.cloudHistoryList.innerHTML = '<p class="hint">Đang tải lịch sử...</p>';

  try {
    const response = await fetch(`${baseUrl}/api/agentic/backtests`);
    const payload = await response.json();
    
    if (payload && payload.result && Array.isArray(payload.data)) {
      els.cloudHistoryList.innerHTML = "";
      const files = payload.data;
      
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
// INITIALIZATION
// ─────────────────────────────────────────────────────────────────────────────
els.loadSymbolsBtn.addEventListener("click", loadSymbols);
els.updatePriceBtn.addEventListener("click", updatePrice);
els.updateNewsBtn.addEventListener("click", updateNews);
els.clearLogBtn.addEventListener("click", clearLog);
els.runBacktestBtn.addEventListener("click", runBacktest);
els.exportVn30CsvBtn.addEventListener("click", exportVn30Csv);
els.refreshCloudHistoryBtn.addEventListener("click", loadCloudHistory);

window.addEventListener("DOMContentLoaded", () => {
  appendLog("Dashboard đã khởi tạo.");

  // Tabs Navigation init
  initTabs();

  // Drag and drop JSON uploader init
  initDragDrop();

  // Mode (auto/manual) + data selection toggles init
  initDataSelectionControls();

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
