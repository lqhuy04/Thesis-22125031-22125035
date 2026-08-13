import React, { useCallback, useEffect, useRef, useState } from "react";
import { Animated, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import {
  fetchRandomMarketIndexStocks,
  fetchRelatedStocks,
  RelatedStockItem,
} from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { router, useFocusEffect } from "expo-router";
import {
  formatPercentageChange,
  getStockChangeColor,
} from "@/helpers/stockChange";

interface RelatedStocksSectionProps {
  stockSymbol?: string;
  marketIndexId?: string;
  registerRefresh?: (fn: () => Promise<void>) => () => void;
}

// Chia mảng thành các hàng `size` phần tử, phần thiếu được fill object rỗng
// để giữ layout lưới đều nhau (giống phần lịch sử tìm kiếm).
function chunkArray<T>(arr: T[], size: number = 3): (T | any)[][] {
  const result: (T | any)[][] = [];

  for (let i = 0; i < arr.length; i += size) {
    const chunk: (T | any)[] = arr.slice(i, i + size);

    while (chunk.length < size) {
      chunk.push({});
    }

    result.push(chunk);
  }

  return result;
}

// ── Skeleton ────────────────────────────────────────────────────────────────
const RelatedStocksSkeleton = () => {
  const { theme } = useTheme();
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: 900,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, [shimmer]);

  const opacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [0.4, 0.85],
  });

  return (
    <View>
      {[0, 1].map((row) => (
        <View
          key={row}
          style={{
            flexWrap: "wrap",
            flexDirection: "row",
            marginHorizontal: 12,
            gap: 8,
            marginTop: 12,
          }}
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <Animated.View
              key={i}
              style={{
                flex: 1,
                minWidth: 0,
                height: 52,
                borderRadius: 8,
                backgroundColor: theme.background.bg,
                opacity,
              }}
            />
          ))}
        </View>
      ))}
    </View>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const RelatedStocksSection = ({
  stockSymbol,
  marketIndexId,
  registerRefresh,
}: RelatedStocksSectionProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [related, setRelated] = useState<RelatedStockItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Khoá điều hướng để tránh push nhiều trang Detail khi bấm nhanh nhiều lần
  const isNavigatingRef = useRef(false);

  useFocusEffect(
    useCallback(() => {
      isNavigatingRef.current = false;
    }, []),
  );

  const fetchData = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    isNavigatingRef.current = false;
    try {
      const result = marketIndexId
        ? await fetchRandomMarketIndexStocks(marketIndexId)
        : stockSymbol
          ? await fetchRelatedStocks(stockSymbol)
          : { status: true, data: [] };
      if (result.status) {
        setRelated(result.data);
      }
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [marketIndexId, stockSymbol]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Pull-to-refresh
  useEffect(() => {
    const unregister = registerRefresh?.(() => fetchData(false));
    return () => unregister?.();
  }, [registerRefresh, fetchData]);

  const goToStock = (symbol: string) => {
    if (!symbol || isNavigatingRef.current) return;
    isNavigatingRef.current = true;
    router.push({
      pathname: "/Detail",
      params: { data: symbol },
    });
  };

  const sectionTitle = marketIndexId
    ? t("detail.indexConstituentsTitle")
    : t("detail.relatedSectionTitle");

  if (loading) {
    return (
      <View>
        <Text
          typography="titleLarge"
          color={theme.text.primary}
          style={{ marginHorizontal: 12, marginTop: 24 }}
        >
          {sectionTitle}
        </Text>
        <RelatedStocksSkeleton />
      </View>
    );
  }

  if (related.length === 0) return null;

  const distributed = chunkArray(related, 3);

  return (
    <View>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginHorizontal: 12, marginTop: 24 }}
      >
        {sectionTitle}
      </Text>

      <View>
        {distributed.map((row, index) => (
          <View
            key={index.toString()}
            style={{
              flexWrap: "wrap",
              flexDirection: "row",
              marginHorizontal: 12,
              marginTop: 12,
              gap: 8,
            }}
          >
            {row.map((item, subIndex) =>
              item?.symbol != null ? (
                <TouchableOpacity
                  onPress={() => goToStock(item?.symbol)}
                  key={subIndex.toString() + index.toString()}
                  style={{
                    backgroundColor: theme.background.bg,
                    padding: 10,
                    borderRadius: 8,
                    flex: 1,
                  }}
                >
                  <Text
                    color={theme.text.primary}
                    typography="titleSmall"
                    style={{ marginBottom: 4 }}
                  >
                    {item?.symbol}
                  </Text>

                  <Text
                    color={getStockChangeColor(
                      item?.per_price_change,
                      theme.base,
                    )}
                    typography="bodySmall"
                  >
                    {item?.current_price?.toLocaleString("vi-VN", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}{" "}
                    {formatPercentageChange(item?.per_price_change)}
                  </Text>
                </TouchableOpacity>
              ) : (
                <View
                  key={subIndex.toString() + index.toString()}
                  style={{ padding: 10, borderRadius: 8, flex: 1 }}
                />
              ),
            )}
          </View>
        ))}
      </View>
    </View>
  );
};

export default RelatedStocksSection;
