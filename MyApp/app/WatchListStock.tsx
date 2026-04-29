import {
  addStockToWatchList,
  getWatchlist,
  HistoryItem,
  removeWatchListRecords,
  updateWatchListRecord,
  WatchItem,
} from "@/helpers/ProfileHelpers";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Text } from "@/components/ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import DateTimePicker from "@react-native-community/datetimepicker";
import { SearchStockItem, searchStocks } from "@/helpers/SearchHelper";

// ─── helpers ────────────────────────────────────────────────────────────────

const fmtTime = (iso?: string) => {
  if (!iso) return "-";
  const d = new Date(iso);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
};

const fmtDate = (d: Date) => {
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  return `${day}/${month}/${d.getFullYear()}`;
};

const toISODay = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}T00:00:00.000Z`;
};

const MONEY_SCALE = 1000;
const fmt = (n: number) => (n * MONEY_SCALE).toLocaleString("vi-VN") + " ₫";

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

// ─── EditHistoryModal ─────────────────────────────────────────────────────────

type EditHistoryModalProps = {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
  historyItem: HistoryItem | null;
  symbol: string;
};

const EditHistoryModal = ({
  visible,
  onClose,
  onSuccess,
  historyItem,
  symbol,
}: EditHistoryModalProps) => {
  const { theme } = useTheme();

  const [amount, setAmount] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [date, setDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Điền sẵn thông tin khi mở modal
  useEffect(() => {
    if (historyItem) {
      setAmount(String(historyItem.amount));
      setBuyPrice(String(historyItem.buy_price));
      setDate(historyItem.time ? new Date(historyItem.time) : new Date());
      setError("");
    }
  }, [historyItem, visible]);

  const handleClose = () => {
    setError("");
    onClose();
  };

  const handleSave = async () => {
    if (!historyItem) return;
    const amt = parseInt(amount, 10);
    const price = parseFloat(buyPrice);
    if (!amt || amt <= 0) return setError("Số lượng không hợp lệ.");
    if (!price || price <= 0) return setError("Giá mua không hợp lệ.");

    setError("");
    setSaving(true);
    const res = await updateWatchListRecord({
      portfolio_id: historyItem.id,
      amount: amt,
      buy_price: price,
      time: toISODay(date),
    });
    setSaving(false);

    if (res.status) {
      onSuccess();
    } else {
      setError("Cập nhật thất bại, vui lòng thử lại.");
    }
  };

  const inputStyle = [
    styles.input,
    {
      borderColor: theme.border.default,
      color: theme.text.primary,
      backgroundColor: theme.background.surface,
    },
  ];

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
    >
      <Pressable style={styles.overlay} onPress={handleClose}>
        <Pressable
          style={[
            styles.sheet,
            {
              backgroundColor: theme.background.bg,
              borderColor: theme.border.default,
            },
          ]}
          onPress={() => {}}
        >
          {/* Title */}
          <View style={styles.modalHeader}>
            <View
              style={{ gap: 2, flexDirection: "row", alignItems: "center" }}
            >
              <Text typography="titleLarge">Cập nhật lịch sử mua </Text>
              <Text typography="titleLarge" color={theme.base.primary}>
                {symbol}
              </Text>
            </View>
            <TouchableOpacity onPress={handleClose}>
              <SimpleLineIcons
                name="close"
                size={16}
                color={theme.text.primary}
              />
            </TouchableOpacity>
          </View>

          {/* Amount */}
          <Text typography="labelLarge" style={styles.fieldLabel}>
            Số lượng (cp)
          </Text>
          <TextInput
            style={inputStyle}
            placeholder="VD: 100"
            placeholderTextColor={theme.text.primary + "55"}
            keyboardType="number-pad"
            value={amount}
            onChangeText={(t) => setAmount(t.replace(/[^0-9]/g, ""))}
          />

          {/* Buy price */}
          <Text typography="labelLarge" style={styles.fieldLabel}>
            Giá mua (nghìn ₫/cp)
          </Text>
          <TextInput
            style={inputStyle}
            placeholder="VD: 24.5"
            placeholderTextColor={theme.text.primary + "55"}
            keyboardType="decimal-pad"
            value={buyPrice}
            onChangeText={(t) => {
              const filtered = t.replace(/[^0-9.]/g, "");
              const parts = filtered.split(".");
              if (parts.length > 2) return;
              if (parts[1]?.length > 1) return;
              setBuyPrice(filtered);
            }}
          />

          {/* Date picker */}
          <Text typography="labelLarge" style={styles.fieldLabel}>
            Ngày mua
          </Text>
          <TouchableOpacity
            style={[inputStyle, styles.dateTrigger]}
            onPress={() => setShowDatePicker(true)}
          >
            <Text typography="bodyMedium" color={theme.text.primary}>
              {fmtDate(date)}
            </Text>
            <SimpleLineIcons
              name="calendar"
              size={14}
              color={theme.text.primary + "88"}
            />
          </TouchableOpacity>

          {/* Date picker modal */}
          <Modal
            visible={showDatePicker}
            transparent
            animationType="fade"
            onRequestClose={() => setShowDatePicker(false)}
          >
            <Pressable
              style={styles.dateOverlay}
              onPress={() => setShowDatePicker(false)}
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
                <View style={styles.datePopupHeader}>
                  <Text typography="titleMedium">Chọn ngày mua</Text>
                  <TouchableOpacity onPress={() => setShowDatePicker(false)}>
                    <SimpleLineIcons
                      name="close"
                      size={14}
                      color={theme.text.primary}
                    />
                  </TouchableOpacity>
                </View>
                <DateTimePicker
                  value={date}
                  mode="date"
                  display="inline"
                  maximumDate={new Date()}
                  onChange={(_, selected) => {
                    if (selected) {
                      setDate(selected);
                      setShowDatePicker(false);
                    }
                  }}
                  style={styles.datePicker}
                />
              </Pressable>
            </Pressable>
          </Modal>

          {/* Error */}
          {!!error && (
            <Text
              typography="labelLarge"
              color={theme.base.error}
              style={styles.errorText}
            >
              {error}
            </Text>
          )}

          {/* Save button */}
          <TouchableOpacity
            style={[styles.saveButton, { backgroundColor: theme.base.primary }]}
            onPress={handleSave}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator color={theme.text.onPrimary} />
            ) : (
              <Text typography="titleLarge" color={theme.text.onPrimary}>
                Lưu
              </Text>
            )}
          </TouchableOpacity>
        </Pressable>
      </Pressable>
    </Modal>
  );
};

// ─── AddStockModal ────────────────────────────────────────────────────────────

type AddStockModalProps = {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

const AddStockModal = ({ visible, onClose, onSuccess }: AddStockModalProps) => {
  const { theme } = useTheme();

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchStockItem[]>([]);
  const [selectedStock, setSelectedStock] = useState<SearchStockItem | null>(
    null,
  );
  const [searching, setSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const [amount, setAmount] = useState("");
  const [buyPrice, setBuyPrice] = useState("");

  const [date, setDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // debounced search
  useEffect(() => {
    if (query.length < 1) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(async () => {
      if (query.length < 1) return; // ← guard ở đây
      setSearching(true);
      const res = await searchStocks(query);
      const valid = res.filter((s) => s.stock_id != null);
      setSearchResults(valid);
      setShowDropdown(valid.length > 0);
      setSearching(false);
    }, 350);
  }, [query]);

  const reset = () => {
    setQuery("");
    setSearchResults([]);
    setSelectedStock(null);
    setShowDropdown(false);
    setAmount("");
    setBuyPrice("");
    setDate(new Date());
    setShowDatePicker(false);
    setError("");
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSave = async () => {
    if (!selectedStock) return setError("Vui lòng chọn mã cổ phiếu.");
    const amt = parseInt(amount, 10);
    const price = parseFloat(buyPrice);
    if (!amt || amt <= 0) return setError("Số lượng không hợp lệ.");
    if (!price || price <= 0) return setError("Giá mua không hợp lệ.");

    setError("");
    setSaving(true);
    const res = await addStockToWatchList({
      symbol: selectedStock.symbol,
      amount: amt,
      buy_price: price,
      time: toISODay(date),
    });
    setSaving(false);

    if (res.status) {
      reset();
      onSuccess();
    } else {
      setError("Lưu thất bại, vui lòng thử lại.");
    }
  };

  const inputStyle = [
    styles.input,
    {
      borderColor: theme.border.default,
      color: theme.text.primary,
      backgroundColor: theme.background.surface,
    },
  ];

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
    >
      <Pressable style={styles.overlay} onPress={handleClose}>
        <Pressable
          style={[
            styles.sheet,
            {
              backgroundColor: theme.background.bg,
              borderColor: theme.border.default,
            },
          ]}
          onPress={() => {}}
        >
          {/* Title */}
          <View style={styles.modalHeader}>
            <Text typography="titleLarge">Thêm cổ phiếu</Text>
            <TouchableOpacity onPress={handleClose}>
              <SimpleLineIcons
                name="close"
                size={16}
                color={theme.text.primary}
              />
            </TouchableOpacity>
          </View>

          {/* Symbol search */}
          <Text typography="labelLarge" style={styles.fieldLabel}>
            Mã cổ phiếu
          </Text>
          <View style={styles.searchWrapper}>
            <View style={[inputStyle, styles.searchInputRow]}>
              <TextInput
                style={[styles.searchTextInput, { color: theme.text.primary }]}
                placeholder="Tìm mã hoặc tên công ty..."
                placeholderTextColor={theme.text.primary + "55"}
                value={
                  selectedStock
                    ? `${selectedStock.symbol} – ${selectedStock.company_name}`
                    : query
                }
                onChangeText={(t) => {
                  setSelectedStock(null);
                  setQuery(t);
                  if (t.length === 0) {
                    if (searchTimeout.current)
                      clearTimeout(searchTimeout.current);
                    setShowDropdown(false);
                    setSearchResults([]);
                  }
                }}
                onFocus={() => {
                  if (selectedStock) {
                    setSelectedStock(null);
                    setQuery("");
                  }
                  if (searchResults.length > 0) setShowDropdown(true);
                }}
              />
              {searching && (
                <ActivityIndicator size="small" color={theme.base.primary} />
              )}
            </View>

            {showDropdown && (
              <View
                style={[
                  styles.dropdown,
                  {
                    backgroundColor: theme.background.bg,
                    borderColor: theme.border.default,
                  },
                ]}
              >
                <ScrollView
                  keyboardShouldPersistTaps="handled"
                  nestedScrollEnabled
                  style={{ maxHeight: 200 }}
                >
                  {searchResults.map((s, i) => (
                    <TouchableOpacity
                      key={s.stock_id ?? `stock-${i}`}
                      style={[
                        styles.dropdownItem,
                        { borderBottomColor: theme.border.default },
                      ]}
                      onPress={() => {
                        setSelectedStock(s);
                        setQuery("");
                        setShowDropdown(false);
                      }}
                    >
                      <Text typography="titleSmall" color={theme.base.primary}>
                        {s.symbol}
                      </Text>
                      <Text typography="bodySmall" style={{ opacity: 0.55 }}>
                        {s.company_name}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            )}
          </View>

          {/* Amount */}
          <Text typography="labelLarge" style={styles.fieldLabel}>
            Số lượng (cp)
          </Text>
          <TextInput
            style={inputStyle}
            placeholder="VD: 100"
            placeholderTextColor={theme.text.primary + "55"}
            keyboardType="number-pad"
            value={amount}
            onChangeText={(t) => setAmount(t.replace(/[^0-9]/g, ""))}
          />

          {/* Buy price */}
          <Text typography="labelLarge" style={styles.fieldLabel}>
            Giá mua (nghìn ₫/cp)
          </Text>
          <TextInput
            style={inputStyle}
            placeholder="VD: 24.5"
            placeholderTextColor={theme.text.primary + "55"}
            keyboardType="decimal-pad"
            value={buyPrice}
            onChangeText={(t) => {
              const filtered = t.replace(/[^0-9.]/g, "");
              const parts = filtered.split(".");
              if (parts.length > 2) return;
              if (parts[1]?.length > 1) return;
              setBuyPrice(filtered);
            }}
          />

          {/* Date picker */}
          <Text typography="labelLarge" style={styles.fieldLabel}>
            Ngày mua
          </Text>
          <TouchableOpacity
            style={[inputStyle, styles.dateTrigger]}
            onPress={() => setShowDatePicker(true)}
          >
            <Text typography="bodyMedium" color={theme.text.primary}>
              {fmtDate(date)}
            </Text>
            <SimpleLineIcons
              name="calendar"
              size={14}
              color={theme.text.primary + "88"}
            />
          </TouchableOpacity>

          {/* Date picker modal */}
          <Modal
            visible={showDatePicker}
            transparent
            animationType="fade"
            onRequestClose={() => setShowDatePicker(false)}
          >
            <Pressable
              style={styles.dateOverlay}
              onPress={() => setShowDatePicker(false)}
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
                <View style={styles.datePopupHeader}>
                  <Text typography="titleMedium">Chọn ngày mua</Text>
                  <TouchableOpacity onPress={() => setShowDatePicker(false)}>
                    <SimpleLineIcons
                      name="close"
                      size={14}
                      color={theme.text.primary}
                    />
                  </TouchableOpacity>
                </View>

                <DateTimePicker
                  value={date}
                  mode="date"
                  display="inline"
                  maximumDate={new Date()}
                  onChange={(_, selected) => {
                    if (selected) {
                      setDate(selected);
                      setShowDatePicker(false);
                    }
                  }}
                  style={styles.datePicker}
                />
              </Pressable>
            </Pressable>
          </Modal>

          {/* Error */}
          {!!error && (
            <Text
              typography="labelLarge"
              color={theme.base.error}
              style={styles.errorText}
            >
              {error}
            </Text>
          )}

          {/* Save button */}
          <TouchableOpacity
            style={[styles.saveButton, { backgroundColor: theme.base.primary }]}
            onPress={handleSave}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator color={theme.text.onPrimary} />
            ) : (
              <Text typography="titleLarge" color={theme.text.onPrimary}>
                Lưu
              </Text>
            )}
          </TouchableOpacity>
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
      <Text typography="labelLarge" style={{ opacity: 0.5 }}>
        {label}
      </Text>
      <Text typography="titleLarge" color={gainColor ?? theme.text.primary}>
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
  const [expanded, setExpanded] = useState(false);
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const gain = pnl(item);
  const pct = pnlPct(item);
  const isProfit = gain >= 0;
  const gainColor = isProfit ? theme.base.success : theme.base.error;
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
          <Text typography="titleLarge">{item.symbol}</Text>
          <Text typography="bodyMedium" style={{ opacity: 0.45 }}>
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
          { label: "Giá hiện tại", val: fmt(item.CurrentPrice) },
          { label: "Giá vốn TB", val: fmt(avg) },
          { label: "Khối lượng", val: `${qty.toLocaleString("vi-VN")} cp` },
          { label: "Giá trị", val: fmt(mktVal) },
          { label: "Vốn", val: fmt(cost) },
        ].map(({ label, val }) => (
          <View key={label} style={styles.metaItem}>
            <Text typography="labelLarge" style={{ opacity: 0.45 }}>
              {label}
            </Text>
            <Text typography="bodyLarge">{val}</Text>
          </View>
        ))}
      </View>

      <View style={styles.historyHeader}>
        <Text typography="labelLarge" style={{ opacity: 0.6 }}>
          Lịch sử mua
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
          {/* Header row */}
          <View style={styles.historyRowLine}>
            <Text typography="titleSmall" style={styles.colLeft}>
              SL
            </Text>
            <Text typography="titleSmall" style={styles.colCenter}>
              Giá
            </Text>
            <Text typography="titleSmall" style={styles.colCenter}>
              Thời gian
            </Text>
            <Text typography="titleSmall" style={styles.colRight}>
              Hành động
            </Text>
          </View>

          {item.history.map((h, i) => (
            <HistoryRow
              key={h.id ?? `history-${i}`}
              h={h}
              theme={theme}
              onDeleted={onDeleted}
              symbol={item.symbol}
            />
          ))}
        </View>
      )}

      <TouchableOpacity
        style={[styles.deleteStockButton, { borderColor: theme.base.error }]}
        onPress={() => setConfirmVisible(true)}
      >
        <Text typography="titleMedium" color={theme.base.error}>
          Xoá cổ phiếu
        </Text>
      </TouchableOpacity>

      {/* Confirm modal */}
      <Modal
        visible={confirmVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmVisible(false)}
      >
        <Pressable
          style={styles.dateOverlay}
          onPress={() => !deleting && setConfirmVisible(false)}
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
            <Text typography="titleLarge" style={{ marginBottom: 6 }}>
              Xoá cổ phiếu
            </Text>
            <Text
              typography="bodyLarge"
              style={{ opacity: 0.6, marginBottom: 12 }}
            >
              Bạn có chắc muốn xoá{" "}
              <Text typography="bodyMedium" color={theme.base.primary}>
                {item.symbol}
              </Text>{" "}
              khỏi danh sách? Toàn bộ lịch sử mua sẽ bị xoá.
            </Text>

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
                onPress={() => setConfirmVisible(false)}
                disabled={deleting}
              >
                <Text typography="titleMedium">Huỷ</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.confirmBtn,
                  { backgroundColor: theme.base.error },
                ]}
                onPress={handleDelete}
                disabled={deleting}
              >
                {deleting ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text typography="titleMedium" color="#fff">
                    Xoá
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
};

// ─── HistoryRow ───────────────────────────────────────────────────────────────
const HistoryRow = ({
  h,
  symbol,
  theme,
  onDeleted,
}: {
  h: HistoryItem;
  symbol: string;
  theme: any;
  onDeleted: () => void;
}) => {
  const [menuVisible, setMenuVisible] = useState(false);
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [editVisible, setEditVisible] = useState(false); // ← thêm
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

  return (
    <View style={styles.historyRowLine}>
      <Text style={styles.colLeft}>{h.amount.toLocaleString()}</Text>
      <Text style={styles.colCenter}>{fmt(h.buy_price)}</Text>
      <Text style={styles.colCenter}>{fmtTime(h.time)}</Text>

      {/* 3 chấm */}
      <View style={styles.colRight}>
        <TouchableOpacity onPress={() => setMenuVisible(true)}>
          <SimpleLineIcons
            name="options-vertical"
            size={12}
            color={theme.text.primary}
          />
        </TouchableOpacity>
      </View>

      {/* Menu modal */}
      <Modal
        visible={menuVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setMenuVisible(false)}
      >
        <Pressable
          style={styles.dateOverlay}
          onPress={() => setMenuVisible(false)}
        >
          <Pressable
            style={[
              styles.menuPopup,
              {
                backgroundColor: theme.background.bg,
                borderColor: theme.border.default,
              },
            ]}
          >
            <Text typography="titleLarge" style={{ marginBottom: 2 }}>
              {symbol}
            </Text>
            <Text
              typography="labelLarge"
              style={{ opacity: 0.45, marginBottom: 2 }}
            >
              {fmtTime(h.time)} · {h.amount.toLocaleString()} cp
            </Text>
            <Text
              typography="labelLarge"
              style={{ opacity: 0.45, marginBottom: 14 }}
            >
              Đơn giá: {fmt(h.buy_price)}
            </Text>

            <View style={styles.confirmButtons}>
              <TouchableOpacity
                style={[
                  styles.confirmBtn,
                  {
                    borderWidth: 1,
                    borderColor: theme.border.default,
                    backgroundColor: theme.background.surface,
                    flexDirection: "row",
                    gap: 6,
                  },
                ]}
                onPress={() => {
                  setMenuVisible(false);
                  setEditVisible(true); // ← mở edit modal
                }}
              >
                <SimpleLineIcons
                  name="pencil"
                  size={14}
                  color={theme.text.primary}
                />
                <Text typography="titleMedium">Cập nhật</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.confirmBtn,
                  {
                    backgroundColor: theme.base.error,
                    flexDirection: "row",
                    gap: 6,
                  },
                ]}
                onPress={() => {
                  setMenuVisible(false);
                  setConfirmVisible(true);
                }}
              >
                <SimpleLineIcons name="trash" size={14} color="#fff" />
                <Text typography="titleMedium" color="#fff">
                  Xoá
                </Text>
              </TouchableOpacity>
            </View>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Edit modal */}
      <EditHistoryModal
        visible={editVisible}
        onClose={() => setEditVisible(false)}
        onSuccess={() => {
          setEditVisible(false);
          onDeleted(); // reuse fetchData
        }}
        historyItem={h}
        symbol={symbol}
      />

      {/* Confirm delete modal — giữ nguyên */}
      <Modal
        visible={confirmVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmVisible(false)}
      >
        <Pressable
          style={styles.dateOverlay}
          onPress={() => !deleting && setConfirmVisible(false)}
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
            <Text typography="titleLarge" style={{ marginBottom: 6 }}>
              Xoá lịch sử mua
            </Text>
            <Text
              typography="bodyMedium"
              style={{ opacity: 0.6, marginBottom: 20 }}
            >
              Bạn có chắc muốn xoá lần mua{" "}
              <Text typography="bodyMedium" color={theme.base.primary}>
                {h.amount.toLocaleString()} cp
              </Text>{" "}
              ngày {fmtTime(h.time)}?
            </Text>

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
                onPress={() => setConfirmVisible(false)}
                disabled={deleting}
              >
                <Text typography="titleMedium">Huỷ</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.confirmBtn,
                  { backgroundColor: theme.base.error },
                ]}
                onPress={handleDelete}
                disabled={deleting}
              >
                {deleting ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text typography="titleMedium" color="#fff">
                    Xoá
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
};
// ─── Main ────────────────────────────────────────────────────────────────────

const WatchListStock = () => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<WatchItem[]>([]);
  const [showAdd, setShowAdd] = useState(false);

  const fetchData = () => {
    setLoading(true);
    getWatchlist().then((res) => {
      if (res?.status) setData(res.data);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchData();
  }, []);

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

  const isProfit = totalPnl >= 0;
  const sign = isProfit ? "+" : "";
  const gainColor = isProfit ? theme.base.success : theme.base.error;

  return (
    <SafeAreaView
      style={[styles.safe, { backgroundColor: theme.background.bg }]}
    >
      {loading ? (
        <ActivityIndicator style={styles.loader} color={theme.base.primary} />
      ) : (
        <View
          style={{
            marginHorizontal: 12,
          }}
        >
          <View style={styles.summaryRow}>
            <SummaryCard
              label="Tổng tài sản"
              value={fmt(totalAsset)}
              sub={`Vốn: ${fmt(totalCostAll)}`}
            />
            <SummaryCard
              label="Lãi / Lỗ"
              value={`${sign}${fmt(totalPnl)}`}
              sub={`${sign}${totalPnlPct.toFixed(2)}%`}
              gainColor={gainColor}
            />
          </View>

          <View style={styles.listHeader}>
            <Text typography="titleLarge">Danh sách cổ phiếu</Text>
            <TouchableOpacity
              style={[
                styles.addButton,
                { backgroundColor: theme.base.primary },
              ]}
              onPress={() => setShowAdd(true)}
            >
              <Text typography="titleMedium" color={theme.text.onPrimary}>
                + Thêm
              </Text>
            </TouchableOpacity>
          </View>
          <ScrollView contentContainerStyle={styles.scroll}>
            {data.map((item) => (
              <StockCard key={item.id} item={item} onDeleted={fetchData} />
            ))}
          </ScrollView>
        </View>
      )}

      <AddStockModal
        visible={showAdd}
        onClose={() => setShowAdd(false)}
        onSuccess={() => {
          setShowAdd(false);
          fetchData();
        }}
      />
    </SafeAreaView>
  );
};

export default WatchListStock;

// ─── styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: { flex: 1 },
  loader: { flex: 1 },
  scroll: { gap: 12 },

  summaryRow: { flexDirection: "row", gap: 10 },
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
  historyRowLine: { flexDirection: "row", justifyContent: "space-between" },
  colLeft: { flex: 0.1, textAlign: "left" },
  colCenter: { flex: 0.35, textAlign: "center" },
  colRight: { flex: 0.2, textAlign: "center", alignItems: "center" },
  listHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginVertical: 12,
  },
  addButton: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 20 },

  // modal
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "flex-end",
  },
  sheet: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderWidth: 0.5,
    padding: 20,
    gap: 6,
    paddingBottom: 36,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  fieldLabel: { marginTop: 10, marginBottom: 4, opacity: 0.55 },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
  },
  searchWrapper: { position: "relative", zIndex: 10 },
  searchInputRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 12,
    gap: 8,
  },
  searchTextInput: { flex: 1, fontSize: 15, padding: 0 },
  dropdown: {
    position: "absolute",
    top: "100%",
    left: 0,
    right: 0,
    borderWidth: 1,
    borderRadius: 10,
    marginTop: 4,
    elevation: 6,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
  },
  dropdownItem: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    gap: 2,
  },
  dateTrigger: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  errorText: { marginTop: 4 },
  saveButton: {
    marginTop: 16,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
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
  datePopupHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  datePicker: {
    width: "100%",
  },
  confirmButtons: {
    flexDirection: "row",
    gap: 10,
  },
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
    borderWidth: 1,
  },

  menuPopup: {
    width: "85%",
    borderRadius: 14,
    borderWidth: 0.5,
    padding: 16,
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    borderBottomWidth: 0.5,
  },
});
