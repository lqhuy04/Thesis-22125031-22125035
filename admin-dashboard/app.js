// Cache elements
const els = {
  // Tabs
  tabBacktestBtn: document.getElementById("tab-backtest-btn"),
  backtestTabContent: document.getElementById("backtest-tab-content"),
  tabHistoryBtn: document.getElementById("tab-history-btn"),
  historyTabContent: document.getElementById("history-tab-content"),

  // Backtest Inputs
  backtestForm: document.getElementById("backtestForm"),
  backtestSymbol: document.getElementById("backtestSymbol"),
  vn30Option: document.getElementById("vn30Option"),
  startDate: document.getElementById("startDate"),
  endDate: document.getElementById("endDate"),
  marketSymbol: document.getElementById("marketSymbol"),
  maxHoldCandles: document.getElementById("maxHoldCandles"),
  exitOnScoreDrop: document.getElementById("exitOnScoreDrop"),
  runBacktestBtn: document.getElementById("runBacktestBtn"),

  // Backtest flow + data selection
  backtestFlowControl: document.getElementById("backtestFlowControl"),
  singleIndicatorField: document.getElementById("singleIndicatorField"),
  singleIndicatorSelect: document.getElementById("singleIndicatorSelect"),
  backtestFlowSummary: document.getElementById("backtestFlowSummary"),
  dataSelectionPanel: document.getElementById("dataSelectionPanel"),
  dsNews: document.getElementById("dsNews"),
  dsFundamental: document.getElementById("dsFundamental"),
  dsTechCount: document.getElementById("dsTechCount"),
  dsWeightNews: document.getElementById("dsWeightNews"),
  dsWeightTechnical: document.getElementById("dsWeightTechnical"),
  dsWeightFundamental: document.getElementById("dsWeightFundamental"),

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
  resetVn30CheckpointBtn: document.getElementById("resetVn30CheckpointBtn"),

  // Viz Wrapper
  vizWrapper: document.getElementById("vizWrapper"),
  statNetProfit: document.getElementById("statNetProfit"),
  statWinRate: document.getElementById("statWinRate"),
  statTotalTrades: document.getElementById("statTotalTrades"),
  statSharpe: document.getElementById("statSharpe"),
  backtestConfigCard: document.getElementById("backtestConfigCard"),
  vizFlowTitle: document.getElementById("vizFlowTitle"),
  vizConfigBadges: document.getElementById("vizConfigBadges"),
  vizSymbol: document.getElementById("vizSymbol"),
  chartLegend: document.getElementById("chartLegend"),
  priceIndicatorTags: document.getElementById("priceIndicatorTags"),
  priceChart: document.getElementById("priceChart"),
  indicatorChartsGrid: document.getElementById("indicatorChartsGrid"),
  rsiChartBox: document.getElementById("rsiChartBox"),
  rsiChart: document.getElementById("rsiChart"),
  macdChartBox: document.getElementById("macdChartBox"),
  macdChart: document.getElementById("macdChart"),
  kdjChartBox: document.getElementById("kdjChartBox"),
  kdjChart: document.getElementById("kdjChart"),
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
  comparisonTitle: document.getElementById("comparisonTitle"),
  pipelineColumnTitle: document.getElementById("pipelineColumnTitle"),
  baselineColumnTitle: document.getElementById("baselineColumnTitle"),
  comparisonDeltaTitle: document.getElementById("comparisonDeltaTitle"),
  comparisonBody: document.getElementById("comparisonBody"),
  agentReportCard: document.getElementById("agentReportCard"),
  agentReportCount: document.getElementById("agentReportCount"),
  agentReportList: document.getElementById("agentReportList"),
  agentReportDetail: document.getElementById("agentReportDetail"),

  // Stockrium Lab authentication
  authBadge: document.getElementById("authBadge"),
  loginCard: document.getElementById("loginCard"),
  loginForm: document.getElementById("loginForm"),
  emailInput: document.getElementById("emailInput"),
  passwordInput: document.getElementById("passwordInput"),
  loginBtn: document.getElementById("loginBtn"),
  loginError: document.getElementById("loginError"),
  logoutBtn: document.getElementById("logoutBtn"),

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
  anFundamental: document.getElementById("anFundamental"),
  anTechCount: document.getElementById("anTechCount"),
  anWeightNews: document.getElementById("anWeightNews"),
  anWeightTechnical: document.getElementById("anWeightTechnical"),
  anWeightFundamental: document.getElementById("anWeightFundamental"),
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

  // Personal experiment history
  refreshExperimentHistoryBtn: document.getElementById("refreshExperimentHistoryBtn"),
  experimentTypeFilter: document.getElementById("experimentTypeFilter"),
  experimentStatusFilter: document.getElementById("experimentStatusFilter"),
  experimentHistoryBody: document.getElementById("experimentHistoryBody"),
  experimentDetailCard: document.getElementById("experimentDetailCard"),
  experimentDetailTitle: document.getElementById("experimentDetailTitle"),
  experimentDetailStatus: document.getElementById("experimentDetailStatus"),
  experimentConfiguration: document.getElementById("experimentConfiguration"),
  experimentResultData: document.getElementById("experimentResultData"),
  experimentReproducibility: document.getElementById("experimentReproducibility"),
  copyExperimentBundleBtn: document.getElementById("copyExperimentBundleBtn"),
  experimentSelectionCount: document.getElementById("experimentSelectionCount"),
  clearExperimentSelectionBtn: document.getElementById("clearExperimentSelectionBtn"),
  compareExperimentsBtn: document.getElementById("compareExperimentsBtn"),
  experimentCompareCard: document.getElementById("experimentCompareCard"),
  closeExperimentCompareBtn: document.getElementById("closeExperimentCompareBtn"),
  experimentComparisonContent: document.getElementById("experimentComparisonContent"),
};

// Tokens remain in memory only. Never put credentials or tokens in web storage.
let accessToken = null;
let sessionRefreshToken = null;
let refreshPromise = null;
let refreshTimer = null;
let apiBaseUrl = normalizeBaseUrl(window.STOCKRIUM_CONFIG?.API_BASE_URL);
let currentUserId = null;
let userContextVersion = 0;
let analyzeSummaryData = [];
const EXPERIMENT_COMPARE_LIMIT = 5;
let selectedExperimentIds = new Set();
let comparisonLoading = false;
let currentExperimentBundle = null;

let vn30SummaryData = []; // Store stats for CSV export

// Active Chart Instances (for window resize cleanup or updates)
let charts = {
  price: null,
  rsi: null,
  macd: null,
  kdj: null,
  candlestickSeries: null,
  tpSLSeries: [] // Keep references to cleanup TP/SL lines
};

// Utilities
function normalizeBaseUrl(raw) {
  return (raw || "").trim().replace(/\/+$/, "");
}

function appendLog(message) {
  console.info(`[Stockrium Lab] ${message}`);
}

function buildAuthenticatedRequestOptions(options = {}, token = accessToken) {
  return {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...(options.body ? { body: JSON.stringify(options.body) } : {}),
  };
}

async function requestJson(url, options = {}) {
  const requestContextVersion = userContextVersion;
  let response = await fetch(url, buildAuthenticatedRequestOptions(options));

  if (response.status === 401) {
    try {
      const refreshedToken = await refreshSession();
      response = await fetch(
        url,
        buildAuthenticatedRequestOptions(options, refreshedToken),
      );
    } catch (error) {
      if (requestContextVersion === userContextVersion) {
        clearSession(error.message || "Phiên đăng nhập đã hết hạn.", true);
      }
      throw error;
    }
  }

  if (requestContextVersion !== userContextVersion) {
    throw new Error("Phiên người dùng đã thay đổi.");
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

async function loadUniverseSymbols(baseUrl, universe) {
  const normalizedUniverse = (universe || "").trim().toUpperCase();
  const payload = await requestJson(
    `${baseUrl}/api/agentic/market-universes/${encodeURIComponent(normalizedUniverse)}`,
  );
  const rawSymbols = payload?.data?.symbols;
  if (!Array.isArray(rawSymbols)) {
    throw new Error(`Backend không trả về danh sách mã hợp lệ cho rổ ${normalizedUniverse}.`);
  }

  const symbols = [...new Set(
    rawSymbols
      .filter((symbol) => typeof symbol === "string")
      .map((symbol) => symbol.trim().toUpperCase())
      .filter(Boolean),
  )];
  if (symbols.length === 0) {
    throw new Error(`Rổ ${normalizedUniverse} không có mã nào (kiểm tra bảng MarketIndex).`);
  }
  return symbols;
}

// ─────────────────────────────────────────────────────────────────────────────
// STOCKRIUM LAB LOGIN
// ─────────────────────────────────────────────────────────────────────────────
function setAuthBadge(type, text) {
  if (!els.authBadge) return;
  els.authBadge.classList.remove("ok", "error", "running");
  if (type) els.authBadge.classList.add(type);
  els.authBadge.textContent = text;
}

function accessTokenExpiresAt(token) {
  try {
    const payloadPart = token.split(".")[1];
    const base64 = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    const payload = JSON.parse(atob(padded));
    return Number(payload.exp) * 1000;
  } catch {
    return 0;
  }
}

function scheduleTokenRefresh() {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
  if (!accessToken || !sessionRefreshToken) return;

  const expiresAt = accessTokenExpiresAt(accessToken);
  // Refresh one minute before expiry. If the JWT cannot be decoded, use the
  // current backend default of a ten-minute refresh cadence.
  const delay = expiresAt
    ? Math.max(expiresAt - Date.now() - 60_000, 5_000)
    : 10 * 60_000;
  refreshTimer = setTimeout(async () => {
    try {
      await refreshSession();
    } catch (error) {
      clearSession(error.message || "Phiên đăng nhập đã hết hạn.", true);
    }
  }, delay);
}

async function refreshSession() {
  if (refreshPromise) return refreshPromise;
  if (!apiBaseUrl || !sessionRefreshToken) {
    throw new Error("Phiên đăng nhập không thể gia hạn. Vui lòng đăng nhập lại.");
  }

  const refreshContextVersion = userContextVersion;
  const tokenToRefresh = sessionRefreshToken;
  const activeRefreshPromise = (async () => {
    const response = await fetch(`${apiBaseUrl}/api/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ refresh_token: tokenToRefresh }),
    });
    const payload = await response.json().catch(() => null);
    const newToken = payload?.data?.token;
    if (refreshContextVersion !== userContextVersion) {
      throw new Error("Phiên người dùng đã thay đổi.");
    }
    if (!response.ok || !payload?.result || !newToken) {
      throw new Error(payload?.errorDesc || "Phiên đăng nhập đã hết hạn.");
    }

    accessToken = newToken;
    sessionRefreshToken = payload.data.refresh_token || sessionRefreshToken;
    scheduleTokenRefresh();
    appendLog("Phiên đăng nhập đã được tự động gia hạn.");
    return accessToken;
  })();
  refreshPromise = activeRefreshPromise;

  try {
    return await activeRefreshPromise;
  } finally {
    if (refreshPromise === activeRefreshPromise) refreshPromise = null;
  }
}

function clearUserOwnedView() {
  vn30SummaryData = [];
  analyzeSummaryData = [];
  [charts.price, charts.rsi, charts.macd, charts.kdj]
    .filter(Boolean)
    .forEach((chart) => {
      try {
        chart.remove();
      } catch {
        // The chart may already have been detached by a previous render.
      }
    });
  charts = {
    price: null,
    rsi: null,
    macd: null,
    kdj: null,
    candlestickSeries: null,
    tpSLSeries: [],
  };
  if (els.cloudHistoryList) {
    els.cloudHistoryList.innerHTML = '<p class="hint">Đăng nhập để tải lịch sử của bạn.</p>';
  }
  if (els.experimentHistoryBody) {
    els.experimentHistoryBody.innerHTML = '<tr><td colspan="8" class="hint">Đăng nhập để tải lịch sử của bạn.</td></tr>';
  }
  if (els.experimentDetailCard) els.experimentDetailCard.style.display = "none";
  if (els.experimentCompareCard) els.experimentCompareCard.style.display = "none";
  if (els.experimentComparisonContent) els.experimentComparisonContent.innerHTML = "";
  comparisonLoading = false;
  selectedExperimentIds.clear();
  updateExperimentSelectionUi();
  if (els.experimentConfiguration) els.experimentConfiguration.textContent = "";
  if (els.experimentResultData) els.experimentResultData.textContent = "";
  if (els.experimentReproducibility) els.experimentReproducibility.textContent = "";
  currentExperimentBundle = null;
  if (els.vn30ResultsBody) els.vn30ResultsBody.innerHTML = "";
  if (els.analyzeResultsBody) els.analyzeResultsBody.innerHTML = "";
  if (els.tradeLogsBody) els.tradeLogsBody.innerHTML = "";
  if (els.agentReportList) els.agentReportList.innerHTML = "";
  if (els.agentReportDetail) els.agentReportDetail.innerHTML = "";
  if (els.vn30Logs) els.vn30Logs.textContent = "";
  if (els.analyzeLogs) els.analyzeLogs.textContent = "";
  if (els.vn30ResultsCard) els.vn30ResultsCard.style.display = "none";
  if (els.vn30ProgressCard) els.vn30ProgressCard.style.display = "none";
  if (els.vizWrapper) els.vizWrapper.style.display = "none";
  if (els.agentReportCard) els.agentReportCard.style.display = "none";
  if (els.tradeDetailPanel) els.tradeDetailPanel.style.display = "none";
  if (els.analyzeSingleResult) {
    els.analyzeSingleResult.innerHTML = "";
    els.analyzeSingleResult.style.display = "none";
  }
  if (els.analyzeProgressCard) els.analyzeProgressCard.style.display = "none";
  if (els.analyzeResultsCard) els.analyzeResultsCard.style.display = "none";
  if (els.analyzeDetailPanel) {
    els.analyzeDetailPanel.innerHTML = "";
    els.analyzeDetailPanel.style.display = "none";
  }
}

function clearSession(message = "", preserveUserContext = false) {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
  accessToken = null;
  sessionRefreshToken = null;
  refreshPromise = null;
  if (!preserveUserContext) {
    userContextVersion += 1;
    currentUserId = null;
    clearUserOwnedView();
  }
  els.passwordInput.value = "";
  els.loginError.textContent = message;
  els.loginCard.hidden = false;
  document.body.classList.add("auth-required");
  setAuthBadge("error", "Chưa đăng nhập");
}

function showLab(email) {
  els.loginError.textContent = "";
  els.passwordInput.value = "";
  els.loginCard.hidden = true;
  document.body.classList.remove("auth-required");
  setAuthBadge("ok", email || "Đã đăng nhập");
}

async function loginToLab(event) {
  event?.preventDefault();
  const baseUrl = apiBaseUrl;
  const email = els.emailInput.value.trim();
  const password = els.passwordInput.value;
  if (!baseUrl) {
    els.loginError.textContent = "Stockrium Lab chưa được cấu hình địa chỉ backend.";
    return false;
  }
  if (!email || !password) return false;

  els.loginBtn.disabled = true;
  els.loginError.textContent = "";
  setAuthBadge("running", "Đang đăng nhập...");

  try {
    const loginResponse = await fetch(`${baseUrl}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const loginPayload = await loginResponse.json();
    if (!loginResponse.ok || !loginPayload?.result || !loginPayload?.data?.token) {
      throw new Error(loginPayload?.errorDesc || "Đăng nhập không thành công.");
    }

    const candidateToken = loginPayload.data.token;
    const candidateRefreshToken = loginPayload.data.refresh_token || null;
    const sessionResponse = await fetch(`${baseUrl}/api/auth/me`, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${candidateToken}`,
      },
    });
    const sessionPayload = await sessionResponse.json();
    if (!sessionResponse.ok || !sessionPayload?.result || !sessionPayload?.data?.user_id) {
      if (candidateRefreshToken) {
        await fetch(`${baseUrl}/api/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ refresh_token: candidateRefreshToken }),
        });
      }
      throw new Error(sessionPayload?.errorDesc || "Không thể xác minh phiên đăng nhập.");
    }

    if (currentUserId && currentUserId !== sessionPayload.data.user_id) {
      clearUserOwnedView();
    }
    userContextVersion += 1;
    accessToken = candidateToken;
    sessionRefreshToken = candidateRefreshToken;
    currentUserId = sessionPayload.data.user_id;
    scheduleTokenRefresh();
    showLab(sessionPayload.data.email);
    appendLog("Đăng nhập thành công.");
    loadCloudHistory();
    loadExperimentHistory();
    return true;
  } catch (error) {
    clearSession(error.message);
    appendLog(`Đăng nhập thất bại: ${error.message}`);
    return false;
  } finally {
    els.loginBtn.disabled = false;
  }
}

async function logoutFromLab() {
  const baseUrl = apiBaseUrl;
  const refreshToken = sessionRefreshToken;
  clearSession("Đã đăng xuất.");
  if (!baseUrl || !refreshToken) return;
  try {
    await fetch(`${baseUrl}/api/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // Local credentials are already cleared; server expiry is the fallback.
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB SWITCHING
// ─────────────────────────────────────────────────────────────────────────────
function initTabs() {
  const tabs = [
    { btn: els.tabBacktestBtn, content: els.backtestTabContent },
    { btn: els.tabAnalyzeBtn, content: els.analyzeTabContent },
    { btn: els.tabHistoryBtn, content: els.historyTabContent },
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
const TECH_INDICATOR_LABELS = {
  ma: "MA Crossover",
  boll: "Bollinger Bands",
  rsi: "RSI",
  macd: "MACD",
  kdj: "KDJ",
};
const BACKTEST_FLOW_SUMMARIES = {
  full: "Full pipeline: kỹ thuật 5/5 + tin tức + cơ bản; trọng số mid-term là kỹ thuật 40%, tin tức 20%, cơ bản 40%.",
  technical_all: "Technical-only: dùng cả 5 chỉ báo; không gọi nhánh tin tức và cơ bản.",
  technical_single: "Single-indicator AI pipeline: chỉ dùng một chỉ báo kỹ thuật đã chọn.",
  custom: "Tùy chỉnh nguồn dữ liệu, chỉ báo kỹ thuật và trọng số phân tích.",
};
const VN30_BACKTEST_CHECKPOINT_PREFIX = "stockrium.lab.vn30-backtest.v2";

function vn30CheckpointKey() {
  if (!currentUserId) return null;
  return `${VN30_BACKTEST_CHECKPOINT_PREFIX}.${encodeURIComponent(currentUserId)}`;
}

function vn30CheckpointSignature(baseUrl, baseParams, tickers) {
  const { symbol: _ignoredSymbol, ...parameters } = baseParams;
  return JSON.stringify({
    apiBaseUrl: normalizeBaseUrl(baseUrl),
    parameters,
    tickers: [...tickers].sort(),
  });
}

function loadVn30Checkpoint(baseUrl, baseParams, tickers) {
  try {
    const checkpointKey = vn30CheckpointKey();
    if (!checkpointKey) return null;
    const raw = localStorage.getItem(checkpointKey);
    if (!raw) return null;
    const checkpoint = JSON.parse(raw);
    const expectedSignature = vn30CheckpointSignature(
      baseUrl,
      baseParams,
      tickers,
    );
    if (
      checkpoint?.version !== 2
      || checkpoint?.signature !== expectedSignature
      || !Array.isArray(checkpoint?.rows)
    ) {
      return null;
    }
    return checkpoint;
  } catch (error) {
    appendLog(`Không thể đọc checkpoint VN30: ${error.message}`);
    return null;
  }
}

function saveVn30Checkpoint(baseUrl, baseParams, tickers) {
  try {
    const checkpointKey = vn30CheckpointKey();
    if (!checkpointKey) return;
    const rows = vn30SummaryData.map(({ vizData: _vizData, ...row }) => row);
    localStorage.setItem(
      checkpointKey,
      JSON.stringify({
        version: 2,
        signature: vn30CheckpointSignature(baseUrl, baseParams, tickers),
        updatedAt: new Date().toISOString(),
        rows,
      }),
    );
  } catch (error) {
    appendLog(`Không thể lưu checkpoint VN30: ${error.message}`);
  }
}

function clearVn30Checkpoint() {
  try {
    const checkpointKey = vn30CheckpointKey();
    if (checkpointKey) localStorage.removeItem(checkpointKey);
  } catch (error) {
    appendLog(`Không thể xóa checkpoint VN30: ${error.message}`);
  }
}

function removeVn30Result(ticker) {
  vn30SummaryData = vn30SummaryData.filter((row) => row.ticker !== ticker);
  els.vn30ResultsBody
    ?.querySelector(`tr[data-ticker="${ticker}"]`)
    ?.remove();
}

function upsertVn30Result(row) {
  removeVn30Result(row.ticker);
  vn30SummaryData.push(row);
  addVn30TableRow(
    row.ticker,
    row.pnl,
    row.winRate,
    row.tradesCount,
    row.sharpe,
    row.status,
    row.vizData,
    row.error || "",
  );
}

function getBacktestFlow() {
  const activeBtn = els.backtestFlowControl?.querySelector(".seg-btn.active");
  return activeBtn ? activeBtn.dataset.flow : "full";
}

function getBacktestMode() {
  return getBacktestFlow() === "full" ? "auto" : "manual";
}

function readChecks(selector, keys) {
  const result = {};
  keys.forEach((k) => {
    const el = document.querySelector(`${selector}[value="${k}"]`);
    result[k] = el ? el.checked : true;
  });
  return result;
}

function readWeightSelection(newsInput, technicalInput, fundamentalInput) {
  const percentages = {
    news: Number(newsInput?.value),
    technical: Number(technicalInput?.value),
    fundamental: Number(fundamentalInput?.value),
  };

  if (Object.values(percentages).some((value) => !Number.isFinite(value) || value < 0 || value > 100 || !Number.isInteger(value))) {
    throw new Error("Mỗi trọng số phải là số nguyên trong khoảng 0–100%.");
  }

  const total = percentages.news + percentages.technical + percentages.fundamental;
  if (Math.abs(total - 100) > 0.001) {
    throw new Error(`Tổng trọng số phải bằng 100% (hiện tại ${total}%).`);
  }

  return {
    news: percentages.news / 100,
    technical: percentages.technical / 100,
    fundamental: percentages.fundamental / 100,
  };
}

function redistributeWeights(inputs, enabled) {
  const order = ["technical", "fundamental", "news"];
  const active = order.filter((key) => enabled[key]);
  const next = { news: 0, technical: 0, fundamental: 0 };
  let remaining = 100;

  active.forEach((key, index) => {
    const value = index === active.length - 1
      ? remaining
      : Math.floor(100 / active.length);
    next[key] = value;
    remaining -= value;
  });

  order.forEach((key) => {
    if (!inputs[key]) return;
    inputs[key].value = next[key];
    inputs[key].disabled = !enabled[key];
  });
}

function bindRequiredTechnical(selector, updateCount) {
  document.querySelectorAll(selector).forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      const checkedCount = document.querySelectorAll(`${selector}:checked`).length;
      if (checkedCount === 0) {
        checkbox.checked = true;
        alert("Phải giữ lại ít nhất một chỉ báo kỹ thuật.");
      }
      updateCount();
    });
  });
}

function getDataSelection() {
  return {
    news: els.dsNews ? els.dsNews.checked : true,
    technical: readChecks(".ds-tech", DS_TECH_KEYS),
    fundamental: els.dsFundamental ? els.dsFundamental.checked : true,
    weight: readWeightSelection(
      els.dsWeightNews,
      els.dsWeightTechnical,
      els.dsWeightFundamental,
    ),
  };
}

function getBacktestParams(symbolOverride = null) {
  const mode = getBacktestMode();
  const params = {
    symbol: symbolOverride || els.backtestSymbol.value.trim().toUpperCase() || "FPT",
    start_date: els.startDate.value || null,
    end_date: els.endDate.value || null,
    market_symbol: els.marketSymbol.value.trim().toUpperCase() || "VNINDEX",
    max_hold_candles: parseInt(els.maxHoldCandles.value) || 20,
    exit_on_score_drop: els.exitOnScoreDrop.checked,
    mode,
  };
  if (mode === "manual") {
    params.data_selection = getDataSelection();
  }
  return params;
}

function updateDsCounts() {
  const techOn = DS_TECH_KEYS.filter((k) => document.querySelector(`.ds-tech[value="${k}"]`)?.checked).length;
  if (els.dsTechCount) els.dsTechCount.textContent = `${techOn}/${DS_TECH_KEYS.length}`;
}

function setTechnicalSelection(selectedKeys) {
  const selected = new Set(selectedKeys);
  document.querySelectorAll(".ds-tech").forEach((checkbox) => {
    checkbox.checked = selected.has(checkbox.value);
  });
  updateDsCounts();
}

function setWeightValues(news, technical, fundamental) {
  if (els.dsWeightNews) els.dsWeightNews.value = news;
  if (els.dsWeightTechnical) els.dsWeightTechnical.value = technical;
  if (els.dsWeightFundamental) els.dsWeightFundamental.value = fundamental;
}

function setBacktestControlsLocked(locked) {
  if (els.dsNews) els.dsNews.disabled = locked;
  if (els.dsFundamental) els.dsFundamental.disabled = locked;
  document.querySelectorAll(".ds-tech").forEach((checkbox) => {
    checkbox.disabled = locked;
  });

  if (locked) {
    [els.dsWeightNews, els.dsWeightTechnical, els.dsWeightFundamental]
      .filter(Boolean)
      .forEach((input) => { input.disabled = true; });
  }
}

function applyBacktestFlow(flow) {
  const normalizedFlow = BACKTEST_FLOW_SUMMARIES[flow] ? flow : "full";
  els.backtestFlowControl?.querySelectorAll(".seg-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.flow === normalizedFlow);
  });

  const isFull = normalizedFlow === "full";
  const isSingle = normalizedFlow === "technical_single";
  const isCustom = normalizedFlow === "custom";

  if (els.dataSelectionPanel) {
    els.dataSelectionPanel.style.display = isFull ? "none" : "flex";
  }
  if (els.singleIndicatorField) {
    els.singleIndicatorField.style.display = isSingle ? "grid" : "none";
  }

  if (normalizedFlow === "full") {
    if (els.dsNews) els.dsNews.checked = true;
    if (els.dsFundamental) els.dsFundamental.checked = true;
    setTechnicalSelection(DS_TECH_KEYS);
    setWeightValues(20, 40, 40);
  } else if (normalizedFlow === "technical_all") {
    if (els.dsNews) els.dsNews.checked = false;
    if (els.dsFundamental) els.dsFundamental.checked = false;
    setTechnicalSelection(DS_TECH_KEYS);
    setWeightValues(0, 100, 0);
  } else if (normalizedFlow === "technical_single") {
    if (els.dsNews) els.dsNews.checked = false;
    if (els.dsFundamental) els.dsFundamental.checked = false;
    setTechnicalSelection([els.singleIndicatorSelect?.value || "rsi"]);
    setWeightValues(0, 100, 0);
  }

  setBacktestControlsLocked(!isCustom);
  if (isCustom) {
    redistributeWeights(
      {
        news: els.dsWeightNews,
        technical: els.dsWeightTechnical,
        fundamental: els.dsWeightFundamental,
      },
      {
        news: els.dsNews?.checked !== false,
        technical: true,
        fundamental: els.dsFundamental?.checked !== false,
      },
    );
  }

  if (els.singleIndicatorSelect) {
    els.singleIndicatorSelect.disabled = !isSingle;
  }
  if (els.backtestFlowSummary) {
    els.backtestFlowSummary.textContent = BACKTEST_FLOW_SUMMARIES[normalizedFlow];
  }
  updateDsCounts();
}

function initDataSelectionControls() {
  if (!els.backtestFlowControl) return;

  els.backtestFlowControl.querySelectorAll(".seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyBacktestFlow(btn.dataset.flow);
    });
  });

  bindRequiredTechnical(".ds-tech", updateDsCounts);

  els.singleIndicatorSelect?.addEventListener("change", () => {
    if (getBacktestFlow() === "technical_single") {
      setTechnicalSelection([els.singleIndicatorSelect.value]);
    }
  });

  const weightInputs = {
    news: els.dsWeightNews,
    technical: els.dsWeightTechnical,
    fundamental: els.dsWeightFundamental,
  };
  const updateSourceWeights = () => {
    if (getBacktestFlow() !== "custom") return;
    redistributeWeights(weightInputs, {
      news: els.dsNews?.checked !== false,
      technical: true,
      fundamental: els.dsFundamental?.checked !== false,
    });
  };
  els.dsNews?.addEventListener("change", updateSourceWeights);
  els.dsFundamental?.addEventListener("change", updateSourceWeights);
  applyBacktestFlow(getBacktestFlow());
}

async function runBacktest() {
  const baseUrl = apiBaseUrl;
  if (!baseUrl) {
    alert("Không thể chạy backtest: dịch vụ backend chưa được cấu hình.");
    return;
  }

  const runVn30 = els.vn30Option.checked;
  let baseParams;
  try {
    baseParams = getBacktestParams();
  } catch (error) {
    alert(`Cấu hình backtest không hợp lệ: ${error.message}`);
    return;
  }
  els.runBacktestBtn.disabled = true;

  let vn30Tickers = [];
  if (runVn30) {
    els.runBacktestBtn.textContent = "Đang tải rổ VN30...";
    try {
      vn30Tickers = await loadUniverseSymbols(baseUrl, "VN30");
    } catch (error) {
      appendLog(`Lỗi tải rổ VN30: ${error.message}`);
      alert(`Không thể tải rổ VN30: ${error.message}`);
      els.runBacktestBtn.disabled = false;
      els.runBacktestBtn.textContent = "Chạy Backtest Pipeline";
      return;
    }
  }

  if (!runVn30) {
    // SINGLE ticker run
    const params = baseParams;
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
      loadExperimentHistory();
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
    const checkpoint = loadVn30Checkpoint(
      baseUrl,
      baseParams,
      vn30Tickers,
    );
    vn30SummaryData = (checkpoint?.rows || [])
      .filter((row) => vn30Tickers.includes(row?.ticker))
      .map((row) => ({ ...row, vizData: null }));
    vn30SummaryData.forEach((row) => {
      addVn30TableRow(
        row.ticker,
        row.pnl,
        row.winRate,
        row.tradesCount,
        row.sharpe,
        row.status,
        null,
        row.error || "",
      );
    });

    const completedSymbols = new Set(
      vn30SummaryData
        .filter((row) => row.status === "OK")
        .map((row) => row.ticker),
    );
    let completedCount = completedSymbols.size;
    let batchInterrupted = false;
    updateProgressBar(completedCount, vn30Tickers.length);

    if (completedCount > 0) {
      appendVn30Log(
        `↩️ Khôi phục checkpoint: ${completedCount}/${vn30Tickers.length} mã đã hoàn thành.`,
      );
      appendLog(`Tiếp tục batch VN30 từ checkpoint (${completedCount}/${vn30Tickers.length}).`);
    } else {
      appendLog(`Bắt đầu chạy backtest tuần tự rổ VN30 (${vn30Tickers.length} mã)...`);
    }

    for (let i = 0; i < vn30Tickers.length; i++) {
      const ticker = vn30Tickers[i];
      if (completedSymbols.has(ticker)) {
        appendVn30Log(`[${i + 1}/${vn30Tickers.length}] Bỏ qua ${ticker}: đã hoàn thành trong checkpoint.`);
        continue;
      }

      removeVn30Result(ticker);
      updateProgressBar(completedCount, vn30Tickers.length, `Đang xử lý ${ticker} (${i + 1}/${vn30Tickers.length})...`);

      const params = { ...baseParams, symbol: ticker };
      appendVn30Log(`[${i + 1}/${vn30Tickers.length}] Khởi động chạy backtest cho ${ticker}...`);

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

          upsertVn30Result({
            ticker,
            pnl,
            winRate,
            tradesCount,
            sharpe,
            status: "OK",
            vizData
          });
        } else {
          throw new Error("Dữ liệu rỗng");
        }
      } catch (err) {
        appendVn30Log(`❌ ${ticker} thất bại: ${err.message}`);

        upsertVn30Result({
          ticker,
          pnl: "N/A",
          winRate: "N/A",
          tradesCount: "N/A",
          sharpe: "N/A",
          status: "Lỗi",
          vizData: null,
          error: err.message,
        });
      }

      completedCount++;
      saveVn30Checkpoint(baseUrl, baseParams, vn30Tickers);
      updateProgressBar(completedCount, vn30Tickers.length, `Đang chạy: ${completedCount}/${vn30Tickers.length}`);

      if (!accessToken) {
        batchInterrupted = true;
        appendVn30Log("⏸️ Batch đã tạm dừng vì phiên đăng nhập không thể gia hạn. Đăng nhập rồi chạy lại để tiếp tục.");
        updateProgressBar(
          completedCount,
          vn30Tickers.length,
          `Tạm dừng tại ${completedCount}/${vn30Tickers.length}`,
        );
        break;
      }

      // Delay briefly between sequential API calls to prevent blocking
      await new Promise(resolve => setTimeout(resolve, 300));
    }

    const successfulCount = vn30SummaryData.filter((row) => row.status === "OK").length;
    const failedCount = vn30SummaryData.filter((row) => row.status !== "OK").length;
    if (successfulCount === vn30Tickers.length) {
      clearVn30Checkpoint();
      appendVn30Log(`🎉 Đã hoàn thành toàn bộ ${vn30Tickers.length} mã VN30!`);
      updateProgressBar(vn30Tickers.length, vn30Tickers.length, "Hoàn tất rổ VN30");
      appendLog("Chạy batch VN30 hoàn tất.");
    } else if (!batchInterrupted) {
      appendVn30Log(`⚠️ Kết thúc lượt chạy: ${successfulCount} thành công, ${failedCount} lỗi. Chạy lại để retry các mã lỗi.`);
      updateProgressBar(completedCount, vn30Tickers.length, `Còn ${vn30Tickers.length - successfulCount} mã cần chạy lại`);
    }
    loadCloudHistory();
    loadExperimentHistory();
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
  tr.dataset.ticker = ticker;
  const pnlNum = parseFloat(pnl);
  const pnlClass = isNaN(pnlNum) ? "" : (pnlNum >= 0 ? "text-green font-semibold" : "text-red font-semibold");
  const statusClass = status === "OK" ? "badge ok" : "badge error";
  const canView = status === "OK" && Boolean(vizData);

  tr.innerHTML = `
    <td><strong>${escapeHtml(ticker)}</strong></td>
    <td class="${pnlClass}">${escapeHtml(pnl)}</td>
    <td>${escapeHtml(winRate)}</td>
    <td>${escapeHtml(trades)}</td>
    <td>${escapeHtml(sharpe)}</td>
    <td><span class="${statusClass}" title="${escapeHtml(errMsg)}">${escapeHtml(status)}</span></td>
    <td style="text-align: center;">
      <button class="btn btn-ghost btn-view-vn30-viz" type="button" style="padding: 4px 10px; font-size: 0.75rem;" ${canView ? "" : "disabled"}>Xem</button>
    </td>
  `;

  if (canView) {
    tr.querySelector(".btn-view-vn30-viz").addEventListener("click", () => {
      renderVisualization(vizData);
    });
  }

  els.vn30ResultsBody.appendChild(tr);
}

function resetVn30Checkpoint() {
  if (els.runBacktestBtn.disabled) {
    alert("Không thể xóa checkpoint khi backtest đang chạy.");
    return;
  }
  if (!confirm("Xóa toàn bộ tiến độ VN30 đã lưu để chạy lại từ đầu?")) return;

  clearVn30Checkpoint();
  vn30SummaryData = [];
  els.vn30ResultsBody.innerHTML = "";
  els.vn30Logs.textContent = "Checkpoint đã được xóa. Lần chạy VN30 tiếp theo sẽ bắt đầu từ đầu.";
  updateProgressBar(0, 1, "Chưa bắt đầu");
  appendLog("Đã xóa checkpoint backtest VN30.");
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
  const baseUrl = apiBaseUrl;
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
            const fileUrl = new URL(file.json_url, `${baseUrl}/`).toString();
            const vizData = await requestJson(fileUrl);
            
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
function normalizeBacktestConfiguration(vizData) {
  const raw = vizData?.configuration || {};
  const reports = Array.isArray(vizData?.agent_reports) ? vizData.agent_reports : [];
  const sampleReport = reports.find((report) => report && !report.error) || {};
  const reportTechnical = sampleReport?.agent_breakdown?.technical_agent?.indicators;
  const hasIndicatorMetadata = Array.isArray(raw.selected_indicators);
  const selectedIndicators = hasIndicatorMetadata
    ? raw.selected_indicators.filter((name) => DS_TECH_KEYS.includes(name))
    : (reportTechnical && typeof reportTechnical === "object"
      ? DS_TECH_KEYS.filter((name) => Object.prototype.hasOwnProperty.call(reportTechnical, name))
      : [...DS_TECH_KEYS]);
  const reportSources = Array.isArray(sampleReport.data_sources_used)
    ? sampleReport.data_sources_used
    : [];
  const dataSources = Array.isArray(raw.data_sources) && raw.data_sources.length
    ? raw.data_sources
    : (reportSources.length ? reportSources : ["technical", "article", "fundamental"]);
  const weights = raw.weights && typeof raw.weights === "object"
    ? raw.weights
    : { news: 0.20, technical: 0.40, fundamental: 0.40 };

  return {
    mode: raw.mode || "legacy",
    period: raw.period || "mid_term",
    interval: raw.interval || "1d",
    dataSources,
    selectedIndicators: selectedIndicators.length ? selectedIndicators : [...DS_TECH_KEYS],
    weights,
    hasMetadata: Object.keys(raw).length > 0,
  };
}

function backtestFlowPresentation(configuration) {
  const sources = new Set(configuration.dataSources);
  const indicators = configuration.selectedIndicators;
  const technicalOnly = sources.size === 1 && sources.has("technical");

  if (configuration.mode === "auto") {
    return {
      title: "Full pipeline — Kỹ thuật + Tin tức + Cơ bản",
      pipelineLabel: "Full Pipeline (AI)",
      baselineLabel: "Technical Baseline (5/5)",
    };
  }
  if (technicalOnly && indicators.length === DS_TECH_KEYS.length) {
    return {
      title: "Technical-only — 5/5 chỉ báo",
      pipelineLabel: "Technical AI (5/5)",
      baselineLabel: "Engine-only (5/5)",
    };
  }
  if (technicalOnly && indicators.length === 1) {
    const indicatorLabel = TECH_INDICATOR_LABELS[indicators[0]] || indicators[0];
    return {
      title: `Technical-only — ${indicatorLabel}`,
      pipelineLabel: `Technical AI (${indicatorLabel})`,
      baselineLabel: `Engine-only (${indicatorLabel})`,
    };
  }
  if (!configuration.hasMetadata) {
    return {
      title: "Backtest cũ — không có metadata cấu hình",
      pipelineLabel: "Pipeline AI",
      baselineLabel: "Baseline kỹ thuật",
    };
  }
  return {
    title: "Pipeline tùy chỉnh",
    pipelineLabel: "Custom Pipeline (AI)",
    baselineLabel: "Technical Baseline",
  };
}

function sourceLabel(source) {
  return {
    technical: "Kỹ thuật",
    article: "Tin tức",
    fundamental: "Cơ bản",
  }[source] || source;
}

function renderBacktestConfiguration(configuration) {
  const presentation = backtestFlowPresentation(configuration);
  els.vizFlowTitle.textContent = presentation.title;
  const sourceBadges = configuration.dataSources.map(
    (source) => `<span class="config-badge">${escapeHtml(sourceLabel(source))}</span>`,
  );
  const indicatorNames = configuration.selectedIndicators
    .map((name) => TECH_INDICATOR_LABELS[name] || name)
    .join(", ");
  const indicatorBadge = `<span class="config-badge">Chỉ báo: ${escapeHtml(indicatorNames)}</span>`;
  const periodBadge = `<span class="config-badge">mid-term · ${escapeHtml(configuration.interval)}</span>`;
  const weights = configuration.weights;
  const weightBadge = `<span class="config-badge">Trọng số Kỹ thuật/Tin tức/Cơ bản: ${Math.round((weights.technical || 0) * 100)}/${Math.round((weights.news || 0) * 100)}/${Math.round((weights.fundamental || 0) * 100)}%</span>`;
  els.vizConfigBadges.innerHTML = [
    ...sourceBadges,
    indicatorBadge,
    weightBadge,
    periodBadge,
  ].join("");
}

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
  const configuration = normalizeBacktestConfiguration(vizData);
  renderBacktestConfiguration(configuration);

  // 2b. Comparison table (Full vs Baseline) + Agent report panel
  renderComparison(vizData, configuration);
  renderAgentReports(vizData, configuration);

  // 3. Clear existing charts divs (destroys old graphs completely)
  els.priceChart.innerHTML = "";
  els.rsiChart.innerHTML = "";
  els.macdChart.innerHTML = "";
  els.kdjChart.innerHTML = "";
  const enabledIndicators = new Set(configuration.selectedIndicators);
  const hasData = (value) => Array.isArray(value) && value.length > 0;
  const showMa = enabledIndicators.has("ma") && hasData(vizData.sma20_data);
  const showBoll = enabledIndicators.has("boll") && hasData(vizData.bb_upper_data);
  const showRsi = enabledIndicators.has("rsi") && hasData(vizData.rsi_data);
  const showMacd = enabledIndicators.has("macd") && hasData(vizData.macd_line_data);
  const showKdj = enabledIndicators.has("kdj") && hasData(vizData.kdj_k_data);
  els.rsiChartBox.style.display = showRsi ? "flex" : "none";
  els.macdChartBox.style.display = showMacd ? "flex" : "none";
  els.kdjChartBox.style.display = showKdj ? "flex" : "none";
  els.indicatorChartsGrid.style.display = (showRsi || showMacd || showKdj)
    ? "grid"
    : "none";

  const priceTags = [];
  if (showMa) {
    priceTags.push('<span class="indicator-tag tag-sma20">SMA 20</span>');
    priceTags.push('<span class="indicator-tag tag-sma50">SMA 50</span>');
  }
  if (showBoll) {
    priceTags.push('<span class="indicator-tag">Bollinger Bands</span>');
  }
  els.priceIndicatorTags.innerHTML = priceTags.join("");
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
  const getSubchartWidth = (element) => (
    element.clientWidth || element.offsetWidth || (containerWidth / 2 - 8)
  );

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

  if (showMa) {
    const sma20Series = priceChart.addLineSeries({
      color: "#3b82f6",
      lineWidth: 1.5,
      title: "SMA 20",
    });
    sma20Series.setData(vizData.sma20_data || []);

    const sma50Series = priceChart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 1.5,
      title: "SMA 50",
    });
    sma50Series.setData(vizData.sma50_data || []);
  }

  if (showBoll) {
    [
      [vizData.bb_upper_data, "#38bdf8", "Bollinger Upper"],
      [vizData.bb_middle_data, "rgba(56, 189, 248, 0.55)", "Bollinger Middle"],
      [vizData.bb_lower_data, "#38bdf8", "Bollinger Lower"],
    ].forEach(([data, color, title]) => {
      const series = priceChart.addLineSeries({
        color,
        lineWidth: 1,
        title,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      series.setData(data || []);
    });
  }

  const createSubchart = (element) => LightweightCharts.createChart(element, {
    width: getSubchartWidth(element),
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

  let rsiChart = null;
  if (showRsi) {
    rsiChart = createSubchart(els.rsiChart);
    const rsiData = vizData.rsi_data || [];
    const rsiSeries = rsiChart.addLineSeries({
      color: "#a855f7",
      lineWidth: 1.5,
    });
    rsiSeries.setData(rsiData);

    const rsiUpper = rsiChart.addLineSeries({
      color: "rgba(168, 85, 247, 0.25)",
      lineWidth: 1,
      lineStyle: 1,
    });
    rsiUpper.setData(rsiData.map(d => ({ time: d.time, value: 70 })));

    const rsiLower = rsiChart.addLineSeries({
      color: "rgba(168, 85, 247, 0.25)",
      lineWidth: 1,
      lineStyle: 1,
    });
    rsiLower.setData(rsiData.map(d => ({ time: d.time, value: 30 })));
  }

  let macdChart = null;
  if (showMacd) {
    macdChart = createSubchart(els.macdChart);
    const macdLineSeries = macdChart.addLineSeries({
      color: "#2563eb",
      lineWidth: 1,
    });
    macdLineSeries.setData(vizData.macd_line_data || []);

    const macdSignalSeries = macdChart.addLineSeries({
      color: "#ea580c",
      lineWidth: 1,
    });
    macdSignalSeries.setData(vizData.macd_signal_data || []);

    const macdHistSeries = macdChart.addHistogramSeries({
      color: "#26a69a",
    });
    macdHistSeries.setData(vizData.macd_hist_data || []);
  }

  let kdjChart = null;
  if (showKdj) {
    kdjChart = createSubchart(els.kdjChart);
    [
      [vizData.kdj_k_data, "#38bdf8", "K"],
      [vizData.kdj_d_data, "#f59e0b", "D"],
      [vizData.kdj_j_data, "#f472b6", "J"],
    ].forEach(([data, color, title]) => {
      const series = kdjChart.addLineSeries({
        color,
        lineWidth: 1.25,
        title,
      });
      series.setData(data || []);
    });
  }

  // Synchronize only the charts enabled by the selected indicators.
  const synchronizedCharts = [priceChart, rsiChart, macdChart, kdjChart].filter(Boolean);
  let isScaling = false;
  synchronizedCharts.forEach((sourceChart) => {
    sourceChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (isScaling || !range) return;
      isScaling = true;
      synchronizedCharts.forEach((targetChart) => {
        if (targetChart !== sourceChart) {
          targetChart.timeScale().setVisibleLogicalRange(range);
        }
      });
      isScaling = false;
    });
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
      const tradeConfidence = confidenceInfo(trade.confidence);
      confBadge.innerText = tradeConfidence.text;
      confBadge.className = `badge ${tradeConfidence.cls}`;

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
  charts.kdj = kdjChart;
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

function renderComparison(vizData, configuration) {
  const baseline = vizData.baseline;
  if (!baseline || !baseline.metrics || Object.keys(baseline.metrics).length === 0) {
    els.comparisonCard.style.display = "none";
    return;
  }

  const full = vizData.metrics;
  const base = baseline.metrics;
  const presentation = backtestFlowPresentation(configuration);
  els.comparisonTitle.textContent = `So sánh: ${presentation.pipelineLabel} vs ${presentation.baselineLabel}`;
  els.pipelineColumnTitle.textContent = presentation.pipelineLabel;
  els.baselineColumnTitle.textContent = presentation.baselineLabel;
  els.comparisonDeltaTitle.textContent = `${presentation.pipelineLabel} − ${presentation.baselineLabel}`;

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

function isBuyRecommendation(rec) {
  if (typeof rec?.buy === "boolean") return rec.buy;
  return rec?.recommendation === "Mua";
}

function recommendationText(rec) {
  if (!rec) return "N/A";
  if (typeof rec.buy === "boolean") return rec.buy ? "Mua" : "Chờ";
  return rec.recommendation || "N/A";
}

function scoreOutOf100(value) {
  const score = Number(value);
  return Number.isFinite(score)
    ? `${Math.round(Math.min(Math.max(score, 0), 1) * 100)}/100`
    : "--";
}

function sourceScoreDisplay(configuration, source, value) {
  return configuration.dataSources.includes(source)
    ? scoreOutOf100(value)
    : "Tắt";
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function analysisSection(title, text) {
  if (!text) return "";
  return `<div class="agent-sub-block"><h4>${title}</h4><p class="agent-analysis-text">${escapeHtml(text)}</p></div>`;
}

function renderAgentReportDetail(report, configuration) {
  const rec = recommendationText(report);
  const conf = confidenceInfo(report.confidence);
  const analysis = report.analysis;
  const score = report.score && typeof report.score === "object"
    ? report.score
    : {};
  const totalScore = Number.isFinite(Number(score.total))
    ? scoreOutOf100(score.total)
    : (report.total_score ?? "--");
  const technicalScore = Number.isFinite(Number(score.technical))
    ? scoreOutOf100(score.technical)
    : (report.technical_total_score !== undefined
      ? `${report.technical_total_score}/5`
      : "--");

  const sources = Array.isArray(report.data_sources_used) && report.data_sources_used.length
    ? report.data_sources_used.map(sourceLabel).join(", ")
    : "--";
  const indicatorNames = configuration.selectedIndicators
    .map((name) => TECH_INDICATOR_LABELS[name] || name)
    .join(", ");

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
      <li><span class="lbl">Điểm tổng:</span> <span class="val">${totalScore}</span></li>
      <li><span class="lbl">Điểm kỹ thuật:</span> <span class="val">${technicalScore}</span></li>
      <li><span class="lbl">Điểm cơ bản:</span> <span class="val">${sourceScoreDisplay(configuration, "fundamental", score.fundamental)}</span></li>
      <li><span class="lbl">Điểm tin tức:</span> <span class="val">${sourceScoreDisplay(configuration, "article", score.news)}</span></li>
      <li><span class="lbl">Giá vào:</span> <span class="val">${report.entry_price ?? "--"}</span></li>
      <li><span class="lbl">Take Profit:</span> <span class="val text-green">${report.take_profit_price ?? "--"}</span></li>
      <li><span class="lbl">Stop Loss:</span> <span class="val text-red">${report.stop_loss_price ?? "--"}</span></li>
      <li><span class="lbl">Nến giữ tối đa:</span> <span class="val">${report.max_hold_candles ?? "--"}</span></li>
      <li><span class="lbl">Nguồn dữ liệu:</span> <span class="val">${escapeHtml(sources)}</span></li>
      <li><span class="lbl">Chỉ báo:</span> <span class="val">${escapeHtml(indicatorNames)}</span></li>
    </ul>
    ${analysisHtml}
  `;
}

function renderAgentReports(vizData, configuration) {
  // Chỉ hiển thị report cho các tín hiệu được khuyến nghị Mua.
  const reports = (Array.isArray(vizData.agent_reports) ? vizData.agent_reports : [])
    .filter((report) => isBuyRecommendation(report));

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
    const rec = recommendationText(report);
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
      renderAgentReportDetail(report, configuration);
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
    [
      [charts.rsi, els.rsiChart],
      [charts.macd, els.macdChart],
      [charts.kdj, els.kdjChart],
    ].forEach(([chart, element]) => {
      if (!chart) return;
      const subW = element.offsetWidth || element.clientWidth || (w / 2 - 8);
      chart.resize(subW, 180);
    });
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// AI ANALYZE TAB — single symbol or VN30/VN100 basket
// ─────────────────────────────────────────────────────────────────────────────
const AN_TECH_KEYS = ["ma", "boll", "rsi", "macd", "kdj"];

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
    fundamental: els.anFundamental ? els.anFundamental.checked : true,
    weight: readWeightSelection(
      els.anWeightNews,
      els.anWeightTechnical,
      els.anWeightFundamental,
    ),
  };
}

function updateAnalyzeDsCounts() {
  const techOn = AN_TECH_KEYS.filter((k) => document.querySelector(`.an-tech[value="${k}"]`)?.checked).length;
  if (els.anTechCount) els.anTechCount.textContent = `${techOn}/${AN_TECH_KEYS.length}`;
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

  bindRequiredTechnical(".an-tech", updateAnalyzeDsCounts);

  const weightInputs = {
    news: els.anWeightNews,
    technical: els.anWeightTechnical,
    fundamental: els.anWeightFundamental,
  };
  const updateSourceWeights = () => redistributeWeights(weightInputs, {
    news: els.anNews?.checked !== false,
    technical: true,
    fundamental: els.anFundamental?.checked !== false,
  });
  els.anNews?.addEventListener("change", updateSourceWeights);
  els.anFundamental?.addEventListener("change", updateSourceWeights);
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
  const recText = recommendationText(rec);
  const score = rec.score && typeof rec.score === "object" ? rec.score : {};
  const tradingPlanHtml = isBuyRecommendation(rec)
    ? `
      <li><span class="lbl">Giá vào:</span> <span class="val">${rec.entry_price ?? "--"}</span></li>
      <li><span class="lbl">Take Profit:</span> <span class="val text-green">${rec.take_profit_price ?? "--"}</span></li>
      <li><span class="lbl">Stop Loss:</span> <span class="val text-red">${rec.stop_loss_price ?? "--"}</span></li>
      <li><span class="lbl">Nến giữ tối đa:</span> <span class="val">${rec.max_hold_candles ?? "--"}</span></li>
    `
    : "";
  return `
    <div class="report-detail-header">
      <h3>${escapeHtml(symbol)}</h3>
      <div class="report-badges">
        <span class="badge ${recommendationBadgeClass(recText)}">${escapeHtml(recText)}</span>
        <span class="badge ${conf.cls}">${escapeHtml(conf.text)}</span>
      </div>
    </div>
    <ul class="detail-list">
      <li><span class="lbl">Điểm tổng:</span> <span class="val">${scoreOutOf100(score.total)}</span></li>
      <li><span class="lbl">Điểm kỹ thuật:</span> <span class="val">${scoreOutOf100(score.technical)}</span></li>
      <li><span class="lbl">Điểm cơ bản:</span> <span class="val">${scoreOutOf100(score.fundamental)}</span></li>
      <li><span class="lbl">Điểm tin tức:</span> <span class="val">${scoreOutOf100(score.news)}</span></li>
      ${tradingPlanHtml}
    </ul>
    ${analysisBlocksHtml(rec)}
    <div class="investment-warning-inline">
      <strong>Không phải khuyến nghị đầu tư.</strong> Kết quả AI chỉ dùng để nghiên cứu và thử nghiệm;
      dữ liệu hoặc mô hình có thể thay đổi và không bảo đảm hiệu quả tương lai.
    </div>
  `;
}

function renderSingleRecommendation(symbol, rec) {
  els.analyzeSingleResult.style.display = "block";
  els.analyzeSingleResult.innerHTML = recommendationDetailHtml(symbol, rec);
  els.analyzeSingleResult.scrollIntoView({ behavior: "smooth" });
}

function addAnalyzeTableRow(symbol, rec, status, errMsg = "") {
  const tr = document.createElement("tr");
  const recText = recommendationText(rec);
  const totalScore = rec ? scoreOutOf100(rec.score?.total) : "--";
  const conf = rec ? confidenceInfo(rec.confidence) : { text: "--", cls: "" };
  const summary = rec && rec.analysis && rec.analysis.summary ? rec.analysis.summary : "";
  const shortSummary = summary.length > 90 ? summary.slice(0, 90) + "…" : summary;
  const statusClass = status === "ok" ? "badge ok" : "badge error";
  const recClass = rec ? `badge ${recommendationBadgeClass(recText)}` : "badge";

  tr.innerHTML = `
    <td><strong>${escapeHtml(symbol)}</strong></td>
    <td><span class="${recClass}">${escapeHtml(recText)}</span></td>
    <td>${escapeHtml(totalScore)}</td>
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
  const baseUrl = apiBaseUrl;
  if (!baseUrl) {
    alert("Không thể phân tích: dịch vụ backend chưa được cấu hình.");
    return;
  }
  if (!accessToken) {
    alert("Vui lòng đăng nhập.");
    return;
  }

  const source = getAnalyzeSource();
  if (getAnalyzeMode() === "manual") {
    try {
      getAnalyzeDataSelection();
    } catch (error) {
      alert(`Cấu hình phân tích không hợp lệ: ${error.message}`);
      return;
    }
  }
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

      const payload = await requestJson(`${baseUrl}/api/agentic/experiments/analyze`, {
        method: "POST",
        body: buildAnalyzeBody(symbol),
      });
      const entry = payload?.data?.results?.[0];
      if (entry && entry.status === "ok" && entry.recommendation) {
        renderSingleRecommendation(symbol, entry.recommendation);
        appendLog(`Phân tích ${symbol} hoàn thành: ${recommendationText(entry.recommendation)}.`);
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
      const symbols = await loadUniverseSymbols(baseUrl, source);

      appendLog(`Bắt đầu phân tích rổ ${source} (${symbols.length} mã)...`);
      els.runAnalyzeBtn.textContent = `Đang chạy ${source}...`;

      for (let i = 0; i < symbols.length; i++) {
        const sym = symbols[i];
        updateAnalyzeProgress(i, symbols.length, `Đang xử lý ${sym} (${i + 1}/${symbols.length})...`);
        appendAnalyzeLog(`[${i + 1}/${symbols.length}] Phân tích ${sym}...`);

        try {
          const payload = await requestJson(`${baseUrl}/api/agentic/experiments/analyze`, {
            method: "POST",
            body: buildAnalyzeBody(sym),
          });
          const entry = payload?.data?.results?.[0];
          if (entry && entry.status === "ok" && entry.recommendation) {
            const rec = entry.recommendation;
            addAnalyzeTableRow(sym, rec, "ok");
            analyzeSummaryData.push({ symbol: sym, rec, status: "ok" });
            appendAnalyzeLog(`✅ ${sym}: ${recommendationText(rec)} (điểm ${scoreOutOf100(rec.score?.total)}, tự tin ${confidenceInfo(rec.confidence).text}).`);
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
    if (accessToken) loadExperimentHistory();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PERSONAL EXPERIMENT HISTORY
// ─────────────────────────────────────────────────────────────────────────────
function experimentTypeLabel(type) {
  return type === "backtest" ? "Backtest" : type === "analysis" ? "Phân tích AI" : type || "--";
}

function experimentStatusInfo(status) {
  if (status === "completed") return { label: "Hoàn thành", cls: "ok" };
  if (status === "failed") return { label: "Thất bại", cls: "error" };
  return { label: "Đang chạy", cls: "running" };
}

function formatExperimentPercent(value) {
  if (value === undefined || value === null || value === "") return "--";
  const number = Number(value);
  return Number.isFinite(number) ? `${(number * 100).toFixed(1)}%` : "--";
}

function experimentQuickSummary(experiment) {
  const summary = experiment?.result_summary || {};
  if (experiment?.status === "failed") {
    return experiment.error_message || "Thử nghiệm thất bại";
  }
  if (experiment?.status === "running") return "Đang xử lý...";
  if (experiment?.experiment_type === "backtest") {
    const profit = formatExperimentPercent(summary.net_profit);
    const winRate = formatExperimentPercent(summary.win_rate);
    const sharpe = summary.sharpe_ratio == null ? Number.NaN : Number(summary.sharpe_ratio);
    return `Lợi nhuận ${profit} · Win rate ${winRate} · Sharpe ${Number.isFinite(sharpe) ? sharpe.toFixed(2) : "--"}`;
  }
  if (summary.recommendation) {
    const score = Number(summary.score);
    return `${summary.recommendation} · Điểm ${Number.isFinite(score) ? scoreOutOf100(score) : "--"} · ${confidenceInfo(summary.confidence).text}`;
  }
  return `${summary.successful || 0}/${summary.count || 0} mã thành công`;
}

function updateExperimentSelectionUi() {
  const count = selectedExperimentIds.size;
  if (els.experimentSelectionCount) {
    els.experimentSelectionCount.textContent = `Đã chọn ${count}/${EXPERIMENT_COMPARE_LIMIT} thử nghiệm`;
  }
  if (els.compareExperimentsBtn) {
    els.compareExperimentsBtn.disabled = comparisonLoading || count < 2;
    els.compareExperimentsBtn.textContent = comparisonLoading ? "Đang tải so sánh..." : "So sánh đã chọn";
  }
  if (els.clearExperimentSelectionBtn) {
    els.clearExperimentSelectionBtn.disabled = comparisonLoading || count === 0;
  }
  document.querySelectorAll(".experiment-select-checkbox").forEach((checkbox) => {
    const selected = selectedExperimentIds.has(checkbox.dataset.experimentId);
    checkbox.checked = selected;
    checkbox.disabled = comparisonLoading || (!selected && count >= EXPERIMENT_COMPARE_LIMIT);
    checkbox.closest("tr")?.classList.toggle("experiment-row-selected", selected);
  });
}

function toggleExperimentSelection(experimentId, checked) {
  if (checked && selectedExperimentIds.size >= EXPERIMENT_COMPARE_LIMIT) {
    alert(`Chỉ có thể so sánh tối đa ${EXPERIMENT_COMPARE_LIMIT} thử nghiệm.`);
    updateExperimentSelectionUi();
    return;
  }
  if (checked) selectedExperimentIds.add(experimentId);
  else selectedExperimentIds.delete(experimentId);
  if (els.experimentCompareCard) els.experimentCompareCard.style.display = "none";
  updateExperimentSelectionUi();
}

function clearExperimentSelection() {
  selectedExperimentIds.clear();
  if (els.experimentCompareCard) els.experimentCompareCard.style.display = "none";
  if (els.experimentComparisonContent) els.experimentComparisonContent.innerHTML = "";
  updateExperimentSelectionUi();
}

function experimentModeLabel(mode) {
  return mode === "manual" ? "Thủ công" : mode === "auto" ? "Tự động" : mode || "--";
}

function riskPeriodLabel(period) {
  return ({
    short_term: "Ngắn hạn",
    mid_term: "Trung hạn",
    long_term: "Dài hạn",
  })[period] || period || "--";
}

function experimentDurationLabel(durationMs) {
  if (durationMs === undefined || durationMs === null || durationMs === "") return "--";
  const value = Number(durationMs);
  if (!Number.isFinite(value)) return "--";
  if (value < 1000) return `${Math.round(value)} ms`;
  if (value < 60_000) return `${(value / 1000).toFixed(1)} giây`;
  return `${(value / 60_000).toFixed(1)} phút`;
}

function experimentSourcesLabel(experiment) {
  const selection = experiment?.configuration?.data_selection;
  if (!selection) return experiment?.mode === "auto" ? "Tất cả nguồn (tự động)" : "--";
  const sources = [];
  if (selection.news !== false) sources.push("Tin tức");
  if (selection.technical && Object.values(selection.technical).some(Boolean)) sources.push("Kỹ thuật");
  if (selection.fundamental !== false) sources.push("Cơ bản");
  return sources.join(" + ") || "--";
}

function experimentTechnicalLabel(experiment) {
  const technical = experiment?.configuration?.data_selection?.technical;
  if (!technical) return "--";
  const selected = Object.entries(technical)
    .filter(([, enabled]) => enabled)
    .map(([key]) => TECH_INDICATOR_LABELS[key] || key.toUpperCase());
  return selected.join(", ") || "--";
}

function experimentWeightsLabel(experiment) {
  const weight = experiment?.configuration?.data_selection?.weight;
  if (!weight) return "Mặc định theo kỳ hạn";
  const percent = (value) => `${Math.round(Number(value || 0) * 100)}%`;
  return `Tin ${percent(weight.news)} · KT ${percent(weight.technical)} · CB ${percent(weight.fundamental)}`;
}

function comparisonValue(value) {
  return value === undefined || value === null || value === "" ? "--" : String(value);
}

function shortFingerprint(value) {
  const text = String(value || "");
  if (!text) return "--";
  return text.length > 12 ? `${text.slice(0, 12)}…` : text;
}

function reproducibilityLevelLabel(value) {
  return value === "configuration_only" ? "Tái lập cấu hình" : value || "--";
}

function buildComparisonSections() {
  const summary = (experiment) => experiment?.result_summary || {};
  const config = (experiment) => experiment?.configuration || {};
  const reproducibility = (experiment) => experiment?.reproducibility || {};
  const numeric = (getter) => (experiment) => {
    const rawValue = getter(experiment);
    if (rawValue === undefined || rawValue === null || rawValue === "") return null;
    const value = Number(rawValue);
    return Number.isFinite(value) ? value : null;
  };
  return [
    {
      title: "Thông tin thử nghiệm",
      rows: [
        { label: "Loại", value: (item) => experimentTypeLabel(item.experiment_type) },
        { label: "Mã / phạm vi", value: (item) => item.symbol || String(item.scope || "--").toUpperCase() },
        { label: "Chế độ", value: (item) => experimentModeLabel(item.mode) },
        { label: "Trạng thái", value: (item) => experimentStatusInfo(item.status).label },
        { label: "Thời điểm chạy", value: (item) => item.created_at ? new Date(item.created_at).toLocaleString("vi-VN") : "--" },
        { label: "Thời gian xử lý", value: (item) => experimentDurationLabel(item.duration_ms) },
      ],
    },
    {
      title: "Cấu hình dữ liệu",
      rows: [
        { label: "Kỳ hạn", value: (item) => riskPeriodLabel(config(item).risk_appetite?.period) },
        { label: "Nguồn dữ liệu", value: experimentSourcesLabel },
        { label: "Chỉ báo kỹ thuật", value: experimentTechnicalLabel },
        { label: "Trọng số", value: experimentWeightsLabel },
      ],
    },
    {
      title: "Tái lập và phiên bản",
      rows: [
        { label: "Fingerprint cấu hình", value: (item) => shortFingerprint(reproducibility(item).configuration_sha256) },
        { label: "Fingerprint lần chạy", value: (item) => shortFingerprint(reproducibility(item).run_fingerprint) },
        { label: "Phiên bản ứng dụng", value: (item) => reproducibility(item).application?.version || "--" },
        { label: "Code revision", value: (item) => shortFingerprint(reproducibility(item).application?.code_revision) },
        { label: "Pipeline", value: (item) => reproducibility(item).pipeline?.version || "--" },
        { label: "Prompt bundle", value: (item) => reproducibility(item).pipeline?.prompt_bundle_version || "--" },
        { label: "Mô hình AI", value: (item) => reproducibility(item).ai?.model || "--" },
        { label: "Dữ liệu", value: (item) => reproducibility(item).data?.snapshot_mode === "live_sources" ? "Nguồn live, chưa đóng băng" : reproducibility(item).data?.snapshot_mode || "--" },
        { label: "Mức tái lập", value: (item) => reproducibilityLevelLabel(reproducibility(item).reproducibility_level) },
      ],
    },
    {
      title: "Cấu hình backtest",
      rows: [
        { label: "Giai đoạn", value: (item) => config(item).start_date || config(item).end_date ? `${config(item).start_date || "--"} → ${config(item).end_date || "--"}` : "--" },
        { label: "Benchmark", value: (item) => config(item).market_symbol || "--" },
        { label: "Nắm giữ tối đa", value: (item) => config(item).max_hold_candles != null ? `${config(item).max_hold_candles} nến` : "--" },
        { label: "Thoát khi điểm giảm", value: (item) => config(item).exit_on_score_drop == null ? "--" : config(item).exit_on_score_drop ? "Có" : "Không" },
      ],
    },
    {
      title: "Kết quả backtest",
      rows: [
        { label: "Lợi nhuận ròng", value: (item) => formatExperimentPercent(summary(item).net_profit), score: numeric((item) => summary(item).net_profit) },
        { label: "Win rate", value: (item) => formatExperimentPercent(summary(item).win_rate), score: numeric((item) => summary(item).win_rate) },
        { label: "Số giao dịch", value: (item) => comparisonValue(summary(item).total_trades) },
        { label: "Sharpe ratio", value: (item) => summary(item).sharpe_ratio != null && Number.isFinite(Number(summary(item).sharpe_ratio)) ? Number(summary(item).sharpe_ratio).toFixed(2) : "--", score: numeric((item) => summary(item).sharpe_ratio) },
        { label: "Max drawdown", value: (item) => formatExperimentPercent(summary(item).max_drawdown), score: numeric((item) => summary(item).max_drawdown) },
      ],
    },
    {
      title: "Kết quả phân tích AI",
      rows: [
        { label: "Khuyến nghị", value: (item) => summary(item).recommendation || "--" },
        { label: "Điểm tổng", value: (item) => summary(item).score != null && Number.isFinite(Number(summary(item).score)) ? scoreOutOf100(summary(item).score) : "--", score: numeric((item) => summary(item).score) },
        { label: "Độ tự tin", value: (item) => summary(item).confidence == null ? "--" : confidenceInfo(summary(item).confidence).text, score: numeric((item) => summary(item).confidence) },
        { label: "Số mã thành công", value: (item) => summary(item).count == null ? "--" : `${summary(item).successful || 0}/${summary(item).count}` },
      ],
    },
  ];
}

function renderExperimentComparison(experiments) {
  const headerCells = experiments.map((item) => {
    const target = item.symbol || String(item.scope || "--").toUpperCase();
    return `<th><strong>${escapeHtml(item.name || "--")}</strong><br><span class="hint">${escapeHtml(experimentTypeLabel(item.experiment_type))} · ${escapeHtml(target)}</span></th>`;
  }).join("");

  const bodyRows = [];
  buildComparisonSections().forEach((section) => {
    const rows = section.rows.map((row) => ({
      ...row,
      values: experiments.map((item) => comparisonValue(row.value(item))),
      scores: row.score ? experiments.map((item) => row.score(item)) : [],
    })).filter((row) => row.values.some((value) => value !== "--"));
    if (rows.length === 0) return;

    bodyRows.push(`<tr class="experiment-comparison-section"><td colspan="${experiments.length + 1}">${escapeHtml(section.title)}</td></tr>`);
    rows.forEach((row) => {
      const finiteScores = row.scores.filter((value) => Number.isFinite(value));
      const bestScore = finiteScores.length >= 2 ? Math.max(...finiteScores) : null;
      const valueCells = row.values.map((value, index) => {
        const isBest = bestScore !== null && row.scores[index] === bestScore;
        return `<td class="${isBest ? "experiment-comparison-best" : ""}">${escapeHtml(value)}</td>`;
      }).join("");
      bodyRows.push(`<tr><td>${escapeHtml(row.label)}</td>${valueCells}</tr>`);
    });
  });

  els.experimentComparisonContent.innerHTML = `
    <table class="results-table experiment-comparison-table">
      <thead><tr><th>Tiêu chí</th>${headerCells}</tr></thead>
      <tbody>${bodyRows.join("")}</tbody>
    </table>
  `;
  els.experimentCompareCard.style.display = "block";
  els.experimentCompareCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function compareSelectedExperiments() {
  if (!apiBaseUrl || !accessToken || selectedExperimentIds.size < 2) return;
  comparisonLoading = true;
  updateExperimentSelectionUi();
  try {
    const experimentIds = [...selectedExperimentIds];
    const payload = await requestJson(`${apiBaseUrl}/api/agentic/experiments/compare`, {
      method: "POST",
      body: { experiment_ids: experimentIds },
    });
    const items = payload?.data?.items;
    if (!Array.isArray(items) || items.length !== experimentIds.length) {
      throw new Error("Không nhận đủ dữ liệu thử nghiệm để so sánh.");
    }
    renderExperimentComparison(items);
  } catch (error) {
    appendLog(`Lỗi so sánh thử nghiệm: ${error.message}`);
    alert(`Không thể so sánh thử nghiệm: ${error.message}`);
  } finally {
    comparisonLoading = false;
    updateExperimentSelectionUi();
  }
}

async function copyTextToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  document.body.removeChild(textarea);
  if (!copied) throw new Error("Trình duyệt không cho phép sao chép tự động.");
}

async function copyCurrentExperimentBundle() {
  if (!currentExperimentBundle) return;
  const originalLabel = els.copyExperimentBundleBtn.textContent;
  try {
    await copyTextToClipboard(JSON.stringify(currentExperimentBundle, null, 2));
    els.copyExperimentBundleBtn.textContent = "Đã sao chép";
    setTimeout(() => {
      els.copyExperimentBundleBtn.textContent = originalLabel;
    }, 1600);
  } catch (error) {
    alert(`Không thể sao chép gói tái lập: ${error.message}`);
  }
}

async function loadExperimentDetail(experimentId) {
  if (!apiBaseUrl || !accessToken || !experimentId) return;
  try {
    const payload = await requestJson(`${apiBaseUrl}/api/agentic/experiments/${encodeURIComponent(experimentId)}`);
    const experiment = payload?.data;
    if (!experiment) throw new Error("Không nhận được chi tiết thử nghiệm.");
    const reproducibility = experiment.reproducibility || {};
    const displayedReproducibility = Object.keys(reproducibility).length > 0
      ? reproducibility
      : { notice: "Experiment cũ chưa có metadata tái lập." };

    const statusInfo = experimentStatusInfo(experiment.status);
    els.experimentDetailTitle.textContent = experiment.name || "Chi tiết thử nghiệm";
    els.experimentDetailStatus.className = `badge ${statusInfo.cls}`;
    els.experimentDetailStatus.textContent = statusInfo.label;
    els.experimentConfiguration.textContent = JSON.stringify(experiment.configuration || {}, null, 2);
    els.experimentReproducibility.textContent = JSON.stringify(displayedReproducibility, null, 2);
    els.experimentResultData.textContent = JSON.stringify({
      summary: experiment.result_summary,
      data: experiment.result_data,
      result_reference: experiment.result_reference,
      error_message: experiment.error_message,
      duration_ms: experiment.duration_ms,
    }, null, 2);
    currentExperimentBundle = {
      schema: "stockrium-experiment-reproduction-bundle/v1",
      experiment_id: experiment.id,
      experiment_type: experiment.experiment_type,
      configuration: experiment.configuration || {},
      reproducibility,
      investment_disclaimer: experiment.investment_disclaimer || {
        title: "Không phải khuyến nghị đầu tư",
        message: "Gói này chỉ phục vụ nghiên cứu và thử nghiệm; kết quả chạy lại có thể thay đổi.",
      },
    };
    els.experimentDetailCard.style.display = "block";
    els.experimentDetailCard.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    appendLog(`Lỗi tải chi tiết thử nghiệm: ${error.message}`);
    alert(`Không thể tải chi tiết thử nghiệm: ${error.message}`);
  }
}

async function loadExperimentHistory() {
  if (!apiBaseUrl || !accessToken || !els.experimentHistoryBody) return;

  const params = new URLSearchParams({ limit: "100", offset: "0" });
  if (els.experimentTypeFilter?.value) params.set("experiment_type", els.experimentTypeFilter.value);
  if (els.experimentStatusFilter?.value) params.set("experiment_status", els.experimentStatusFilter.value);
  els.experimentHistoryBody.innerHTML = '<tr><td colspan="9" class="hint">Đang tải lịch sử...</td></tr>';

  try {
    const payload = await requestJson(`${apiBaseUrl}/api/agentic/experiments?${params.toString()}`);
    const items = payload?.data?.items;
    if (!Array.isArray(items)) throw new Error("Dữ liệu lịch sử không hợp lệ.");

    els.experimentHistoryBody.innerHTML = "";
    if (items.length === 0) {
      els.experimentHistoryBody.innerHTML = '<tr><td colspan="9" class="hint">Chưa có thử nghiệm phù hợp.</td></tr>';
      els.experimentDetailCard.style.display = "none";
      return;
    }

    items.forEach((experiment) => {
      const tr = document.createElement("tr");
      const statusInfo = experimentStatusInfo(experiment.status);
      const scope = experiment.symbol || String(experiment.scope || "--").toUpperCase();
      const createdAt = experiment.created_at
        ? new Date(experiment.created_at).toLocaleString("vi-VN")
        : "--";
      tr.innerHTML = `
        <td style="text-align: center;"><input class="experiment-select-checkbox" type="checkbox" data-experiment-id="${escapeHtml(experiment.id)}" aria-label="Chọn ${escapeHtml(experiment.name || "thử nghiệm")}"></td>
        <td>${escapeHtml(createdAt)}</td>
        <td><strong>${escapeHtml(experiment.name || "--")}</strong></td>
        <td>${escapeHtml(experimentTypeLabel(experiment.experiment_type))}</td>
        <td>${escapeHtml(scope)}</td>
        <td>${escapeHtml(experiment.mode || "--")}</td>
        <td><span class="badge ${statusInfo.cls}">${statusInfo.label}</span></td>
        <td style="max-width: 340px; color: var(--muted); font-size: 0.82rem;">${escapeHtml(experimentQuickSummary(experiment))}</td>
        <td style="text-align: center;"><button class="btn btn-ghost btn-view-experiment" type="button" style="padding: 4px 10px; font-size: 0.75rem;">Xem</button></td>
      `;
      tr.querySelector(".experiment-select-checkbox").addEventListener("change", (event) => {
        toggleExperimentSelection(experiment.id, event.target.checked);
      });
      tr.querySelector(".btn-view-experiment").addEventListener("click", () => loadExperimentDetail(experiment.id));
      els.experimentHistoryBody.appendChild(tr);
    });
    updateExperimentSelectionUi();
  } catch (error) {
    els.experimentHistoryBody.innerHTML = `<tr><td colspan="9" class="hint text-red">${escapeHtml(error.message)}</td></tr>`;
    appendLog(`Lỗi tải lịch sử thử nghiệm: ${error.message}`);
  }
}

function exportAnalyzeCsv() {
  if (analyzeSummaryData.length === 0) return;
  let csv = "data:text/csv;charset=utf-8,Symbol,Recommendation,Score,Confidence,Status\n";
  analyzeSummaryData.forEach((row) => {
    const rec = row.rec ? recommendationText(row.rec) : "";
    const score = row.rec ? scoreOutOf100(row.rec.score?.total) : "";
    const conf = row.rec ? confidenceInfo(row.rec.confidence).text : "";
    csv += `${row.symbol},${rec},${score},${conf},${row.status}\n`;
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
els.runBacktestBtn.addEventListener("click", runBacktest);
els.exportVn30CsvBtn.addEventListener("click", exportVn30Csv);
els.resetVn30CheckpointBtn.addEventListener("click", resetVn30Checkpoint);
els.refreshCloudHistoryBtn.addEventListener("click", loadCloudHistory);
els.runAnalyzeBtn.addEventListener("click", runAnalyze);
els.exportAnalyzeCsvBtn.addEventListener("click", exportAnalyzeCsv);
els.refreshExperimentHistoryBtn.addEventListener("click", loadExperimentHistory);
els.experimentTypeFilter.addEventListener("change", loadExperimentHistory);
els.experimentStatusFilter.addEventListener("change", loadExperimentHistory);
els.compareExperimentsBtn.addEventListener("click", compareSelectedExperiments);
els.clearExperimentSelectionBtn.addEventListener("click", clearExperimentSelection);
els.closeExperimentCompareBtn.addEventListener("click", () => {
  els.experimentCompareCard.style.display = "none";
});
els.copyExperimentBundleBtn.addEventListener("click", copyCurrentExperimentBundle);
els.loginForm.addEventListener("submit", loginToLab);
els.logoutBtn.addEventListener("click", logoutFromLab);

window.addEventListener("DOMContentLoaded", async () => {
  appendLog("Stockrium Lab đã khởi tạo.");

  // Tabs Navigation init
  initTabs();

  // Drag and drop JSON uploader init
  initDragDrop();

  // Mode (auto/manual) + data selection toggles init
  initDataSelectionControls();

  // AI analyze tab controls init
  initAnalyzeControls();

  // Disable text symbol input if VN30 option is checked
  els.vn30Option.addEventListener("change", (e) => {
    els.backtestSymbol.disabled = e.target.checked;
    if (e.target.checked) {
      els.backtestSymbol.placeholder = "Danh sách VN30 lấy từ backend";
    } else {
      els.backtestSymbol.placeholder = "Ví dụ: FPT, VNM...";
    }
  });

  clearSession();
});
