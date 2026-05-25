import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Dimensions, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { getWatchlist, WatchItem } from "@/helpers/ProfileHelpers";
import { router } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useSafeAreaInsets } from "react-native-safe-area-context";

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

  const screenWidth = Dimensions.get("window").width;
  const insets = useSafeAreaInsets();

  return (
    <View
      style={{
        alignItems: "center",
        justifyContent: "center",
        paddingTop: insets.top + 24,
        paddingBottom: 48,
      }}
    >
      <TouchableOpacity
        onPress={() => router.push("/WatchListStock")}
        activeOpacity={1}
        style={{
          borderRadius: 12,
          backgroundColor: theme.background.bg + "36",
          borderWidth: 1,
          borderColor: theme.background.bg,
          padding: 24,
          width: screenWidth - 48,
        }}
      >
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("home.asset")}
        </Text>

        <Text
          typography="headlineLarge"
          style={{ marginVertical: 8, fontSize: 36, lineHeight: 48 }}
          color={theme.text.primary}
        >
          {totalAsset.toLocaleString("vi-VN")} đ
        </Text>

        <Text typography="bodyMedium" color={theme.text.primary}>
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
      </TouchableOpacity>
    </View>
  );
};

export default HomeAssetSection;
