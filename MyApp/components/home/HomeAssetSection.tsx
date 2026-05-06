import React, { useEffect, useMemo, useState } from "react";
import { TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { getWatchlist, WatchItem } from "@/helpers/ProfileHelpers";
import Entypo from "@expo/vector-icons/Entypo";
import { router } from "expo-router";

const totalQty = (item: WatchItem) =>
  item.history.reduce((s, h) => s + h.amount, 0);
const totalCost = (item: WatchItem) =>
  item.history.reduce((s, h) => s + h.buy_price * h.amount, 0);
const marketValue = (item: WatchItem) => item.CurrentPrice * totalQty(item);
const pnl = (item: WatchItem) => marketValue(item) - totalCost(item);

const HomeAssetSection = () => {
  const { theme } = useTheme();
  const [data, setData] = useState<WatchItem[]>([]);

  const totalAsset = useMemo(
    () => data.reduce((s, item) => s + marketValue(item), 0) * 1000,
    [data],
  );

  const totalPnl = useMemo(
    () => data.reduce((s, item) => s + pnl(item), 0) * 1000,
    [data],
  );

  const totalCostAll = useMemo(
    () => data.reduce((s, item) => s + totalCost(item), 0),
    [data],
  );
  const totalPnlPct = useMemo(
    () => (totalCostAll === 0 ? 0 : totalPnl / totalCostAll),
    [totalPnl, totalCostAll],
  );

  const isProfit = totalPnl >= 0;
  const sign = isProfit ? "+" : "";

  useEffect(() => {
    getWatchlist().then((res) => {
      if (res?.status) setData(res.data);
    });
  }, []);

  return (
    <View
      style={{
        alignItems: "center",
        justifyContent: "center",
        marginVertical: 36,
      }}
    >
      <TouchableOpacity
        onPress={() => router.push("/WatchListStock")}
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <Text typography="titleSmall" color={theme.text.onPrimary}>
          Tài sản ròng
        </Text>
        <Entypo
          name="chevron-small-right"
          size={20}
          color={theme.text.onPrimary}
        />
      </TouchableOpacity>

      <Text
        typography="headlineLarge"
        color={theme.text.onPrimary}
        style={{ marginBottom: 12 }}
      >
        {totalAsset.toLocaleString("vi-VN")} đ
      </Text>

      <Text typography="bodySmall" color={theme.text.onPrimary}>
        Khoản đầu tư của bạn đang:{" "}
        <Text
          typography="bodySmall"
          color={isProfit ? theme.base.success : theme.base.error}
          style={{ fontWeight: "bold" }}
        >
          {sign}
          {totalPnl.toLocaleString("vi-VN")} đ ({sign}
          {totalPnlPct.toFixed(2)}%)
        </Text>
      </Text>
    </View>
  );
};

export default HomeAssetSection;
