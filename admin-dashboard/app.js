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
};

let symbolsLoaded = false;

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

  // Keep log compact for long admin sessions.
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

  // Supports either ["VNM", "FPT"] or [{symbol:"VNM"}, ...].
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
      Accept: "application/json",
      ...(options.headers || {}),
    },
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

els.loadSymbolsBtn.addEventListener("click", loadSymbols);
els.updatePriceBtn.addEventListener("click", updatePrice);
els.updateNewsBtn.addEventListener("click", updateNews);
els.clearLogBtn.addEventListener("click", clearLog);

window.addEventListener("DOMContentLoaded", () => {
  appendLog("Dashboard đã khởi tạo.");

  // Auto-load symbols once to reduce manual actions for admin.
  if (!symbolsLoaded) {
    loadSymbols();
  }
});
