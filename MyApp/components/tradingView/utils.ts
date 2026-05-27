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

export type VolumeMAData = {
  time: number;
  vma20: number | null;
  vma50: number | null;
};

export type MAData = {
  time: number;
  ma20: number;
  ma50: number;
};

export type BollData = {
  time: number;
  boll: number;
  ub: number;
  lb: number;
};

export type MACDData = {
  time: number;
  macd: number;
  dif: number;
  dea: number;
};

export type RSIData = {
  time: number;
  value: number;
};

export type KDJData = {
  time: number;
  k: number;
  d: number;
  j: number;
};

export const getWebViewSource = (): WebViewSource => {
  const source: WebViewSource = {
    html: TradingViewHtml,
  };
  return source;
};
