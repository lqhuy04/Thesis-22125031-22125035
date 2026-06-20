import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import Feather from "@expo/vector-icons/Feather";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import ScreenFooter from "@/components/ScreenFooter";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import {
  CurrentPriceData,
  fetchCurrentPriceData,
} from "@/helpers/DetailHelpers";
import { addStockToWatchList } from "@/helpers/ProfileHelpers";

// Màu sàn theo quy ước thị trường VN (cyan) — không có sẵn trong theme tokens.
const FLOOR_COLOR = "#22A7C9";

const fmtPrice = (n?: number) =>
  (n ?? 0).toLocaleString("vi-VN", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  });

const BuyStock = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const { data } = useLocalSearchParams() || {};
  const symbol = (data as string) ?? "";

  const [priceData, setPriceData] = useState<CurrentPriceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  // null = chưa đặt lệnh, true = thành công, false = thất bại
  const [result, setResult] = useState<boolean | null>(null);

  // Fetch lại giá hiện tại / trần / sàn / tham chiếu mỗi khi mã thay đổi
  // (bao gồm khi quay lại từ trang Search với mã mới).
  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchCurrentPriceData(symbol).then((res) => {
      if (!active) return;
      if (res.status && res.data) {
        setPriceData(res.data);
        setPrice(String(res.data.CurrentPrice ?? ""));
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [symbol]);

  const change = priceData?.PerPriceChange ?? 0;
  const changeColor =
    change > 0
      ? theme.base.success
      : change < 0
        ? theme.base.error
        : theme.base.warning;

  const parsedPrice = parseFloat(price.replace(",", "."));
  const parsedQty = parseInt(quantity, 10);
  const canBuy = parsedPrice > 0 && parsedQty > 0;

  const handleBuy = async () => {
    if (!canBuy) return;

    setSubmitting(true);
    const res = await addStockToWatchList({
      symbol,
      amount: parsedQty,
      buy_price: parsedPrice,
      time: new Date().toISOString(),
    });
    setSubmitting(false);
    setResult(res.status);
  };

  const inputStyle = [
    styles.input,
    {
      borderColor: theme.border.default,
      backgroundColor: theme.background.bg,
      color: theme.text.primary,
    },
  ];

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title={t("buyStock.screenTitle")} />

      {loading ? (
        <View style={styles.loader}>
          <ActivityIndicator size="large" color={theme.base.primary} />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.scroll}>
          {/* ─── Block thông tin mã ─── */}
          <View
            style={[
              styles.card,
              {
                backgroundColor: theme.background.bg,
                borderColor: theme.border.default,
              },
            ]}
          >
            <View style={styles.symbolRow}>
              <View style={styles.symbolLeft}>
                <Text typography="titleLarge" color={theme.text.primary}>
                  {symbol}
                  {priceData?.exchange ? (
                    <Text typography="bodyMedium" color={theme.text.primary}>
                      {`  (${priceData.exchange})`}
                    </Text>
                  ) : null}
                </Text>

                <TouchableOpacity
                  style={styles.changeSymbol}
                  onPress={() =>
                    router.push({
                      pathname: "/Search",
                      params: { returnTo: "BuyStock" },
                    })
                  }
                >
                  <Feather
                    name="refresh-cw"
                    size={13}
                    color={theme.base.primary}
                  />
                  <Text typography="labelLarge" color={theme.base.primary}>
                    {t("buyStock.changeSymbol")}
                  </Text>
                </TouchableOpacity>
              </View>

              <TouchableOpacity
                style={styles.detailLink}
                onPress={() =>
                  router.dismissTo({
                    pathname: "/Detail",
                    params: { data: symbol },
                  })
                }
              >
                <Text typography="labelLarge" color={theme.base.primary}>
                  {t("buyStock.detail")}
                </Text>
                <Feather
                  name="chevron-right"
                  size={16}
                  color={theme.base.primary}
                />
              </TouchableOpacity>
            </View>

            {/* Giá hiện tại + % thay đổi */}
            <View style={styles.priceRow}>
              <Text typography="headlineSmall" color={changeColor}>
                {fmtPrice(priceData?.CurrentPrice)}
              </Text>
              <Text typography="labelLarge" color={changeColor}>
                {change > 0 ? "▲" : change < 0 ? "▼" : ""}
                {Math.abs(change).toFixed(2)}%
              </Text>
            </View>

            {/* Trần / Tham chiếu / Sàn */}
            <View
              style={[styles.bandRow, { borderTopColor: theme.border.default }]}
            >
              <View style={styles.bandItem}>
                <Text typography="labelMedium" color={theme.text.primary}>
                  {t("detailHeader.ceiling")}
                </Text>
                <Text typography="titleSmall" color={theme.base.primary}>
                  {fmtPrice(priceData?.CeilingPrice)}
                </Text>
              </View>
              <View style={styles.bandItem}>
                <Text typography="labelMedium" color={theme.text.primary}>
                  {t("detailHeader.reference")}
                </Text>
                <Text typography="titleSmall" color={theme.base.warning}>
                  {fmtPrice(priceData?.RefPrice)}
                </Text>
              </View>
              <View style={styles.bandItem}>
                <Text typography="labelMedium" color={theme.text.primary}>
                  {t("detailHeader.floor")}
                </Text>
                <Text typography="titleSmall" color={FLOOR_COLOR}>
                  {fmtPrice(priceData?.FloorPrice)}
                </Text>
              </View>
            </View>
          </View>

          {/* ─── Giá ─── */}
          <View
            style={[
              styles.card,
              {
                backgroundColor: theme.background.bg,
                borderColor: theme.border.default,
              },
            ]}
          >
            <Text
              typography="labelLarge"
              color={theme.text.primary}
              style={{ opacity: 0.6, marginBottom: 6 }}
            >
              {t("buyStock.priceLabel")}
            </Text>
            <View
              style={[
                styles.input,
                {
                  borderColor: theme.border.default,
                  backgroundColor: theme.background.surface,
                },
              ]}
            >
              <Text
                typography="titleLarge"
                color={theme.text.primary}
              >
                {fmtPrice(priceData?.CurrentPrice)}
              </Text>
            </View>
          </View>

          {/* ─── Khối lượng ─── */}
          <View
            style={[
              styles.card,
              {
                backgroundColor: theme.background.bg,
                borderColor: theme.border.default,
              },
            ]}
          >
            <Text
              typography="labelLarge"
              color={theme.text.primary}
              style={{ opacity: 0.6, marginBottom: 6 }}
            >
              {t("buyStock.quantityLabel")}
            </Text>
            <TextInput
              style={inputStyle}
              keyboardType="number-pad"
              value={quantity}
              onChangeText={(val) => setQuantity(val.replace(/[^0-9]/g, ""))}
              placeholder={t("buyStock.quantityPlaceholder")}
              placeholderTextColor={theme.text.primary + "55"}
            />
          </View>
        </ScrollView>
      )}

      <ScreenFooter
        onPressBuy={handleBuy}
        loading={submitting}
        disabled={!canBuy}
      />

      {/* Modal kết quả đặt lệnh */}
      <Modal
        visible={result !== null}
        transparent
        animationType="fade"
        statusBarTranslucent
        onRequestClose={() => setResult(null)}
      >
        <View style={styles.modalOverlay}>
          <View
            style={[
              styles.modalCard,
              {
                backgroundColor: theme.background.bg,
                borderColor: theme.border.default,
              },
            ]}
          >
            <View
              style={[
                styles.iconCircle,
                {
                  backgroundColor:
                    (result ? theme.base.success : theme.base.error) + "20",
                },
              ]}
            >
              <SimpleLineIcons
                name={result ? "check" : "close"}
                size={28}
                color={result ? theme.base.success : theme.base.error}
              />
            </View>

            <Text
              typography="titleLarge"
              color={theme.text.primary}
              style={{ textAlign: "center" }}
            >
              {t(result ? "buyStock.successTitle" : "buyStock.errorTitle")}
            </Text>

            <Text
              typography="bodyMedium"
              color={theme.text.secondary}
              style={{ textAlign: "center" }}
            >
              {result
                ? t("buyStock.successMessage").replace("{symbol}", symbol)
                : t("buyStock.errorMessage")}
            </Text>

            <TouchableOpacity
              style={[styles.modalButton, { backgroundColor: theme.base.primary }]}
              activeOpacity={0.8}
              onPress={() => {
                const ok = result;
                setResult(null);
                if (ok) router.back();
              }}
            >
              <Text typography="titleLarge" color={theme.text.onPrimary}>
                OK
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

export default BuyStock;

const styles = StyleSheet.create({
  safe: { flex: 1 },
  loader: { flex: 1, alignItems: "center", justifyContent: "center" },
  scroll: { gap: 12, padding: 12 },

  card: {
    borderRadius: 14,
    borderWidth: 0.5,
    padding: 14,
  },

  symbolRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  symbolLeft: { gap: 6 },
  changeSymbol: { flexDirection: "row", alignItems: "center", gap: 4 },
  detailLink: { flexDirection: "row", alignItems: "center", gap: 2 },

  priceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 12,
  },

  bandRow: {
    flexDirection: "row",
    borderTopWidth: 0.5,
    marginTop: 12,
    paddingTop: 12,
  },
  bandItem: { flex: 1, gap: 2 },

  tabRow: { flexDirection: "row" },
  tabBuy: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    borderRadius: 24,
    borderWidth: 1,
  },

  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 18,
    fontWeight: "600",
  },

  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  modalCard: {
    width: "100%",
    borderRadius: 20,
    borderWidth: 0.5,
    padding: 24,
    alignItems: "center",
    gap: 16,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 4,
  },
  modalButton: {
    width: "100%",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 4,
  },
});
