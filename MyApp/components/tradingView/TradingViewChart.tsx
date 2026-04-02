import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { ActivityIndicator, View } from "react-native";
import { WebView } from "react-native-webview";
import { WebViewMessageEvent } from "react-native-webview/lib/WebViewTypes";
import { getWebViewSource, PriceData, VolumeData } from "./utils";
import injectedJavaScript from "./trading-view-script";

type Props = {
  prices: PriceData[];
  volumes: VolumeData[];
  timeframe: number;
  chartType: "candle" | "area";
};

const TradingViewChart = ({ prices, volumes, timeframe, chartType }: Props) => {
  const webViewRef = useRef<WebView>(null);
  const isChartReady = useRef(false);

  const WEB_VIEW_SOURCE = useMemo(() => getWebViewSource(), []);
  const injectedJavaScriptCode = useMemo(() => injectedJavaScript(), []);

  const injectScript = useCallback((script: string) => {
    webViewRef.current?.injectJavaScript(script);
  }, []);

  const updateChartData = useCallback(
    (p: PriceData[], v: VolumeData[], tf: number) => {
      const script = /*javascript*/ `
        (function() {
          try {
            if (window.updateChartData) {
              window.updateChartData(${JSON.stringify(p)}, ${JSON.stringify(v)}, ${tf});
            }
          } catch (_e) {}
        })();
        true;
      `;
      injectScript(script);
    },
    [injectScript],
  );

  const switchSeriesType = useCallback(
    (type: "candle" | "area") => {
      const script = /*javascript*/ `
        (function() {
          try {
            if (window.switchSeriesType) window.switchSeriesType("${type}");
          } catch (_e) {}
        })();
        true;
      `;
      injectScript(script);
    },
    [injectScript],
  );

  const onMessage = useCallback(
    (event: WebViewMessageEvent) => {
      try {
        const message = JSON.parse(event.nativeEvent.data);
        if (message.type === "chart-ready") {
          isChartReady.current = true;
          // Push initial data as soon as chart signals ready
          if (prices.length > 0 && volumes.length > 0) {
            updateChartData(prices, volumes, timeframe);
          }
        }
      } catch (_e) {
        console.error(_e);
      }
    },
    [prices, updateChartData, timeframe, volumes],
  );

  // Update chart whenever data or timeframe changes (after chart is ready)
  useEffect(() => {
    if (!isChartReady.current) return;
    if (prices.length === 0 || volumes.length === 0) return;
    updateChartData(prices, volumes, timeframe);
  }, [prices, volumes, timeframe, updateChartData]);

  useEffect(() => {
    switchSeriesType(chartType);
  }, [chartType, switchSeriesType]);

  return (
    <View style={{ height: 270 }}>
      <WebView
        ref={webViewRef}
        source={WEB_VIEW_SOURCE}
        cacheEnabled={true}
        cacheMode="LOAD_CACHE_ELSE_NETWORK"
        domStorageEnabled={true}
        javaScriptEnabled={true}
        startInLoadingState={true}
        scrollEnabled={false}
        bounces={false}
        overScrollMode="never"
        showsHorizontalScrollIndicator={false}
        showsVerticalScrollIndicator={false}
        onMessage={onMessage}
        renderLoading={() => (
          <View
            style={{
              width: "100%",
              height: "100%",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ActivityIndicator size="small" />
          </View>
        )}
        injectedJavaScriptBeforeContentLoaded={injectedJavaScriptCode}
        webviewDebuggingEnabled={false}
      />
    </View>
  );
};

export default TradingViewChart;
