import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { ActivityIndicator, View } from "react-native";
import { WebView } from "react-native-webview";
import { WebViewMessageEvent } from "react-native-webview/lib/WebViewTypes";
import {
  BollData,
  getWebViewSource,
  MAData,
  PriceData,
  VolumeData,
} from "./utils";
import injectedJavaScript from "./trading-view-script";

type Props = {
  prices: PriceData[];
  volumes: VolumeData[];
  maData: MAData[];
  bollData: BollData[];
  timeframe: number;
  chartType: "candle" | "area";
  showVolume: boolean;
  technicalIndicatorMode1: string | null;
};

const TradingViewChart = ({
  prices,
  volumes,
  maData,
  bollData,
  timeframe,
  chartType,
  showVolume,
  technicalIndicatorMode1,
}: Props) => {
  const webViewRef = useRef<WebView>(null);
  const isChartReady = useRef(false);

  const WEB_VIEW_SOURCE = useMemo(() => getWebViewSource(), []);
  const injectedJavaScriptCode = useMemo(() => injectedJavaScript(), []);

  const injectScript = useCallback((script: string) => {
    webViewRef.current?.injectJavaScript(script);
  }, []);

  const updateChartData = useCallback(
    (
      p: PriceData[],
      v: VolumeData[],
      maData: MAData[],
      bollData: BollData[],
      tf: number,
    ) => {
      const script = /*javascript*/ `
        (function() {
          try {
            if (window.updateChartData) {
              window.updateChartData(${JSON.stringify(p)}, ${JSON.stringify(v)}, ${JSON.stringify(maData)}, ${JSON.stringify(bollData)}, ${tf});
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

  const setVolumeVisible = useCallback(
    (visible: boolean) => {
      const script = /*javascript*/ `
        (function() {
          try {
            if (window.setVolumeVisible) window.setVolumeVisible(${visible});
          } catch (_e) {}
        })();
        true;
      `;
      injectScript(script);
    },
    [injectScript],
  );

  const setTechnicalIndicatorMode1 = useCallback(
    (mode: string | null) => {
      const script = /*javascript*/ `
      (function() {
        try {
          if (window.setTechnicalIndicatorMode1) window.setTechnicalIndicatorMode1(${JSON.stringify(mode)});
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
            updateChartData(prices, volumes, maData, bollData, timeframe);
          }
          // Áp dụng trạng thái volume ngay khi chart ready
          setVolumeVisible(showVolume);
        }
      } catch (_e) {
        console.error(_e);
      }
    },
    [
      prices,
      volumes,
      setVolumeVisible,
      showVolume,
      updateChartData,
      maData,
      bollData,
      timeframe,
    ],
  );

  // Update chart whenever data or timeframe changes (after chart is ready)
  useEffect(() => {
    if (!isChartReady.current) return;
    if (prices.length === 0 || volumes.length === 0) return;
    updateChartData(prices, volumes, maData, bollData, timeframe);
  }, [prices, volumes, timeframe, updateChartData, maData, bollData]);

  useEffect(() => {
    if (!isChartReady.current) return;
    switchSeriesType(chartType);
  }, [chartType, switchSeriesType]);

  useEffect(() => {
    if (!isChartReady.current) return;
    setVolumeVisible(showVolume);
  }, [showVolume, setVolumeVisible]);

  useEffect(() => {
    if (!isChartReady.current) return;
    setTechnicalIndicatorMode1(technicalIndicatorMode1);
  }, [technicalIndicatorMode1, setTechnicalIndicatorMode1]);

  return (
    <View style={{ height: 300 }}>
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
