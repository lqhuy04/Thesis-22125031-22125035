import React, { useCallback, useEffect, useMemo, useState } from "react";
import { TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { getWatchlist, WatchItem } from "@/helpers/ProfileHelpers";
import Entypo from "@expo/vector-icons/Entypo";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useLocalization } from "@/hooks/LocalizationContext";

const totalQty = (item: WatchItem) =>
  item.history.reduce((s, h) => s + h.amount, 0);
const totalCost = (item: WatchItem) =>
  item.history.reduce((s, h) => s + h.buy_price * h.amount, 0);
const marketValue = (item: WatchItem) => item.CurrentPrice * totalQty(item);
const pnl = (item: WatchItem) => marketValue(item) - totalCost(item);

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

const HomeAssetSection = ({ registerRefresh }: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
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

  const fetchData = useCallback(async () => {
    getWatchlist().then((res) => {
      if (res?.status) setData(res.data);
    });
  }, []);

  useEffect(() => {
    fetchData(); // gọi lần đầu

    // Đăng ký để Home có thể trigger refresh
    const unregister = registerRefresh?.(fetchData);
    return () => unregister?.();
  }, [fetchData, registerRefresh]);

  const insets = useSafeAreaInsets();

  return (
    <View
      style={{
        alignItems: "center",
        justifyContent: "center",
        paddingBottom: 48,
        paddingTop: 36 + insets.top,
        backgroundColor: theme.base.primary,
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
        <Text typography="titleMedium" color={theme.text.onPrimary}>
          {t("home.asset")}
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

      <Text typography="bodyMedium" color={theme.text.onPrimary}>
        {t("home.yourInvestment")}
        <Text
          typography="labelLarge"
          color={
            totalPnl > 0
              ? theme.base.success
              : totalPnl < 0
                ? theme.base.error
                : theme.base.warning
          }
          style={{ fontWeight: "bold" }}
        >
          {totalPnl > 0 ? "+" : ""}
          {totalPnl.toLocaleString("vi-VN")} đ ({totalPnl > 0 ? "+" : ""}
          {totalPnlPct.toFixed(2)}%)
        </Text>
      </Text>
    </View>
  );
};

export default HomeAssetSection;
