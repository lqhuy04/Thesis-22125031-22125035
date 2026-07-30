import { RelatedStock } from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import React from "react";
import { Pressable, StyleProp, View, ViewStyle } from "react-native";
import { Text } from "./Text";

type Props = {
  maxVisible?: number;
  size?: "default" | "large";
  stocks?: RelatedStock[];
  style?: StyleProp<ViewStyle>;
};

const formatPercentage = (value: number | null) => {
  if (value == null) {
    return "--";
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toLocaleString("vi-VN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}%`;
};

const RelatedStockBadges = ({
  maxVisible,
  size = "default",
  stocks = [],
  style,
}: Props) => {
  const { theme } = useTheme();
  const isLarge = size === "large";
  const visibleStocks =
    maxVisible == null ? stocks : stocks.slice(0, maxVisible);
  const hiddenCount = Math.max(0, stocks.length - visibleStocks.length);

  if (stocks.length === 0) {
    return null;
  }

  return (
    <View
      style={[
        {
          flexDirection: "row",
          flexWrap: "wrap",
          alignItems: "center",
          gap: 4,
        },
        style,
      ]}
    >
      {visibleStocks.map((stock) => {
        const percentageColor =
          stock.per_price_change == null
            ? theme.text.primary + "80"
            : stock.per_price_change > 0
              ? theme.base.success
              : stock.per_price_change < 0
                ? theme.base.error
                : theme.base.warning;

        return (
          <Pressable
            accessibilityHint="Mở trang chi tiết cổ phiếu"
            accessibilityLabel={`${stock.symbol} ${formatPercentage(stock.per_price_change)}`}
            accessibilityRole="button"
            key={stock.symbol}
            onPress={(event) => {
              event.stopPropagation();

              const symbol = stock.symbol.trim();
              if (!symbol) {
                return;
              }

              router.push({
                pathname: "/Detail",
                params: { data: symbol },
              });
            }}
            style={({ pressed }) => [
              {
                flexDirection: "row",
                alignItems: "center",
                gap: isLarge ? 5 : 2,
                paddingHorizontal: isLarge ? 10 : 6,
                paddingVertical: isLarge ? 6 : 2,
                borderRadius: isLarge ? 14 : 10,
                backgroundColor: theme.border.default + "40",
                opacity: pressed ? 0.65 : 1,
              },
            ]}
          >
            <Text
              typography={isLarge ? "labelLarge" : "labelSmall"}
              color={theme.text.primary}
            >
              {stock.symbol}
            </Text>
            <Text
              typography={isLarge ? "labelLarge" : "labelSmall"}
              color={percentageColor}
            >
              {formatPercentage(stock.per_price_change)}
            </Text>
          </Pressable>
        );
      })}

      {hiddenCount > 0 ? (
        <View
          style={{
            paddingHorizontal: isLarge ? 11 : 7,
            paddingVertical: isLarge ? 6 : 2,
            borderRadius: isLarge ? 14 : 10,
            backgroundColor: theme.border.default + "40",
          }}
        >
          <Text
            typography={isLarge ? "labelLarge" : "labelSmall"}
            color={theme.text.primary + "80"}
          >
            +{hiddenCount}
          </Text>
        </View>
      ) : null}
    </View>
  );
};

export default RelatedStockBadges;
