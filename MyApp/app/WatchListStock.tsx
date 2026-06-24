import {
  getWatchlist,
  HistoryItem,
  removeWatchListRecords,
  WatchItem,
} from "@/helpers/ProfileHelpers";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ActivityIndicator,
  Animated,
  Modal,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import { useSafeAreaInsets } from "react-native-safe-area-context";

// ─── helpers ────────────────────────────────────────────────────────────────

const fmtTime = (iso?: string) => {
  if (!iso) return "-";
  const d = new Date(iso);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
};

const MONEY_SCALE = 1000;
const fmt = (n: number) => (n * MONEY_SCALE).toLocaleString("vi-VN") + " đ";

const avgBuyPrice = (item: WatchItem): number => {
  const qty = item.history.reduce((s, h) => s + h.amount, 0);
  if (qty === 0) return 0;
  return item.history.reduce((s, h) => s + h.buy_price * h.amount, 0) / qty;
};
const totalQty = (item: WatchItem) =>
  item.history.reduce((s, h) => s + h.amount, 0);
const totalCost = (item: WatchItem) =>
  item.history.reduce((s, h) => s + h.buy_price * h.amount, 0);
const marketValue = (item: WatchItem) => item.CurrentPrice * totalQty(item);
const pnl = (item: WatchItem) => marketValue(item) - totalCost(item);
const pnlPct = (item: WatchItem) => {
  const cost = totalCost(item);
  return cost === 0 ? 0 : (pnl(item) / cost) * 100;
};

// ─── SkeletonBox ──────────────────────────────────────────────────────────────

const useShimmer = () => {
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [shimmer]);

  return shimmer;
};

const SkeletonBox = ({
  width,
  height,
  borderRadius = 8,
  style,
}: {
  width?: number | string;
  height: number;
  borderRadius?: number;
  style?: any;
}) => {
  const { theme } = useTheme();
  const shimmer = useShimmer();

  const opacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [0.35, 0.7],
  });

  return (
    <Animated.View
      style={[
        {
          width: width ?? "100%",
          height,
          borderRadius,
          backgroundColor: theme.border.default,
          opacity,
        },
        style,
      ]}
    />
  );
};

// ─── SkeletonSummaryCard ──────────────────────────────────────────────────────

const SkeletonSummaryCard = () => {
  const { theme } = useTheme();
  return (
    <View
      style={[
        styles.summaryCard,
        {
          backgroundColor: theme.background.bg,
          borderColor: theme.border.default,
        },
      ]}
    >
      <SkeletonBox width="55%" height={12} borderRadius={6} />
      <SkeletonBox
        width="80%"
        height={20}
        borderRadius={6}
        style={{ marginTop: 6 }}
      />
      <SkeletonBox
        width="60%"
        height={12}
        borderRadius={6}
        style={{ marginTop: 4 }}
      />
    </View>
  );
};

// ─── SkeletonStockCard ────────────────────────────────────────────────────────

const SkeletonStockCard = () => {
  const { theme } = useTheme();
  return (
    <View
      style={[
        styles.stockCard,
        {
          backgroundColor: theme.background.bg,
          borderColor: theme.border.default,
        },
      ]}
    >
      {/* Header */}
      <View style={styles.stockHeader}>
        <View style={{ gap: 6 }}>
          <SkeletonBox width={60} height={18} borderRadius={6} />
          <SkeletonBox width={120} height={12} borderRadius={6} />
        </View>
        <View style={{ alignItems: "flex-end", gap: 6 }}>
          <SkeletonBox width={100} height={16} borderRadius={6} />
          <SkeletonBox width={60} height={12} borderRadius={6} />
        </View>
      </View>

      {/* Meta row */}
      <View style={[styles.metaRow, { borderTopColor: theme.border.default }]}>
        {[0, 1, 2, 3, 4].map((i) => (
          <View key={i} style={[styles.metaItem, { gap: 6 }]}>
            <SkeletonBox width="70%" height={10} borderRadius={5} />
            <SkeletonBox width="90%" height={14} borderRadius={5} />
          </View>
        ))}
      </View>

      {/* History label */}
      <View style={[styles.historyHeader, { marginTop: 12 }]}>
        <SkeletonBox width={80} height={12} borderRadius={6} />
        <SkeletonBox width={16} height={12} borderRadius={4} />
      </View>
    </View>
  );
};

// ─── WatchListSkeleton ────────────────────────────────────────────────────────

const WatchListSkeleton = () => (
  <View style={[styles.scroll, { gap: 12 }]}>
    {/* Summary row */}
    <View style={styles.summaryRow}>
      <SkeletonSummaryCard />
      <SkeletonSummaryCard />
    </View>

    {/* List header */}
    <View style={styles.listHeader}>
      <SkeletonBox width={160} height={18} borderRadius={8} />
    </View>

    {/* Stock cards */}
    {[0, 1, 2].map((i) => (
      <SkeletonStockCard key={i} />
    ))}
  </View>
);

// ─── ConfirmDeleteModal ───────────────────────────────────────────────────────

type ConfirmDeleteModalProps = {
  visible: boolean;
  title: string;
  deleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  children: React.ReactNode;
};

const ConfirmDeleteModal = ({
  visible,
  title,
  deleting,
  onCancel,
  onConfirm,
  children,
}: ConfirmDeleteModalProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <Pressable
        style={styles.dateOverlay}
        onPress={() => !deleting && onCancel()}
      >
        <Pressable
          style={[
            styles.datePopup,
            {
              backgroundColor: theme.background.bg,
              borderColor: theme.border.default,
            },
          ]}
        >
          <Text
            typography="titleLarge"
            color={theme.text.primary}
            style={{ marginBottom: 6 }}
          >
            {title}
          </Text>
          {children}

          <View style={styles.confirmButtons}>
            <TouchableOpacity
              style={[
                styles.confirmBtn,
                {
                  borderWidth: 1,
                  borderColor: theme.border.default,
                  backgroundColor: theme.background.surface,
                },
              ]}
              onPress={onCancel}
              disabled={deleting}
            >
              <Text typography="titleMedium" color={theme.text.primary}>
                {t("watchList.cancel")}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.confirmBtn, { backgroundColor: theme.base.error }]}
              onPress={onConfirm}
              disabled={deleting}
            >
              {deleting ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text typography="titleMedium" color="#fff">
                  {t("watchList.delete")}
                </Text>
              )}
            </TouchableOpacity>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
};

// ─── SummaryCard ─────────────────────────────────────────────────────────────

type SummaryCardProps = {
  label: string;
  value: string;
  sub?: string;
  gainColor?: string;
};

const SummaryCard = ({ label, value, sub, gainColor }: SummaryCardProps) => {
  const { theme } = useTheme();
  return (
    <View
      style={[
        styles.summaryCard,
        {
          backgroundColor: theme.background.bg,
          borderColor: theme.border.default,
        },
      ]}
    >
      <Text
        typography="labelLarge"
        color={theme.text.primary}
        style={{ opacity: 0.5 }}
      >
        {label}
      </Text>
      <Text
        typography="titleLarge"
        color={gainColor ?? theme.text.primary}
        style={{ marginTop: 4, marginBottom: 2 }}
      >
        {value}
      </Text>
      {sub ? (
        <Text
          typography="labelLarge"
          color={gainColor ?? theme.text.primary}
          style={{ opacity: gainColor ? 0.85 : 0.5 }}
        >
          {sub}
        </Text>
      ) : null}
    </View>
  );
};

// ─── StockCard ───────────────────────────────────────────────────────────────

const StockCard = ({
  item,
  onDeleted,
}: {
  item: WatchItem;
  onDeleted: () => void;
}) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [expanded, setExpanded] = useState(false);
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const gain = pnl(item);
  const pct = pnlPct(item);
  const isZero = gain === 0;
  const isProfit = gain > 0;
  const gainColor = isZero
    ? theme.base.warning
    : isProfit
      ? theme.base.success
      : theme.base.error;
  const sign = isProfit ? "+" : "";
  const qty = totalQty(item);
  const mktVal = marketValue(item);
  const avg = avgBuyPrice(item);
  const cost = totalCost(item);

  const handleDelete = async () => {
    setDeleting(true);
    const ids = item.history.map((h) => h.id);
    const res = await removeWatchListRecords({ portfolio_ids: ids });
    setDeleting(false);
    if (res.status) {
      setConfirmVisible(false);
      onDeleted();
    }
  };

  const confirmParts = t("watchList.deleteStockConfirm").split("{symbol}");

  return (
    <View
      style={[
        styles.stockCard,
        {
          backgroundColor: theme.background.bg,
          borderColor: theme.border.default,
        },
      ]}
    >
      <View style={styles.stockHeader}>
        <View style={styles.stockTitleGroup}>
          <Text typography="titleLarge" color={theme.text.primary}>
            {item.symbol}
          </Text>
          <Text
            typography="bodyMedium"
            color={theme.text.primary}
            style={{ opacity: 0.45 }}
          >
            {item.company_name}
          </Text>
        </View>
        <View style={styles.pnlBox}>
          <Text
            typography="bodyLarge"
            color={gainColor}
            style={styles.textRight}
          >
            {sign}
            {fmt(gain)}
          </Text>
          <Text
            typography="labelLarge"
            color={gainColor}
            style={styles.textRight}
          >
            {sign}
            {pct.toFixed(2)}%
          </Text>
        </View>
      </View>

      <View style={[styles.metaRow, { borderTopColor: theme.border.default }]}>
        {[
          { label: t("watchList.currentPrice"), val: fmt(item.CurrentPrice) },
          { label: t("watchList.avgPrice"), val: fmt(avg) },
          {
            label: t("watchList.volume"),
            val: `${qty.toLocaleString("vi-VN")} ${t("watchList.shares")}`,
          },
          { label: t("watchList.marketValue"), val: fmt(mktVal) },
          { label: t("watchList.capital"), val: fmt(cost) },
        ].map(({ label, val }) => (
          <View key={label} style={styles.metaItem}>
            <Text
              typography="labelLarge"
              color={theme.text.primary}
              style={{ opacity: 0.45 }}
            >
              {label}
            </Text>
            <Text typography="bodyLarge" color={theme.text.primary}>
              {val}
            </Text>
          </View>
        ))}
      </View>

      <View style={styles.historyHeader}>
        <Text
          typography="labelLarge"
          color={theme.text.primary}
          style={{ opacity: 0.6 }}
        >
          {t("watchList.buyHistory")}
        </Text>
        <TouchableOpacity onPress={() => setExpanded(!expanded)}>
          <SimpleLineIcons
            name={expanded ? "arrow-up" : "arrow-down"}
            size={10}
            color={theme.text.primary}
          />
        </TouchableOpacity>
      </View>

      {expanded && item.history.length > 0 && (
        <View style={styles.historyTable}>
          <View style={styles.historyRowLine}>
            <Text
              typography="titleSmall"
              color={theme.text.primary}
              style={styles.colLeft}
            >
              {t("watchList.colAmount")}
            </Text>
            <Text
              typography="titleSmall"
              color={theme.text.primary}
              style={styles.colCenter}
            >
              {t("watchList.colPrice")}
            </Text>
            <Text
              typography="titleSmall"
              color={theme.text.primary}
              style={styles.colCenter}
            >
              {t("watchList.colTime")}
            </Text>
            <Text
              typography="titleSmall"
              color={theme.text.primary}
              style={styles.colRight}
            >
              {t("watchList.colAction")}
            </Text>
          </View>

          {item.history.map((h, i) => (
            <HistoryRow
              key={h.id ?? `history-${i}`}
              h={h}
              theme={theme}
              onDeleted={onDeleted}
            />
          ))}
        </View>
      )}

      <TouchableOpacity
        style={[
          styles.deleteStockButton,
          { backgroundColor: theme.base.error },
        ]}
        onPress={() => setConfirmVisible(true)}
      >
        <SimpleLineIcons name="trash" size={14} color={theme.text.onPrimary} />
        <Text typography="titleMedium" color={theme.text.onPrimary}>
          {t("watchList.deleteStock")}
        </Text>
      </TouchableOpacity>

      <ConfirmDeleteModal
        visible={confirmVisible}
        title={t("watchList.deleteStock")}
        deleting={deleting}
        onCancel={() => setConfirmVisible(false)}
        onConfirm={handleDelete}
      >
        <Text
          typography="bodyLarge"
          color={theme.text.primary}
          style={{ opacity: 0.6, marginBottom: 12 }}
        >
          {confirmParts[0]}
          <Text typography="bodyMedium" color={theme.base.primary}>
            {item.symbol}
          </Text>
          {confirmParts[1]}
        </Text>
      </ConfirmDeleteModal>
    </View>
  );
};

// ─── HistoryRow ───────────────────────────────────────────────────────────────

const HistoryRow = ({
  h,
  theme,
  onDeleted,
}: {
  h: HistoryItem;
  theme: any;
  onDeleted: () => void;
}) => {
  const { t } = useLocalization();
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    const res = await removeWatchListRecords({ portfolio_ids: [h.id] });
    setDeleting(false);
    if (res.status) {
      setConfirmVisible(false);
      onDeleted();
    }
  };

  const amountLabel = `${h.amount.toLocaleString()} ${t("watchList.shares")}`;
  const confirmParts = t("watchList.deleteHistoryConfirm")
    .replace("{date}", fmtTime(h.time))
    .split("{amount}");

  return (
    <View style={styles.historyRowLine}>
      <Text style={styles.colLeft} color={theme.text.primary}>
        {h.amount.toLocaleString()}
      </Text>
      <Text style={styles.colCenter} color={theme.text.primary}>
        {fmt(h.buy_price)}
      </Text>
      <Text style={styles.colCenter} color={theme.text.primary}>
        {fmtTime(h.time)}
      </Text>

      <View style={styles.colRight}>
        <TouchableOpacity onPress={() => setConfirmVisible(true)}>
          <SimpleLineIcons name="trash" size={14} color={theme.base.error} />
        </TouchableOpacity>
      </View>

      <ConfirmDeleteModal
        visible={confirmVisible}
        title={t("watchList.deleteHistory")}
        deleting={deleting}
        onCancel={() => setConfirmVisible(false)}
        onConfirm={handleDelete}
      >
        <Text
          typography="bodyMedium"
          color={theme.text.primary}
          style={{ opacity: 0.6, marginBottom: 20 }}
        >
          {confirmParts[0]}
          <Text typography="bodyMedium" color={theme.base.primary}>
            {amountLabel}
          </Text>
          {confirmParts[1]}
        </Text>
      </ConfirmDeleteModal>
    </View>
  );
};

// ─── Main ────────────────────────────────────────────────────────────────────

const WatchListStock = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<WatchItem[]>([]);
  const insets = useSafeAreaInsets();

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    const res = await getWatchlist();
    if (res?.status) setData(res.data);

    if (isRefresh) {
      setRefreshing(false);
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalAsset = useMemo(
    () => data.reduce((s, item) => s + marketValue(item), 0),
    [data],
  );
  const totalPnl = useMemo(
    () => data.reduce((s, item) => s + pnl(item), 0),
    [data],
  );
  const totalCostAll = useMemo(
    () => data.reduce((s, item) => s + totalCost(item), 0),
    [data],
  );
  const totalPnlPct = useMemo(
    () => (totalCostAll === 0 ? 0 : (totalPnl / totalCostAll) * 100),
    [totalPnl, totalCostAll],
  );

  const isZero = totalPnl === 0;
  const isProfit = totalPnl > 0;
  const sign = isProfit ? "+" : "";
  const gainColor = isZero
    ? theme.base.warning
    : isProfit
      ? theme.base.success
      : theme.base.error;

  return (
    <View
      style={[
        styles.safe,
        {
          backgroundColor: theme.background.surface,
          marginTop: insets.top,
        },
      ]}
    >
      {loading ? (
        <WatchListSkeleton />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchData(true)}
              tintColor={theme.base.primary}
              colors={[theme.base.primary]}
            />
          }
        >
          <View style={styles.summaryRow}>
            <SummaryCard
              label={t("watchList.totalAsset")}
              value={fmt(totalAsset)}
              sub={`${t("watchList.capitalLabel")}: ${fmt(totalCostAll)}`}
            />
            <SummaryCard
              label={t("watchList.profitLoss")}
              value={`${sign}${fmt(totalPnl)}`}
              sub={`${sign}${totalPnlPct.toFixed(2)}%`}
              gainColor={gainColor}
            />
          </View>

          <View style={styles.listHeader}>
            <Text typography="titleLarge" color={theme.text.primary}>
              {t("watchList.stockList")}
            </Text>
          </View>

          {data.length === 0 ? (
            <View style={styles.emptyBox}>
              <SimpleLineIcons
                name="graph"
                size={36}
                color={theme.text.primary}
                style={{ opacity: 0.35 }}
              />
              <Text
                typography="bodyLarge"
                color={theme.text.primary}
                style={{ opacity: 0.5, textAlign: "center" }}
              >
                {t("watchList.empty")}
              </Text>
            </View>
          ) : (
            data.map((item) => (
              <StockCard
                key={item.id}
                item={item}
                onDeleted={() => fetchData()}
              />
            ))
          )}
        </ScrollView>
      )}
    </View>
  );
};

export default WatchListStock;

// ─── styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: { flex: 1 },
  scroll: { gap: 12, marginHorizontal: 12 },

  summaryRow: { flexDirection: "row", gap: 10, marginTop: 4 },
  summaryCard: {
    flex: 1,
    borderRadius: 12,
    padding: 14,
    gap: 3,
    borderWidth: 1,
  },

  stockCard: { borderRadius: 14, borderWidth: 0.5, padding: 14 },
  stockHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 12,
  },
  stockTitleGroup: { gap: 2 },
  pnlBox: { alignItems: "flex-end", gap: 2 },
  textRight: { textAlign: "right" },
  metaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    borderTopWidth: 0.5,
    paddingTop: 12,
    gap: 8,
  },
  metaItem: { width: "30%", gap: 3 },
  historyHeader: {
    marginTop: 12,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  historyTable: { marginTop: 8, gap: 6 },
  historyRowLine: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  colLeft: { flex: 0.1, textAlign: "left" },
  colCenter: { flex: 0.35, textAlign: "center" },
  colRight: { flex: 0.2, textAlign: "center", alignItems: "center" },
  listHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
  },

  emptyBox: {
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingVertical: 48,
  },

  dateOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  datePopup: {
    width: "100%",
    borderRadius: 16,
    borderWidth: 0.5,
    padding: 16,
    gap: 8,
  },
  confirmButtons: { flexDirection: "row", gap: 10 },
  confirmBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  deleteStockButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    marginTop: 14,
    paddingVertical: 10,
    borderRadius: 10,
  },
});
