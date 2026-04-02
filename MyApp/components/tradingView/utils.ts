import { WebViewSource } from "react-native-webview/lib/WebViewTypes";
import { TradingViewHtml } from "./trading-view-html";

export type PriceData = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
};

export type VolumeData = {
  time: number;
  value: number;
  color: string;
};

export const getWebViewSource = (): WebViewSource => {
  const source: WebViewSource = {
    html: TradingViewHtml,
  };
  return source;
};

export const samplePrices: PriceData[] = [
  { time: 1711929600, open: 1245.3, high: 1258.7, low: 1240.1, close: 1253.2 },
  { time: 1712016000, open: 1253.2, high: 1265.0, low: 1248.5, close: 1261.8 },
  { time: 1712102400, open: 1261.8, high: 1270.3, low: 1255.2, close: 1258.4 },
  { time: 1712188800, open: 1258.4, high: 1262.1, low: 1241.6, close: 1244.9 },
  { time: 1712275200, open: 1244.9, high: 1252.3, low: 1238.0, close: 1250.6 },
  { time: 1712534400, open: 1250.6, high: 1268.5, low: 1247.3, close: 1265.1 },
  { time: 1712620800, open: 1265.1, high: 1278.9, low: 1260.4, close: 1274.3 },
  { time: 1712707200, open: 1274.3, high: 1280.0, low: 1265.7, close: 1269.8 },
  { time: 1712793600, open: 1269.8, high: 1275.2, low: 1255.1, close: 1258.3 },
  { time: 1712880000, open: 1258.3, high: 1263.4, low: 1244.8, close: 1261.7 },
  { time: 1713139200, open: 1261.7, high: 1272.6, low: 1257.0, close: 1270.2 },
  { time: 1713225600, open: 1270.2, high: 1285.3, low: 1266.8, close: 1282.5 },
  { time: 1713312000, open: 1282.5, high: 1290.1, low: 1275.4, close: 1278.9 },
  { time: 1713398400, open: 1278.9, high: 1283.7, low: 1262.3, close: 1265.4 },
  { time: 1713484800, open: 1265.4, high: 1271.8, low: 1258.2, close: 1268.7 },
  { time: 1713744000, open: 1268.7, high: 1279.4, low: 1264.1, close: 1276.3 },
  { time: 1713830400, open: 1276.3, high: 1288.0, low: 1271.5, close: 1284.9 },
  { time: 1713916800, open: 1284.9, high: 1292.7, low: 1278.3, close: 1281.6 },
  { time: 1714003200, open: 1281.6, high: 1286.4, low: 1265.9, close: 1270.1 },
  { time: 1714089600, open: 1270.1, high: 1275.3, low: 1258.7, close: 1272.8 },
  { time: 1714348800, open: 1272.8, high: 1283.5, low: 1268.2, close: 1280.4 },
  { time: 1714435200, open: 1280.4, high: 1295.1, low: 1276.7, close: 1291.3 },
  { time: 1714521600, open: 1291.3, high: 1298.6, low: 1283.4, close: 1287.5 },
  { time: 1714608000, open: 1287.5, high: 1293.2, low: 1271.8, close: 1275.9 },
  { time: 1714694400, open: 1275.9, high: 1281.4, low: 1267.3, close: 1279.6 },
  { time: 1714953600, open: 1279.6, high: 1291.7, low: 1275.1, close: 1288.2 },
  { time: 1715040000, open: 1288.2, high: 1302.5, low: 1284.6, close: 1298.7 },
  { time: 1715126400, open: 1298.7, high: 1310.3, low: 1293.2, close: 1305.4 },
  { time: 1715212800, open: 1305.4, high: 1312.8, low: 1298.1, close: 1301.9 },
  { time: 1715299200, open: 1301.9, high: 1308.6, low: 1292.4, close: 1306.3 },
];

export const sampleVolumes: VolumeData[] = samplePrices.map((p) => ({
  time: p.time,
  value: Math.round(300_000_000 + Math.random() * 700_000_000),
  color: p.close >= p.open ? "#34C75966" : "#F6384266",
}));

// Timeframe enum (phải khớp với CandleChartOption bên native)
export const TIMEFRAME = {
  UNKNOWN: 0,
  FIFTEEN_MINUTES: 1,
  ONE_HOUR: 2,
  FOUR_HOURS: 3,
  ONE_DAY: 4,
  ONE_WEEK: 5,
  ONE_MONTH: 6,
} as const;
