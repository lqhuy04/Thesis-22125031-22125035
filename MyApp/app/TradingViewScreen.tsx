import { Text } from "@/components/ui/Text";
import React, { useCallback, useMemo, useRef, useState } from "react";
import { Platform, StyleSheet, TouchableOpacity, View } from "react-native";
import {
  SafeAreaView,
  useSafeAreaFrame,
  useSafeAreaInsets,
} from "react-native-safe-area-context";
import { WebView } from "react-native-webview";
import {
  WebViewErrorEvent,
  WebViewHttpErrorEvent,
} from "react-native-webview/lib/WebViewTypes";
import { router, useLocalSearchParams } from "expo-router";
import Ionicons from "@expo/vector-icons/Ionicons";
import FontAwesome6 from "@expo/vector-icons/FontAwesome6";
import { useTheme } from "@/hooks/ThemeContext";

const BASE_URL = "https://vn.tradingview.com/chart";
const TRADINGVIEW_DOMAIN = "tradingview.com/chart";
const FLOATING_BUTTON_SIZE = 36;
const ICON_SIZE = 16;
const SHADOW_RADIUS = 3.84;
const LANDSCAPE_BUTTON_LEFT_MULTIPLIER = 1.5;

const injectedJavaScript = /*javascript*/ `
(function() {
    window.open = function() {
        return null;
    };

    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
        get: function() {
            return originalLocation;
        },
        set: function() {
            return;
        }
    });

    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href) {
            const href = link.href;
            const currentOrigin = window.location.origin;
            if (!href.startsWith(currentOrigin) && !href.startsWith('#')) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        }
    }, true);

    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form && form.action) {
            const action = form.action;
            const currentOrigin = window.location.origin;
            if (!action.startsWith(currentOrigin) && action !== '' && !action.startsWith('#')) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        }
    }, true);
})();
true;
`;

interface FloatingButtonProps {
  onPress: () => void;
  renderIcon: () => React.JSX.Element;
}

const FloatingButton: React.FC<FloatingButtonProps> = ({
  onPress,
  renderIcon,
}) => {
  const { theme } = useTheme();

  return (
    <TouchableOpacity onPress={onPress}>
      <View
        style={[
          styles.shadow,
          {
            width: FLOATING_BUTTON_SIZE,
            height: FLOATING_BUTTON_SIZE,
            borderRadius: 8,
            backgroundColor: theme.base.primary,
            opacity: 0.8,
            justifyContent: "center",
            alignItems: "center",
          },
        ]}
      >
        {renderIcon()}
      </View>
    </TouchableOpacity>
  );
};

const TradingViewScreen = () => {
  const { theme } = useTheme();
  const { data } = useLocalSearchParams() || {};
  const { symbol: stockCode, exchange } = data
    ? (JSON.parse(data as string) as any)
    : {};

  const { bottom, top } = useSafeAreaInsets();
  const { width: screenWidth, height: screenHeight } = useSafeAreaFrame();

  const safeHeight = useMemo(
    () => screenHeight - top - bottom,
    [bottom, screenHeight, top],
  );

  const webViewRef = useRef<WebView>(null);
  const [isLandscape, setIsLandscape] = useState(false);
  const [hasError, setHasError] = useState(false);

  const handleShouldStartLoadWithRequest = useCallback(
    (request: { url: string }) => {
      return request.url.includes(TRADINGVIEW_DOMAIN);
    },
    [],
  );

  const handleError = useCallback((_event: WebViewErrorEvent) => {
    setHasError(true);
  }, []);

  const handleHttpError = useCallback((event: WebViewHttpErrorEvent) => {
    if (event.nativeEvent.statusCode >= 400) {
      setHasError(true);
    }
  }, []);

  const handleRetry = useCallback(() => {
    setHasError(false);
    webViewRef.current?.reload();
  }, []);

  const handleGoBack = useCallback(() => {
    router.dismiss();
  }, []);

  const handleToggleOrientation = useCallback(() => {
    setIsLandscape((prev) => !prev);
  }, []);

  const webViewUri = useMemo(
    () =>
      `${BASE_URL}?symbol=${stockCode === "HNXUpcomIndex" ? "HNX:301" : exchange ? `${exchange}:${stockCode}` : stockCode}`,
    [stockCode, exchange],
  );

  const containerBoxStyle = useMemo(() => {
    if (!isLandscape) {
      return { width: screenWidth, height: safeHeight };
    }
    return {
      ...styles.containerLandscape,
      width: safeHeight,
      height: screenWidth,
      top: (safeHeight - screenWidth) / 2 + top,
      left: (screenWidth - safeHeight) / 2,
    };
  }, [isLandscape, safeHeight, screenWidth, top]);

  const floatingButtonsStyle = useMemo(() => {
    if (!isLandscape) {
      return {
        ...styles.floatingButtonsPortrait,
        bottom: bottom + 64,
      };
    }
    return {
      ...styles.floatingButtonsLandscape,
      bottom: Platform.select({ ios: 24, android: -12 }) || 12,
      left: 64 * LANDSCAPE_BUTTON_LEFT_MULTIPLIER,
    };
  }, [isLandscape, bottom]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={containerBoxStyle}>
        <WebView
          ref={webViewRef}
          style={styles.webView}
          source={{ uri: webViewUri }}
          startInLoadingState
          injectedJavaScript={injectedJavaScript}
          onShouldStartLoadWithRequest={handleShouldStartLoadWithRequest}
          onError={handleError}
          onHttpError={handleHttpError}
          scrollEnabled={!isLandscape}
          bounces={false}
          overScrollMode="never"
          showsHorizontalScrollIndicator={false}
          showsVerticalScrollIndicator={false}
        />
        {hasError && (
          <View style={styles.errorOverlay}>
            <View style={styles.errorContainer}>
              <Text onPress={handleRetry}>
                Không tải được biểu đồ. Kiểm tra kết nối internet và thử lại.
              </Text>
            </View>
          </View>
        )}
      </View>
      <View
        style={[floatingButtonsStyle, { position: "absolute", zIndex: 1000 }]}
      >
        <View style={{ marginBottom: 4 }}>
          <FloatingButton
            onPress={handleToggleOrientation}
            renderIcon={() => (
              <FontAwesome6
                name="arrows-rotate"
                size={ICON_SIZE}
                color={theme.text.onPrimary}
              />
            )}
          />
        </View>
        <FloatingButton
          onPress={handleGoBack}
          renderIcon={() => (
            <Ionicons
              name="close-sharp"
              size={ICON_SIZE}
              color={theme.text.onPrimary}
            />
          )}
        />
      </View>
    </SafeAreaView>
  );
};

export default TradingViewScreen;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  containerLandscape: {
    position: "absolute",
    transform: [{ rotate: "90deg" }],
  },
  webView: {
    height: "100%",
    width: "100%",
  },
  floatingButtonsPortrait: {
    position: "absolute",
    right: 12,
  },
  floatingButtonsLandscape: {
    transform: [{ rotate: "90deg" }],
  },
  shadow: {
    shadowColor: "#303233",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: SHADOW_RADIUS,
    elevation: 5,
  },
  errorOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#ffffff",
    justifyContent: "center",
    alignItems: "center",
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
});
