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

export const getWebViewSource = (): WebViewSource => {
  const source: WebViewSource = {
    html: TradingViewHtml,
  };
  return source;
};
