export default function injectedJavaScript() {
  return /*javascript*/ `

window.themeColors = {
  background: "#ffffff",
  textPrimary: "#333333",
};

window.setTheme = (background, textPrimary) => {
  window.themeColors = { background, textPrimary };

  document.body.style.backgroundColor = background;
  document.documentElement.style.backgroundColor = background;

  if (!window.chart) return;
  window.chart.applyOptions({
    layout: {
      background: { color: background },
      textColor: textPrimary,
    },
  });
};

// Track initialization state
window.currentSeriesType = "candle";
window.cachedPriceData = null;
window.cachedVolumeData = null;
window.cachedVolumeMAData = null;
window.cachedMaData = null;
window.cachedBollData = null;
window.cachedMacdData = null;
window.cachedRsiData = null;
window.cachedKdjData = null;
window.currentTimeframeOption = 3; // Default to UNKNOWN
window.isVolumeVisible = false;
window.currentIndicatorMode2 = null;

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
  return formatDate(date);
};

const tickMarkFormatter = (time, tickMarkType) => {
  const date = new Date(time * 1000);
  const tf = window.currentTimeframeOption;

  if (tf === TIMEFRAME.ONE_MONTH) {
    switch (tickMarkType) {
      case 0: return dtfYear.format(date);
      default: return formatMonthYear(date);
    }
  }

  if (tf === TIMEFRAME.ONE_WEEK || tf === TIMEFRAME.ONE_DAY) {
    switch (tickMarkType) {
      case 0: return dtfYear.format(date);
      case 1: return formatMonthYear(date);
      default: return formatDayMonth(date);
    }
  }

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

  const labelColor = window.themeColors?.textPrimary ?? "#333333";

  ctx.strokeStyle = labelColor;
  ctx.lineWidth = Math.max(1, Math.round(hRatio)) * 0.5;
  ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(lineEndX, by); ctx.stroke();
  ctx.fillStyle = labelColor;
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

// ─── Helper: remove all volume series and reset refs ────────────────────────
const destroyVolumeSeries = () => {
  if (window.vma50Series) { window.chart.removeSeries(window.vma50Series); window.vma50Series = null; }
  if (window.vma20Series) { window.chart.removeSeries(window.vma20Series); window.vma20Series = null; }
  if (window.volumeSeries) { window.chart.removeSeries(window.volumeSeries); window.volumeSeries = null; }
};

// ─── Helper: remove all indicator series and reset refs ─────────────────────
const destroyIndicatorSeries = () => {
  if (window.kdjJSeries) { window.chart.removeSeries(window.kdjJSeries); window.kdjJSeries = null; }
  if (window.kdjDSeries) { window.chart.removeSeries(window.kdjDSeries); window.kdjDSeries = null; }
  if (window.kdjKSeries) { window.chart.removeSeries(window.kdjKSeries); window.kdjKSeries = null; }
  if (window.rsiSeries) { window.chart.removeSeries(window.rsiSeries); window.rsiSeries = null; }
  if (window.macdDeaSeries) { window.chart.removeSeries(window.macdDeaSeries); window.macdDeaSeries = null; }
  if (window.macdDifSeries) { window.chart.removeSeries(window.macdDifSeries); window.macdDifSeries = null; }
  if (window.macdHistogramSeries) { window.chart.removeSeries(window.macdHistogramSeries); window.macdHistogramSeries = null; }
};

// ─── Lazy init: Volume pane (pane động) ─────────────────────────────────────
const ensureVolumePaneCreated = () => {
  if (window.volumeSeries) return; // already created

  // Pane index = number of existing panes (0-based: pane 0 always exists)
  const volumePaneIndex = window.chart.panes().length;

  window.volumeSeries = window.chart.addSeries(LightweightCharts.HistogramSeries, {
    priceFormat: { type: "custom", formatter: volumeFormatter },
    priceScaleId: "right",
    priceLineVisible: false,
    lastValueVisible: true,
  }, volumePaneIndex);

  window.vma20Series = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#D4A017",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: false,
    priceScaleId: "right",
  }, volumePaneIndex);

  window.vma50Series = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#1B7A1B",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: false,
    priceScaleId: "right",
  }, volumePaneIndex);

  // Set cached data immediately
  if (window.cachedVolumeData) window.volumeSeries.setData(window.cachedVolumeData);
  if (window.cachedVolumeMAData) {
    window.vma20Series.setData(
      window.cachedVolumeMAData.filter(i => i.vma20 !== null).map(i => ({ time: i.time, value: i.vma20 }))
    );
    window.vma50Series.setData(
      window.cachedVolumeMAData.filter(i => i.vma50 !== null).map(i => ({ time: i.time, value: i.vma50 }))
    );
  }
};

// ─── Lazy init: Indicator pane (pane động) ──────────────────────────────────
const ensureIndicatorPaneCreated = () => {
  if (window.rsiSeries) return; // already created

  // Pane index = number of existing panes (0-based: pane 0 always exists)
  // If volume pane exists → indicator goes to pane 2, else pane 1
  const indicatorPaneIndex = window.chart.panes().length;

  window.macdHistogramSeries = window.chart.addSeries(LightweightCharts.HistogramSeries, {
    priceScaleId: "right",
    priceLineVisible: false,
    lastValueVisible: false,
    priceFormat: { type: "custom", formatter: indicatorFormatter },
  }, indicatorPaneIndex);

  window.macdDifSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#D4A017",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: true,
    crosshairMarkerVisible: true,
    priceScaleId: "right",
    priceFormat: { type: "custom", formatter: indicatorFormatter },
  }, indicatorPaneIndex);

  window.macdDeaSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#1B7A1B",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: true,
    crosshairMarkerVisible: true,
    priceScaleId: "right",
    priceFormat: { type: "custom", formatter: indicatorFormatter },
  }, indicatorPaneIndex);

  window.rsiSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#FF9F0A",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: true,
    crosshairMarkerVisible: true,
    priceScaleId: "right",
    priceFormat: { type: "custom", formatter: indicatorFormatter },
  }, indicatorPaneIndex);

  window.kdjKSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#FF9F0A",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: true,
    crosshairMarkerVisible: true,
    priceScaleId: "right",
    priceFormat: { type: "custom", formatter: indicatorFormatter },
  }, indicatorPaneIndex);

  window.kdjDSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#3395FF",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: true,
    crosshairMarkerVisible: true,
    priceScaleId: "right",
    priceFormat: { type: "custom", formatter: indicatorFormatter },
  }, indicatorPaneIndex);

  window.kdjJSeries = window.chart.addSeries(LightweightCharts.LineSeries, {
    color: "#FF3B30",
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: true,
    crosshairMarkerVisible: true,
    priceScaleId: "right",
    priceFormat: { type: "custom", formatter: indicatorFormatter },
  }, indicatorPaneIndex);

  // Set cached data immediately
  if (window.cachedRsiData) {
    window.rsiSeries.setData(window.cachedRsiData.map(i => ({ time: i.time, value: i.value })));
  }
  if (window.cachedKdjData) {
    window.kdjKSeries.setData(window.cachedKdjData.map(i => ({ time: i.time, value: i.k })));
    window.kdjDSeries.setData(window.cachedKdjData.map(i => ({ time: i.time, value: i.d })));
    window.kdjJSeries.setData(window.cachedKdjData.map(i => ({ time: i.time, value: i.j })));
  }
  if (window.cachedMacdData) {
    window.macdHistogramSeries.setData(window.cachedMacdData.map(i => ({
      time: i.time,
      value: i.macd,
      color: i.macd >= 0 ? "#34C759" : "#F63842",
    })));
    window.macdDifSeries.setData(window.cachedMacdData.map(i => ({ time: i.time, value: i.dif })));
    window.macdDeaSeries.setData(window.cachedMacdData.map(i => ({ time: i.time, value: i.dea })));
  }

  // Hide all by default — caller will show the right one
  window.macdHistogramSeries.applyOptions({ visible: false });
  window.macdDifSeries.applyOptions({ visible: false });
  window.macdDeaSeries.applyOptions({ visible: false });
  window.rsiSeries.applyOptions({ visible: false });
  window.kdjKSeries.applyOptions({ visible: false });
  window.kdjDSeries.applyOptions({ visible: false });
  window.kdjJSeries.applyOptions({ visible: false });
};

const tryInitialize = () => {
  document.body.style.backgroundColor = window.themeColors.background;
  document.documentElement.style.backgroundColor = window.themeColors.background;

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
      layout: {
        fontSize: 10,
        background: { color: window.themeColors.background },
        textColor: window.themeColors.textPrimary,
      },
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

    // ── Main price series — pane 0 ─────────────────────────────────────────
    window.mainSeries = window.chart.addSeries(LightweightCharts.CandlestickSeries, createCandlestickOptions());

    // ── MA lines — pane 0 ─────────────────────────────────────────────────
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

    // ── BOLL lines — pane 0 ───────────────────────────────────────────────
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

      const volumeData = window.volumeSeries ? param.seriesData.get(window.volumeSeries) : null;

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
  if (!window.chart) return;
  window.isVolumeVisible = visible;

  if (visible) {
    if (window.currentIndicatorMode2 !== null && window.rsiSeries) {
      // Indicator pane exists — must destroy it first so volume can take the next pane slot,
      // then recreate indicator after volume so order is: price → volume → indicator
      destroyIndicatorSeries();
      ensureVolumePaneCreated();
      ensureIndicatorPaneCreated();
      // Re-apply the active indicator mode visibility
      window.setTechnicalIndicatorMode2(window.currentIndicatorMode2);
    } else {
      ensureVolumePaneCreated();
    }
    if (window.volumeSeries) window.volumeSeries.applyOptions({ visible: true });
    if (window.vma20Series) window.vma20Series.applyOptions({ visible: true });
    if (window.vma50Series) window.vma50Series.applyOptions({ visible: true });
  } else {
    destroyVolumeSeries();
  }
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
    window.ma20Series.applyOptions({ visible: false });
    window.ma50Series.applyOptions({ visible: false });
    window.bollSeries.applyOptions({ visible: false });
    window.ubSeries.applyOptions({ visible: false });
    window.lbSeries.applyOptions({ visible: false });
  }
};

// ── technicalIndicatorMode2: "MACD" | "RSI" | "KDJ" | null ───────────────────
window.setTechnicalIndicatorMode2 = (mode) => {
  if (!window.chart) return;

  window.currentIndicatorMode2 = mode;

  if (mode === null) {
    // Destroy indicator series → Lightweight Charts auto-removes empty pane
    destroyIndicatorSeries();
    return;
  }

  // Lazy create indicator pane on first use
  ensureIndicatorPaneCreated();

  if (mode === "MACD") {
    window.macdHistogramSeries.applyOptions({ visible: true });
    window.macdDifSeries.applyOptions({ visible: true });
    window.macdDeaSeries.applyOptions({ visible: true });
    window.rsiSeries.applyOptions({ visible: false });
    window.kdjKSeries.applyOptions({ visible: false });
    window.kdjDSeries.applyOptions({ visible: false });
    window.kdjJSeries.applyOptions({ visible: false });
  } else if (mode === "RSI") {
    window.macdHistogramSeries.applyOptions({ visible: false });
    window.macdDifSeries.applyOptions({ visible: false });
    window.macdDeaSeries.applyOptions({ visible: false });
    window.rsiSeries.applyOptions({ visible: true });
    window.kdjKSeries.applyOptions({ visible: false });
    window.kdjDSeries.applyOptions({ visible: false });
    window.kdjJSeries.applyOptions({ visible: false });
  } else if (mode === "KDJ") {
    window.macdHistogramSeries.applyOptions({ visible: false });
    window.macdDifSeries.applyOptions({ visible: false });
    window.macdDeaSeries.applyOptions({ visible: false });
    window.rsiSeries.applyOptions({ visible: false });
    window.kdjKSeries.applyOptions({ visible: true });
    window.kdjDSeries.applyOptions({ visible: true });
    window.kdjJSeries.applyOptions({ visible: true });
  }
};

// Set chart data (called once or when timeframe changes)
window.updateChartData = (priceData, volumeData, volumeMAData, maData, bollData, macdData, rsiData, kdjData, timeframeOption) => {
  if (!priceData || !volumeData) return;

  const isTimeframeChanged = timeframeOption !== undefined && timeframeOption !== window.currentTimeframeOption;
  if (timeframeOption !== undefined) window.currentTimeframeOption = timeframeOption;

  // Cache everything
  window.cachedPriceData = priceData;
  window.cachedVolumeData = volumeData;
  window.cachedVolumeMAData = volumeMAData;
  window.cachedMaData = maData;
  window.cachedBollData = bollData;
  window.cachedMacdData = macdData;
  window.cachedRsiData = rsiData;
  window.cachedKdjData = kdjData;

  // Price
  if (window.currentSeriesType === "area") {
    window.mainSeries.setData(priceData.map((item) => ({ time: item.time, value: item.close })));
  } else {
    window.mainSeries.setData(priceData);
  }

  // Volume — only if pane already created
  if (window.volumeSeries) {
    window.volumeSeries.setData(volumeData);
    if (volumeMAData && window.vma20Series) {
      window.vma20Series.setData(
        volumeMAData.filter(i => i.vma20 !== null).map(i => ({ time: i.time, value: i.vma20 }))
      );
    }
    if (volumeMAData && window.vma50Series) {
      window.vma50Series.setData(
        volumeMAData.filter(i => i.vma50 !== null).map(i => ({ time: i.time, value: i.vma50 }))
      );
    }
  }

  // MA / BOLL
  if (maData && window.ma20Series) window.ma20Series.setData(maData.map(i => ({ time: i.time, value: i.ma20 })));
  if (maData && window.ma50Series) window.ma50Series.setData(maData.map(i => ({ time: i.time, value: i.ma50 })));
  if (bollData && window.bollSeries) window.bollSeries.setData(bollData.map(i => ({ time: i.time, value: i.boll })));
  if (bollData && window.ubSeries) window.ubSeries.setData(bollData.map(i => ({ time: i.time, value: i.ub })));
  if (bollData && window.lbSeries) window.lbSeries.setData(bollData.map(i => ({ time: i.time, value: i.lb })));

  // Indicators — only if pane already created
  if (window.rsiSeries) {
    if (rsiData) window.rsiSeries.setData(rsiData.map(i => ({ time: i.time, value: i.value })));
    if (kdjData) {
      window.kdjKSeries.setData(kdjData.map(i => ({ time: i.time, value: i.k })));
      window.kdjDSeries.setData(kdjData.map(i => ({ time: i.time, value: i.d })));
      window.kdjJSeries.setData(kdjData.map(i => ({ time: i.time, value: i.j })));
    }
    if (macdData) {
      window.macdHistogramSeries.setData(macdData.map(i => ({
        time: i.time,
        value: i.macd,
        color: i.macd >= 0 ? "#34C759" : "#F63842",
      })));
      window.macdDifSeries.setData(macdData.map(i => ({ time: i.time, value: i.dif })));
      window.macdDeaSeries.setData(macdData.map(i => ({ time: i.time, value: i.dea })));
    }
  }

  if (isTimeframeChanged) {
    requestAnimationFrame(() => {
      if (window.chart) {
        window.chart.timeScale().applyOptions(DEFAULT_ZOOM);
        window.chart.timeScale().scrollToPosition(DEFAULT_ZOOM.rightOffset, false);
      }
    });
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
