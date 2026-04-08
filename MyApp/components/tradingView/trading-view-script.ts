export default function injectedJavaScript() {
  return /*javascript*/ `
// Track initialization state
window.currentSeriesType = "candle";
window.cachedPriceData = null;
window.cachedVolumeData = null;
window.currentTimeframeOption = 3; // Default to UNKNOWN

// Timeframe constants (matching CandleChartOption enum)
const TIMEFRAME = {
  ONE_MINUTE: 1,
  FIVE_MINUTES: 2,
  FIFTEEN_MINUTES: 3,
  THIRTY_MINUTES: 4,
  ONE_HOUR: 5,
  ONE_DAY: 6,
  ONE_WEEK: 7,
  ONE_MONTH: 8,
};

// Chart color constants
const CHART_COLORS = {
  UP: "#34C759",
  DOWN: "#F63842",
  AREA_LINE: "#3395FF",
  AREA_TOP: "rgba(41, 114, 255, 0.25)",
  AREA_BOTTOM: "rgba(41, 114, 255, 0.0001)",
};

// Scale margins configuration
//
// Layout cases (each "slot" is ~20% of chart height):
//   price only            → main: {top:0.05, bottom:0.05}
//   price + volume        → main: {top:0.05, bottom:0.30}, volume: {top:0.75, bottom:0}
//   price + indicator     → main: {top:0.05, bottom:0.30}, indicator: {top:0.75, bottom:0}
//   price + vol + ind     → main: {top:0.05, bottom:0.50}, volume: {top:0.55, bottom:0.25}, indicator: {top:0.80, bottom:0}
//
const SCALE_MARGINS = {
  // price pane
  mainFull:          { top: 0.05, bottom: 0.05 }, // no sub-pane
  mainWithOne:       { top: 0.05, bottom: 0.30 }, // one sub-pane (vol or ind)
  mainWithTwo:       { top: 0.05, bottom: 0.50 }, // both sub-panes
 
  // volume pane
  volumeAlone:       { top: 0.75, bottom: 0.00 }, // only sub-pane
  volumeWithInd:     { top: 0.55, bottom: 0.25 }, // volume above indicator
 
  // indicator pane
  indicatorAlone:    { top: 0.75, bottom: 0.00 }, // only sub-pane
  indicatorWithVol:  { top: 0.80, bottom: 0.00 }, // indicator below volume
 
  // collapsed (hidden but still exists)
  collapsed:         { top: 1.00, bottom: 0.00 },
};

const DEFAULT_ZOOM = {
  barSpacing: 6,
  rightOffset: 1,
};
 
function binarySearchByTime(data, targetTime) {
  let left = 0;
  let right = data.length - 1;
  while (left <= right) {
    const mid = (left + right) >> 1;
    const midTime = data[mid].time;
    if (midTime === targetTime) return mid;
    if (midTime < targetTime) left = mid + 1;
    else right = mid - 1;
  }
  return -1;
}
 
// Shared formatters
const volumeFormatter = (value) => {
  if (value == null || isNaN(value)) return "--";
  const abs = Math.abs(value);
  if (abs >= 1e9) return Math.round(value / 1e9) + " T";
  if (abs >= 1e6) return Math.round(value / 1e6) + " Tr";
  if (abs >= 1e3) return Math.round(value / 1e3) + " N";
  return Math.round(value).toString();
};
const priceFormatter = Intl.NumberFormat("vi-VN", {
  style: "decimal",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format;
 
const indicatorFormatter = (value) => {
  if (value == null || isNaN(value)) return "--";
  return value.toFixed(2);
};
 
// Series configuration factories
const createCandlestickOptions = () => ({
  priceFormat: { type: "custom", formatter: priceFormatter },
  visible: true,
  ticksVisible: false,
  borderVisible: false,
  upColor: CHART_COLORS.UP,
  downColor: CHART_COLORS.DOWN,
});
 
const createAreaOptions = () => ({
  priceFormat: { type: "custom", formatter: priceFormatter },
  lineColor: CHART_COLORS.AREA_LINE,
  topColor: CHART_COLORS.AREA_TOP,
  bottomColor: CHART_COLORS.AREA_BOTTOM,
  lineWidth: 2,
  visible: true,
  priceLineVisible: true,
  lastValueVisible: true,
});
 
// Intl.DateTimeFormat instances (cached for performance)
const dtfTime = new Intl.DateTimeFormat("vi-VN", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});
const dtfYear = new Intl.DateTimeFormat("vi-VN", { year: "numeric" });
const dtfParts = new Intl.DateTimeFormat("vi-VN", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});
 
const getDateParts = (date) => {
  const parts = dtfParts.formatToParts(date);
  const result = {};
  for (const part of parts) result[part.type] = part.value;
  return result;
};
 
const formatDate = (date) => {
  const p = getDateParts(date);
  return p.day + "/" + p.month + "/" + p.year;
};
const formatDayMonth = (date) => {
  const p = getDateParts(date);
  return p.day + "/" + p.month;
};
const formatMonthYear = (date) => {
  const p = getDateParts(date);
  return p.month + "/" + p.year;
};
 
const timeFormatter = (time) => {
  const date = new Date(time * 1000);
  const tf = window.currentTimeframeOption;
  if (
    tf === TIMEFRAME.ONE_MINUTE ||
    tf === TIMEFRAME.FIVE_MINUTES ||
    tf === TIMEFRAME.FIFTEEN_MINUTES ||
    tf === TIMEFRAME.THIRTY_MINUTES ||
    tf === TIMEFRAME.ONE_HOUR
  ) {
    return dtfTime.format(date) + " " + formatDate(date);
  }
  // 1d, 1w, 1month
  return formatDate(date);
};
 
const tickMarkFormatter = (time, tickMarkType) => {
  const date = new Date(time * 1000);
  const tf = window.currentTimeframeOption;
 
  // 1month: chỉ cần hiện tháng/năm hoặc năm
  if (tf === TIMEFRAME.ONE_MONTH) {
    switch (tickMarkType) {
      case 0: return dtfYear.format(date);
      default: return formatMonthYear(date);
    }
  }
 
  // 1w, 1d
  if (tf === TIMEFRAME.ONE_WEEK || tf === TIMEFRAME.ONE_DAY) {
    switch (tickMarkType) {
      case 0: return dtfYear.format(date);
      case 1: return formatMonthYear(date);
      default: return formatDayMonth(date);
    }
  }
 
  // Intraday: 1m, 5m, 15m, 30m, 1h
  switch (tickMarkType) {
    case 0: return dtfYear.format(date);
    case 1: return formatMonthYear(date);
    case 2: return formatDayMonth(date);
    case 3:
    case 4: return dtfTime.format(date);
    default: return formatDate(date);
  }
};
 
const formatDateForTooltip = (timestamp) => {
  const date = new Date(timestamp * 1000);
  const tf = window.currentTimeframeOption;
  if (
    tf === TIMEFRAME.ONE_MINUTE ||
    tf === TIMEFRAME.FIVE_MINUTES ||
    tf === TIMEFRAME.FIFTEEN_MINUTES ||
    tf === TIMEFRAME.THIRTY_MINUTES ||
    tf === TIMEFRAME.ONE_HOUR
  ) {
    return dtfTime.format(date) + ", " + formatDate(date);
  }
  return formatDate(date);
};
 
const formatPriceForTooltip = (price) => {
  if (price === undefined || price === null) return "--";
  return price.toFixed(2).replace(".", ",");
};
 
function setValueWithPrefixAndColor(element, value, prevValue, suffix = "") {
  if (!element) return;
  if (prevValue !== null) {
    let prefix = "";
    let color = "#333333";
    if (value > 0) { prefix = "+"; color = "#34C759"; }
    else if (value < 0) { prefix = "-"; color = "#F63842"; }
    element.textContent = prefix + formatPriceForTooltip(Math.abs(value)) + suffix;
    element.style.color = value === 0 ? "#333333" : color;
  } else {
    element.textContent = "--";
    element.style.color = "#333333";
  }
}
 
// Fixed grid primitive (Binance-style)
const createFixedGridPrimitive = () => {
  const GRID_COLOR = "rgba(0, 0, 0, 0.1)";
  const H_SPACING = 39;
  const V_SPACING = 80;
 
  const renderer = {
    draw(target) {
      target.useBitmapCoordinateSpace((scope) => {
        const ctx = scope.context;
        const { width, height } = scope.bitmapSize;
        const hR = scope.horizontalPixelRatio;
        const vR = scope.verticalPixelRatio;
 
        ctx.save();
        ctx.strokeStyle = GRID_COLOR;
        ctx.lineWidth = 1;
 
        const hStep = H_SPACING * vR;
        for (let y = hStep; y < height; y += hStep) {
          ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
        }
 
        const vStep = V_SPACING * hR;
        for (let x = vStep; x < width; x += vStep) {
          ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
        }
 
        ctx.restore();
      });
    },
  };
 
  const view = { renderer() { return renderer; }, zOrder() { return "bottom"; } };
 
  return {
    attached() {}, detached() {}, updateAllViews() {},
    paneViews() { return [view]; },
  };
};
 
// High/Low price labels primitive (Binance-style)
const drawPriceLabel = (ctx, x, y, text, hRatio, vRatio, bitmapWidth) => {
  ctx.save();
  const fontSize = Math.round(10 * vRatio);
  ctx.font = fontSize + "px -apple-system, sans-serif";
  ctx.textBaseline = "middle";
  const textWidth = ctx.measureText(text).width;
  const lineLen = 20 * hRatio;
  const gap = 4 * hRatio;
  const bx = Math.round(x * hRatio);
  const by = Math.round(y * vRatio);
  const goRight = bx < bitmapWidth * 0.5;
  const dir = goRight ? 1 : -1;
  const lineEndX = bx + dir * lineLen;
  const textX = goRight ? lineEndX + gap : lineEndX - gap - textWidth;
  ctx.strokeStyle = "#333333";
  ctx.lineWidth = Math.max(1, Math.round(hRatio)) * 0.5;
  ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(lineEndX, by); ctx.stroke();
  ctx.fillStyle = "#333333";
  ctx.fillText(text, textX, by);
  ctx.restore();
};
 
const createHighLowPrimitive = () => {
  let _chart = null, _series = null, _data = null, _requestUpdate = null;
 
  const renderer = {
    draw(target) {
      if (!_data) return;
      target.useBitmapCoordinateSpace((scope) => {
        const ctx = scope.context;
        const hR = scope.horizontalPixelRatio;
        const vR = scope.verticalPixelRatio;
        const bw = scope.bitmapSize.width;
        if (_data.high) drawPriceLabel(ctx, _data.high.x, _data.high.y, _data.high.text, hR, vR, bw);
        if (_data.low) drawPriceLabel(ctx, _data.low.x, _data.low.y, _data.low.text, hR, vR, bw);
      });
    },
  };
 
  const view = { renderer() { return renderer; }, zOrder() { return "top"; } };
 
  return {
    attached(params) {
      _chart = params.chart; _series = params.series; _requestUpdate = params.requestUpdate;
    },
    detached() { _chart = null; _series = null; _data = null; _requestUpdate = null; },
    updateAllViews() {
      _data = null;
      if (!_chart || !_series || !window.cachedPriceData || window.currentSeriesType !== "candle") return;
      const logicalRange = _chart.timeScale().getVisibleLogicalRange();
      if (!logicalRange) return;
      const cachedData = window.cachedPriceData;
      const len = cachedData.length;
      const from = Math.max(0, Math.ceil(logicalRange.from));
      const to = Math.min(len - 1, Math.floor(logicalRange.to));
      if (from > to || from >= len) return;
      let hi = from, lo = from;
      for (let i = from + 1; i <= to; i++) {
        if (cachedData[i].high > cachedData[hi].high) hi = i;
        if (cachedData[i].low < cachedData[lo].low) lo = i;
      }
      const hCandle = cachedData[hi], lCandle = cachedData[lo];
      const hx = _chart.timeScale().timeToCoordinate(hCandle.time);
      const hy = _series.priceToCoordinate(hCandle.high);
      const lx = _chart.timeScale().timeToCoordinate(lCandle.time);
      const ly = _series.priceToCoordinate(lCandle.low);
      if (hx === null || hy === null || lx === null || ly === null) return;
      _data = {
        high: { x: hx, y: hy, text: priceFormatter(hCandle.high) },
        low: { x: lx, y: ly, text: priceFormatter(lCandle.low) },
      };
    },
    paneViews() { return [view]; },
    requestRedraw() { if (_requestUpdate) _requestUpdate(); },
  };
};
 
// ─── Helper: recompute and apply all scale margins based on current state ───
const applyScaleMargins = () => {
  if (!window.chart) return;
  const volOn = window.isVolumeVisible;
  const indOn = window.currentIndicatorMode2 !== null;
 
  // Price pane
  let mainMargins;
  if (volOn && indOn)       mainMargins = SCALE_MARGINS.mainWithTwo;
  else if (volOn || indOn)  mainMargins = SCALE_MARGINS.mainWithOne;
  else                      mainMargins = SCALE_MARGINS.mainFull;
  window.chart.priceScale("right").applyOptions({ scaleMargins: mainMargins });
 
  // Volume pane
  if (window.volumeSeries) {
    if (volOn) {
      const volMargins = indOn ? SCALE_MARGINS.volumeWithInd : SCALE_MARGINS.volumeAlone;
      window.chart.priceScale("volume").applyOptions({ scaleMargins: volMargins });
    } else {
      window.chart.priceScale("volume").applyOptions({ scaleMargins: SCALE_MARGINS.collapsed });
    }
  }
 
  // Indicator pane
  if (window.rsiSeries) {
    if (indOn) {
      const indMargins = volOn ? SCALE_MARGINS.indicatorWithVol : SCALE_MARGINS.indicatorAlone;
      window.chart.priceScale("indicator").applyOptions({ scaleMargins: indMargins });
    } else {
      window.chart.priceScale("indicator").applyOptions({ scaleMargins: SCALE_MARGINS.collapsed });
    }
  }
};
 
const tryInitialize = () => {
  const container = document.getElementById("container");
  if (!container || typeof LightweightCharts === "undefined") return;
 
  const rect = container.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) {
    requestAnimationFrame(tryInitialize);
    return;
  }
 
  try {
    window.chart = LightweightCharts.createChart(container, {
      localization: { timeFormatter },
      layout: { fontSize: 10 },
      grid: { vertLines: { visible: false }, horzLines: { visible: false } },
      handleScroll: { vertTouchDrag: true, horzTouchDrag: true },
      rightPriceScale: { borderVisible: false, autoScale: true },
      timeScale: {
        barSpacing: DEFAULT_ZOOM.barSpacing,
        rightOffset: DEFAULT_ZOOM.rightOffset,
        borderVisible: false,
        autoScale: true,
        enableConflation: true,
        timeVisible: true,
        tickMarkFormatter,
      },
      crosshair: {
        vertLine: { labelBackgroundColor: "#007AFF" },
        horzLine: { labelBackgroundColor: "#007AFF" },
      },
    });
 
    // ── Volume series ──────────────────────────────────────────────────────
    window.volumeSeries = window.chart.addSeries(LightweightCharts.HistogramSeries, {
      priceFormat: { type: "custom", formatter: volumeFormatter },
      priceScaleId: "volume",
      priceLineVisible: false,
      lastValueVisible: true,
    });
    window.chart.priceScale("volume").applyOptions({ scaleMargins: SCALE_MARGINS.volumeAlone });
 
    // ── Main price series ──────────────────────────────────────────────────
    window.mainSeries = window.chart.addSeries(LightweightCharts.CandlestickSeries, createCandlestickOptions());
    window.chart.priceScale("right").applyOptions({ scaleMargins: SCALE_MARGINS.mainWithOne });
 
    // ── MA lines ───────────────────────────────────────────────────────────
    window.ma20Series = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#D4A017",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
      priceScaleId: "right",
    });
 
    window.ma50Series = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#1B7A1B",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
      priceScaleId: "right",
    });
 
    // ── BOLL lines ─────────────────────────────────────────────────────────
    window.bollSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#D4A017",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
      priceScaleId: "right",
    });
 
    window.ubSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#1B7A1B",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
      priceScaleId: "right",
    });
 
    window.lbSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#613DE4",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
      priceScaleId: "right",
    });
 
    // ── Indicator pane: RSI (single line) ─────────────────────────────────
    window.rsiSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#FF9F0A",
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      priceScaleId: "indicator",
      priceFormat: { type: "custom", formatter: indicatorFormatter },
    });
 
    // ── Indicator pane: KDJ (K, D, J) ─────────────────────────────────────
    window.kdjKSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#FF9F0A",   // K – orange
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      priceScaleId: "indicator",
      priceFormat: { type: "custom", formatter: indicatorFormatter },
    });
 
    window.kdjDSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#3395FF",   // D – blue
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      priceScaleId: "indicator",
      priceFormat: { type: "custom", formatter: indicatorFormatter },
    });
 
    window.kdjJSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
      visible: false,
      color: "#FF3B30",   // J – red
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      priceScaleId: "indicator",
      priceFormat: { type: "custom", formatter: indicatorFormatter },
    });
 
    // Collapse indicator pane by default (mode2 = null)
    window.chart.priceScale("indicator").applyOptions({ scaleMargins: SCALE_MARGINS.collapsed });
 
    // ── Primitives ─────────────────────────────────────────────────────────
    window.fixedGridPrimitive = createFixedGridPrimitive();
    window.mainSeries.attachPrimitive(window.fixedGridPrimitive);
 
    window.highLowPrimitive = createHighLowPrimitive();
    window.mainSeries.attachPrimitive(window.highLowPrimitive);
 
    // ── Tooltip ────────────────────────────────────────────────────────────
    const tooltip = document.createElement("div");
    tooltip.className = "tooltip";
    tooltip.innerHTML = ${tooltipHTMLTemplateString};
    container.appendChild(tooltip);
    window.tooltip = tooltip;
 
    window.chart.subscribeCrosshairMove((param) => {
      if (
        !param.point || !param.time ||
        param.point.x < 0 || param.point.x > container.clientWidth ||
        param.point.y < 0 || param.point.y > container.clientHeight
      ) {
        tooltip.style.display = "none";
        return;
      }
 
      const candleData = param.seriesData.get(window.mainSeries);
      if (!candleData) { tooltip.style.display = "none"; return; }
 
      const volumeData = param.seriesData.get(window.volumeSeries);
 
      const dateText = tooltip.querySelector(".tooltip-date-text");
      if (dateText) dateText.textContent = formatDateForTooltip(param.time);
 
      const index = binarySearchByTime(window.cachedPriceData, param.time);
      const prevClosePrice = index > 0 ? window.cachedPriceData[index - 1].close : null;
 
      const openEl = document.getElementById("tooltip-open");
      const closeEl = document.getElementById("tooltip-close");
      const highEl = document.getElementById("tooltip-high");
      const lowEl = document.getElementById("tooltip-low");
      const volumeEl = document.getElementById("tooltip-volume");
      const changeEl = document.getElementById("tooltip-change");
      const percentageChangeEl = document.getElementById("tooltip-percentage-change");
      const amplitudeEl = document.getElementById("tooltip-amplitude");
 
      const ohlcData = window.currentSeriesType === "candle"
        ? candleData
        : index >= 0 ? window.cachedPriceData[index] : null;
 
      if (ohlcData && prevClosePrice) {
        const changeValue = ohlcData.close - prevClosePrice;
        const percentageChangeValue = (changeValue / prevClosePrice) * 100;
        const amplitudeValue = ((ohlcData.high - ohlcData.low) / prevClosePrice) * 100;
        if (openEl) openEl.textContent = formatPriceForTooltip(ohlcData.open);
        if (closeEl) closeEl.textContent = formatPriceForTooltip(ohlcData.close);
        if (highEl) highEl.textContent = formatPriceForTooltip(ohlcData.high);
        if (lowEl) lowEl.textContent = formatPriceForTooltip(ohlcData.low);
        if (amplitudeEl) amplitudeEl.textContent = formatPriceForTooltip(amplitudeValue) + "%";
        setValueWithPrefixAndColor(changeEl, changeValue, prevClosePrice);
        setValueWithPrefixAndColor(percentageChangeEl, percentageChangeValue, prevClosePrice, "%");
      } else {
        const fallbackValue = candleData.value !== undefined ? candleData.value : candleData.close;
        if (openEl) openEl.textContent = "--";
        if (closeEl) closeEl.textContent = formatPriceForTooltip(fallbackValue);
        if (highEl) highEl.textContent = "--";
        if (lowEl) lowEl.textContent = "--";
        if (changeEl) changeEl.textContent = "--";
        if (amplitudeEl) amplitudeEl.textContent = "--";
        if (percentageChangeEl) percentageChangeEl.textContent = "--";
      }
 
      if (volumeEl && volumeData) {
        volumeEl.textContent = volumeFormatter(volumeData.value !== undefined ? volumeData.value : volumeData);
      } else if (volumeEl) {
        volumeEl.textContent = "--";
      }
 
      // Position tooltip opposite to crosshair side
      const tooltipWidth = tooltip.offsetWidth || 130;
      const priceScaleWidth = 55;
      const chartMidPoint = (container.clientWidth - priceScaleWidth) / 2;
      const left = param.point.x > chartMidPoint
        ? 8
        : container.clientWidth - tooltipWidth - 8 - priceScaleWidth;
      tooltip.style.left = left + "px";
      tooltip.style.top = "2px";
      tooltip.style.display = "block";
    });
 
    window.addEventListener("resize", () => {
      if (window.chart && window.innerWidth > 0 && window.innerHeight > 0) {
        window.chart.resize(window.innerWidth, window.innerHeight);
      }
    });
 
    if (window.ReactNativeWebView) {
      window.ReactNativeWebView.postMessage(JSON.stringify({ type: "chart-ready" }));
    }
  } catch (error) {
    if (window.ReactNativeWebView) {
      window.ReactNativeWebView.postMessage(JSON.stringify({
        type: "initialization-error",
        message: error.message || "Chart initialization failed",
      }));
    }
  }
};
 
// Switch between candlestick and area series
window.switchSeriesType = (newType) => {
  if (newType === window.currentSeriesType) return;
 
  window.chart.removeSeries(window.mainSeries);
 
  if (newType === "area") {
    window.mainSeries = window.chart.addSeries(LightweightCharts.AreaSeries, createAreaOptions());
    if (window.cachedPriceData) {
      window.mainSeries.setData(window.cachedPriceData.map((item) => ({ time: item.time, value: item.close })));
    }
  } else {
    window.mainSeries = window.chart.addSeries(LightweightCharts.CandlestickSeries, createCandlestickOptions());
    if (window.cachedPriceData) window.mainSeries.setData(window.cachedPriceData);
  }
 
  window.currentSeriesType = newType;
 
  if (window.fixedGridPrimitive) window.mainSeries.attachPrimitive(window.fixedGridPrimitive);
 
  if (newType === "candle" && window.highLowPrimitive) {
    window.mainSeries.attachPrimitive(window.highLowPrimitive);
    requestAnimationFrame(() => { if (window.highLowPrimitive) window.highLowPrimitive.requestRedraw(); });
  }
 
  if (window.ma20Series) window.ma20Series.applyOptions({ priceScaleId: "right" });
  if (window.ma50Series) window.ma50Series.applyOptions({ priceScaleId: "right" });
  if (window.bollSeries) window.bollSeries.applyOptions({ priceScaleId: "right" });
  if (window.ubSeries) window.ubSeries.applyOptions({ priceScaleId: "right" });
  if (window.lbSeries) window.lbSeries.applyOptions({ priceScaleId: "right" });
};
 
window.setVolumeVisible = (visible) => {
  if (!window.volumeSeries || !window.chart) return;
  window.isVolumeVisible = visible;
  window.volumeSeries.applyOptions({ visible });
  applyScaleMargins();
};
 
window.setTechnicalIndicatorMode1 = (mode) => {
  if (!window.ma20Series || !window.ma50Series) return;
  if (!window.bollSeries || !window.ubSeries || !window.lbSeries) return;
 
  if (mode === "MA") {
    window.ma20Series.applyOptions({ visible: true });
    window.ma50Series.applyOptions({ visible: true });
    window.bollSeries.applyOptions({ visible: false });
    window.ubSeries.applyOptions({ visible: false });
    window.lbSeries.applyOptions({ visible: false });
  } else if (mode === "BOLL") {
    window.ma20Series.applyOptions({ visible: false });
    window.ma50Series.applyOptions({ visible: false });
    window.bollSeries.applyOptions({ visible: true });
    window.ubSeries.applyOptions({ visible: true });
    window.lbSeries.applyOptions({ visible: true });
  } else {
    // NONE
    window.ma20Series.applyOptions({ visible: false });
    window.ma50Series.applyOptions({ visible: false });
    window.bollSeries.applyOptions({ visible: false });
    window.ubSeries.applyOptions({ visible: false });
    window.lbSeries.applyOptions({ visible: false });
  }
};
 
// ── technicalIndicatorMode2: "RSI" | "KDJ" | null ─────────────────────────
window.setTechnicalIndicatorMode2 = (mode) => {
  if (!window.rsiSeries || !window.kdjKSeries) return;
 
  window.currentIndicatorMode2 = mode;
 
  if (mode === "RSI") {
    window.rsiSeries.applyOptions({ visible: true });
    window.kdjKSeries.applyOptions({ visible: false });
    window.kdjDSeries.applyOptions({ visible: false });
    window.kdjJSeries.applyOptions({ visible: false });
  } else if (mode === "KDJ") {
    window.rsiSeries.applyOptions({ visible: false });
    window.kdjKSeries.applyOptions({ visible: true });
    window.kdjDSeries.applyOptions({ visible: true });
    window.kdjJSeries.applyOptions({ visible: true });
  } else {
    // null – hide all indicator lines
    window.rsiSeries.applyOptions({ visible: false });
    window.kdjKSeries.applyOptions({ visible: false });
    window.kdjDSeries.applyOptions({ visible: false });
    window.kdjJSeries.applyOptions({ visible: false });
  }
 
  applyScaleMargins();
};
 
// Set chart data (called once or when timeframe changes)
window.updateChartData = (priceData, volumeData, maData, bollData, rsiData, kdjData, timeframeOption) => {
  if (!priceData || !volumeData) return;
 
  const isTimeframeChanged = timeframeOption !== undefined && timeframeOption !== window.currentTimeframeOption;
  if (timeframeOption !== undefined) window.currentTimeframeOption = timeframeOption;
 
  window.cachedPriceData = priceData;
  window.cachedVolumeData = volumeData;
 
  if (window.currentSeriesType === "area") {
    window.mainSeries.setData(priceData.map((item) => ({ time: item.time, value: item.close })));
  } else {
    window.mainSeries.setData(priceData);
  }
  window.volumeSeries.setData(volumeData);
 
  if (isTimeframeChanged) {
    requestAnimationFrame(() => {
      if (window.chart) {
        window.chart.timeScale().applyOptions(DEFAULT_ZOOM);
        window.chart.timeScale().scrollToPosition(DEFAULT_ZOOM.rightOffset, false);
      }
    });
  }
 
  if (maData && window.ma20Series) window.ma20Series.setData(maData.map((item) => ({ time: item.time, value: item.ma20 })));
  if (maData && window.ma50Series) window.ma50Series.setData(maData.map((item) => ({ time: item.time, value: item.ma50 })));
  if (bollData && window.bollSeries) window.bollSeries.setData(bollData.map((item) => ({ time: item.time, value: item.boll })));
  if (bollData && window.ubSeries) window.ubSeries.setData(bollData.map((item) => ({ time: item.time, value: item.ub })));
  if (bollData && window.lbSeries) window.lbSeries.setData(bollData.map((item) => ({ time: item.time, value: item.lb })));
 
  // RSI: [{ time, value }]
  if (rsiData && window.rsiSeries) {
    window.rsiSeries.setData(rsiData.map((item) => ({ time: item.time, value: item.value })));
  }
 
  // KDJ: [{ time, k, d, j }]
  if (kdjData) {
    if (window.kdjKSeries) window.kdjKSeries.setData(kdjData.map((item) => ({ time: item.time, value: item.k })));
    if (window.kdjDSeries) window.kdjDSeries.setData(kdjData.map((item) => ({ time: item.time, value: item.d })));
    if (window.kdjJSeries) window.kdjJSeries.setData(kdjData.map((item) => ({ time: item.time, value: item.j })));
  }
};
 
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", tryInitialize);
} else {
  tryInitialize();
}
true;
`;
}

const tooltipHTML = /*html*/ `
    <div class="tooltip-date">
        <div class="tooltip-indicator"></div>
        <div class="tooltip-date-text"></div>
    </div>
    <div class="tooltip-price-row">
        <span class="tooltip-price-label">Giá mở:</span>
        <span class="tooltip-price-value" id="tooltip-open">--</span>
    </div>
    <div class="tooltip-price-row">
        <span class="tooltip-price-label">Giá đóng:</span>
        <span class="tooltip-price-value" id="tooltip-close">--</span>
    </div>
    <div class="tooltip-price-row">
        <span class="tooltip-price-label">Thay đổi:</span>
        <span class="tooltip-price-value" id="tooltip-change">--</span>
    </div>
    <div class="tooltip-price-row">
        <span class="tooltip-price-label">% thay đổi:</span>
        <span class="tooltip-price-value" id="tooltip-percentage-change">--</span>
    </div>
    <div class="tooltip-price-row">
        <span class="tooltip-price-label">Giá cao nhất:</span>
        <span class="tooltip-price-value" id="tooltip-high">--</span>
    </div>
    <div class="tooltip-price-row">
        <span class="tooltip-price-label">Giá thấp nhất:</span>
        <span class="tooltip-price-value" id="tooltip-low">--</span>
    </div>
    <div class="tooltip-volume-row">
        <span class="tooltip-volume-label">Biên độ:</span>
        <span class="tooltip-volume-value" id="tooltip-amplitude">--</span>
    </div>
    <div class="tooltip-volume-row">
        <span class="tooltip-volume-label">Khối lượng GD:</span>
        <span class="tooltip-volume-value" id="tooltip-volume">--</span>
    </div>
`;

const tooltipHTMLTemplateString = `\`${tooltipHTML}\``;
