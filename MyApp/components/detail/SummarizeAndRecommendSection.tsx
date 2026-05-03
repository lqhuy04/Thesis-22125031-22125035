import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  TouchableOpacity,
  View,
} from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import Entypo from "@expo/vector-icons/Entypo";
import { Switch } from "react-native-gesture-handler";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import AntDesign from "@expo/vector-icons/AntDesign";
import { Ionicons } from "@expo/vector-icons";
import { AnalysisData, getAnalysis } from "@/helpers/AgenticHelpers";

// ─── CustomCheckBox ───────────────────────────────────────────────────────────

const CustomCheckBox = ({
  value,
  onValueChange,
  activeColor,
  inactiveColor,
}: {
  value: boolean;
  onValueChange: (v: boolean) => void;
  activeColor: string;
  inactiveColor: string;
}) => (
  <TouchableOpacity
    onPress={() => onValueChange(!value)}
    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
    style={{
      width: 20,
      height: 20,
      borderRadius: 4,
      borderWidth: 1.5,
      borderColor: value ? activeColor : inactiveColor,
      backgroundColor: value ? activeColor : "transparent",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    {value ? <AntDesign name="check" size={12} color="#fff" /> : null}
  </TouchableOpacity>
);

// ─── ManualConfigModal ────────────────────────────────────────────────────────

const ManualConfigModal = ({
  visible,
  onClose,
  manualOptions,
  theme,
  toggleExpanded,
  toggleSubItem,
  toggleBooleanOption,
}: {
  visible: boolean;
  onClose: () => void;
  manualOptions: any[];
  theme: any;
  toggleExpanded: (key: string) => void;
  toggleSubItem: (parentKey: string, childKey: string, value: boolean) => void;
  toggleBooleanOption: (key: string, value: boolean) => void;
}) => (
  <Modal
    visible={visible}
    animationType="slide"
    transparent
    onRequestClose={onClose}
  >
    <View
      style={{
        flex: 1,
        backgroundColor: "#00000055",
        justifyContent: "flex-end",
      }}
    >
      {/* Backdrop tap to close */}
      <TouchableOpacity
        style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0 }}
        activeOpacity={1}
        onPress={onClose}
      />

      {/* Bottom sheet */}
      <View
        style={{
          backgroundColor: theme.background.bg,
          borderTopLeftRadius: 20,
          borderTopRightRadius: 20,
          maxHeight: "80%",
          overflow: "hidden",
          paddingBottom: 32,
        }}
      >
        {/* Handle bar */}
        <View
          style={{ alignItems: "center", paddingTop: 12, paddingBottom: 4 }}
        >
          <View
            style={{
              width: 40,
              height: 4,
              borderRadius: 2,
              backgroundColor: theme.border.default,
            }}
          />
        </View>

        {/* Header */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            paddingHorizontal: 20,
            paddingVertical: 14,
            borderBottomWidth: 1,
            borderBottomColor: theme.border.default,
          }}
        >
          <View />
          <Text typography="titleLarge" color={theme.text.primary}>
            Chế độ thủ công
          </Text>
          <TouchableOpacity onPress={onClose}>
            <Ionicons name="close" size={22} color={theme.text.primary} />
          </TouchableOpacity>
        </View>

        <ScrollView
          style={{ paddingHorizontal: 20 }}
          showsVerticalScrollIndicator={false}
        >
          <Text
            typography="bodyMedium"
            color={theme.text.primary + "88"}
            style={{ marginTop: 16, marginBottom: 8 }}
          >
            Chọn các thông tin dùng để phân tích
          </Text>

          {manualOptions.map((option, index) => (
            <View key={option.key}>
              {index > 0 && (
                <View
                  style={{
                    height: 1,
                    backgroundColor: theme.border.default,
                    marginVertical: 2,
                  }}
                />
              )}

              {/* Parent row */}
              <View
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  paddingVertical: typeof option.value === "boolean" ? 0 : 12,
                }}
              >
                <Text typography="bodyLarge" color={theme.text.primary}>
                  {option.name}
                </Text>

                {typeof option.value === "boolean" ? (
                  <Switch
                    value={option.value}
                    onValueChange={(value) =>
                      toggleBooleanOption(option.key, value)
                    }
                    thumbColor={theme.base.primary}
                    trackColor={{
                      false: theme.border.default,
                      true: theme.base.primary + "80",
                    }}
                  />
                ) : null}

                {Array.isArray(option.value) ? (
                  <TouchableOpacity
                    onPress={() => toggleExpanded(option.key)}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      gap: 6,
                      backgroundColor: theme.background.surface,
                      paddingHorizontal: 10,
                      paddingVertical: 5,
                      borderRadius: 6,
                      borderWidth: 1,
                      borderColor: theme.border.default,
                    }}
                  >
                    <Text
                      typography="labelMedium"
                      color={theme.text.primary + "88"}
                    >
                      {option.value.filter((c: any) => c.value).length}/
                      {option.value.length}
                    </Text>
                    <SimpleLineIcons
                      name={option.expanded ? "arrow-up" : "arrow-down"}
                      size={10}
                      color={theme.text.primary + "88"}
                    />
                  </TouchableOpacity>
                ) : null}
              </View>

              {/* Sub-items */}
              {Array.isArray(option.value) && option.expanded ? (
                <View
                  style={{
                    backgroundColor: theme.background.surface,
                    borderRadius: 10,
                    marginBottom: 8,
                    paddingHorizontal: 14,
                    borderWidth: 1,
                    borderColor: theme.border.default,
                  }}
                >
                  {option.value.map((child: any, ci: number) => (
                    <View key={child.key}>
                      {ci > 0 && (
                        <View
                          style={{
                            height: 1,
                            backgroundColor: theme.border.default,
                          }}
                        />
                      )}
                      <View
                        style={{
                          flexDirection: "row",
                          alignItems: "center",
                          justifyContent: "space-between",
                          paddingVertical: 11,
                        }}
                      >
                        <Text
                          typography="bodyMedium"
                          color={theme.text.primary}
                          style={{ flex: 1, marginRight: 12 }}
                        >
                          {child.name}
                        </Text>
                        <CustomCheckBox
                          value={child.value}
                          onValueChange={(value) =>
                            toggleSubItem(option.key, child.key, value)
                          }
                          activeColor={theme.base.primary}
                          inactiveColor={theme.border.default}
                        />
                      </View>
                    </View>
                  ))}
                </View>
              ) : null}
            </View>
          ))}
        </ScrollView>

        {/* Apply button */}
        <TouchableOpacity
          onPress={onClose}
          style={{
            marginHorizontal: 20,
            marginTop: 12,
            backgroundColor: theme.base.primary,
            borderRadius: 10,
            paddingVertical: 13,
            alignItems: "center",
          }}
          activeOpacity={0.85}
        >
          <Text typography="titleMedium" color={theme.text.onPrimary}>
            Áp dụng
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  </Modal>
);

// ─── Main Component ───────────────────────────────────────────────────────────

interface Props {
  stockSymbol: string;
}

const SummarizeAndRecommendSection = ({ stockSymbol }: Props) => {
  const { theme } = useTheme();
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [width, setWidth] = useState<number>(0);
  const [manualMode, setManualMode] = useState<boolean>(false);
  const [modalVisible, setModalVisible] = useState<boolean>(false);

  const [manualOptions, setManualOptions] = useState<any[]>([
    {
      key: "articles",
      name: "Tin tức",
      expanded: false,
      value: [
        { key: "stock_articles", name: "Tin tức về cổ phiếu", value: true },
        { key: "industry_articles", name: "Tin tức về ngành", value: true },
        { key: "market_articles", name: "Tin tức thị trường", value: true },
      ],
    },
    { key: "fundamental_analysis", name: "Phân tích cơ bản", value: true },
    {
      key: "fundamental_analysis_indicators",
      name: "Các chỉ số phân tích cơ bản",
      expanded: false,
      value: [
        { key: "eps", name: "EPS", value: true },
        { key: "pe_ratio", name: "P/E", value: true },
        { key: "pb_ratio", name: "P/B", value: true },
        { key: "revenue_yoy", name: "Tăng trưởng doanh thu", value: true },
        { key: "profit_yoy", name: "Tăng trưởng lợi nhuận", value: true },
        { key: "roe", name: "ROE", value: true },
        { key: "roa", name: "ROA", value: true },
        { key: "gross_margin", name: "Biên lợi nhuận gộp", value: true },
        { key: "net_margin", name: "Biên lợi nhuận ròng", value: true },
        { key: "debt_to_equity", name: "Nợ / Vốn chủ sở hữu", value: true },
        {
          key: "current_ratio",
          name: "Tỷ số thanh toán hiện hành",
          value: true,
        },
        { key: "ev_ebitda", name: "EV/EBITDA", value: false },
      ],
    },
    { key: "price", name: "Giá cổ phiếu", value: true },
    {
      key: "technical_indicators",
      name: "Chỉ số kỹ thuật",
      expanded: false,
      value: [
        { key: "MA", name: "MA (Đường trung bình động)", value: true },
        { key: "BOLL", name: "BOLL (Bollinger Bands)", value: true },
        { key: "VOL", name: "VOL (Khối lượng)", value: true },
        { key: "MACD", name: "MACD", value: true },
        { key: "RSI", name: "RSI", value: true },
        { key: "KDJ", name: "KDJ", value: false },
      ],
    },
    { key: "risk_appetite", name: "Khẩu vị rủi ro", value: true },
  ]);

  const getAnalysisData = useCallback(() => {
    setLoading(true);
    getAnalysis(stockSymbol)
      .then((res) => {
        if (res.status) setData(res.data);
      })
      .finally(() => setLoading(false));
  }, [stockSymbol]);

  const toggleExpanded = (key: string) =>
    setManualOptions((prev) =>
      prev.map((o) => (o.key === key ? { ...o, expanded: !o.expanded } : o)),
    );

  const toggleSubItem = (parentKey: string, childKey: string, value: boolean) =>
    setManualOptions((prev) =>
      prev.map((o) => {
        if (o.key === parentKey && Array.isArray(o.value)) {
          return {
            ...o,
            value: o.value.map((child: any) =>
              child.key === childKey ? { ...child, value } : child,
            ),
          };
        }
        return o;
      }),
    );

  const toggleBooleanOption = (key: string, value: boolean) =>
    setManualOptions((prev) =>
      prev.map((o) => (o.key === key ? { ...o, value } : o)),
    );

  return (
    <View style={{ paddingHorizontal: 12, paddingBottom: 16 }}>
      {/* ── Manual mode row ── */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: theme.background.surface,
          borderRadius: 10,
          paddingHorizontal: 8,
          marginVertical: 12,
          borderWidth: 1,
          borderColor: theme.border.default,
        }}
      >
        <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
          <Ionicons
            name="options-outline"
            size={18}
            color={theme.base.primary}
          />
          <Text typography="titleSmall" color={theme.text.primary}>
            Chế độ thủ công
          </Text>
        </View>

        <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
          {manualMode && (
            <TouchableOpacity
              onPress={() => setModalVisible(true)}
              style={{
                flexDirection: "row",
                alignItems: "center",
                gap: 4,
                backgroundColor: theme.background.bg,
                borderWidth: 1,
                borderColor: theme.border.default,
                borderRadius: 6,
                paddingHorizontal: 10,
                paddingVertical: 5,
              }}
            >
              <Ionicons
                name="settings-outline"
                size={14}
                color={theme.text.primary + "94"}
              />
              <Text typography="labelMedium" color={theme.text.primary + "94"}>
                Cấu hình
              </Text>
            </TouchableOpacity>
          )}
          <Switch
            value={manualMode}
            onValueChange={setManualMode}
            thumbColor={theme.base.primary}
            trackColor={{
              false: theme.border.default,
              true: theme.base.primary + "80",
            }}
          />
        </View>
      </View>

      {/* ── Analysis result ── */}
      {loading ? (
        <ActivityIndicator
          size="large"
          color={theme.base.primary}
          style={{ marginVertical: 24 }}
        />
      ) : data != null ? (
        <View
          style={{
            backgroundColor: theme.background.surface,
            borderRadius: 12,
            borderWidth: 1,
            borderColor: theme.border.default,
            padding: 16,
            marginBottom: 12,
            gap: 14,
          }}
        >
          <View>
            <Text
              typography="labelMedium"
              color={theme.text.secondary}
              style={{ marginBottom: 4 }}
            >
              TÓM TẮT
            </Text>
            <Text typography="bodyMedium" color={theme.text.primary}>
              {data?.summary}
            </Text>
          </View>

          <View style={{ height: 1, backgroundColor: theme.border.default }} />

          <View>
            <Text
              typography="labelMedium"
              color={theme.text.secondary}
              style={{ marginBottom: 4 }}
            >
              GỢI Ý
            </Text>
            <Text typography="titleMedium" color={theme.base.primary}>
              {data?.recommendation}
            </Text>
          </View>

          <View style={{ height: 1, backgroundColor: theme.border.default }} />

          <View>
            <Text
              typography="labelMedium"
              color={theme.text.secondary}
              style={{ marginBottom: 4 }}
            >
              LÝ DO
            </Text>
            <Text typography="bodyMedium" color={theme.text.primary}>
              {data?.reasoning}
            </Text>
          </View>

          <View style={{ height: 1, backgroundColor: theme.border.default }} />

          {/* Confidence bar */}
          <View>
            <Text
              typography="labelMedium"
              color={theme.text.secondary}
              style={{ marginBottom: 12 }}
            >
              ĐỘ TIN CẬY
            </Text>
            <View
              style={{ flexDirection: "row", alignItems: "center", gap: 8 }}
            >
              <Text typography="labelSmall" color={theme.text.secondary}>
                0
              </Text>
              <View style={{ flex: 1 }}>
                <View
                  style={{
                    flexDirection: "row",
                    borderRadius: 6,
                    overflow: "hidden",
                    height: 8,
                  }}
                >
                  <View
                    style={{ flex: 0.3, backgroundColor: theme.base.error }}
                  />
                  <View
                    style={{ flex: 0.4, backgroundColor: theme.base.warning }}
                  />
                  <View
                    style={{ flex: 0.3, backgroundColor: theme.base.success }}
                  />
                </View>
                <View
                  style={{ position: "absolute", width: "100%", height: 8 }}
                  onLayout={(e) => setWidth(e.nativeEvent.layout.width)}
                >
                  <View
                    style={{
                      position: "absolute",
                      left: (data?.confidence ?? 0) * width - 12,
                      top: -20,
                      alignItems: "center",
                    }}
                  >
                    <Text typography="labelSmall" color={theme.text.primary}>
                      {Math.round((data?.confidence ?? 0) * 100)}%
                    </Text>
                    <Entypo
                      name="triangle-down"
                      size={20}
                      color={theme.text.primary}
                    />
                  </View>
                </View>
              </View>
              <Text typography="labelSmall" color={theme.text.secondary}>
                100
              </Text>
            </View>
          </View>
        </View>
      ) : null}

      {/* ── Action button ── */}
      <TouchableOpacity
        onPress={getAnalysisData}
        disabled={loading}
        style={{
          backgroundColor: loading
            ? theme.base.primary + "80"
            : theme.base.primary,
          borderRadius: 10,
          paddingVertical: 13,
          alignItems: "center",
        }}
        activeOpacity={0.85}
      >
        <Text typography="titleMedium" color={theme.text.onPrimary}>
          {data != null ? "Phân tích lại" : "Bắt đầu phân tích"}
        </Text>
      </TouchableOpacity>

      {/* ── Manual config modal ── */}
      <ManualConfigModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        manualOptions={manualOptions}
        theme={theme}
        toggleExpanded={toggleExpanded}
        toggleSubItem={toggleSubItem}
        toggleBooleanOption={toggleBooleanOption}
      />
    </View>
  );
};

export default SummarizeAndRecommendSection;
