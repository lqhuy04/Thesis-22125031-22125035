import React, { useCallback, useState } from "react";
import { ActivityIndicator, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import Entypo from "@expo/vector-icons/Entypo";
import { Switch } from "react-native-gesture-handler";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import AntDesign from "@expo/vector-icons/AntDesign";
import { AnalysisData, getAnalysis } from "@/helpers/AgenticHelpers";

// Custom cross-platform checkbox — avoids AndroidCheckBox native module error
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
      width: 18,
      height: 18,
      borderRadius: 3,
      borderWidth: 1.5,
      borderColor: value ? activeColor : inactiveColor,
      backgroundColor: value ? activeColor : "transparent",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    {value ? <AntDesign name="check" size={11} color="#fff" /> : null}
  </TouchableOpacity>
);

interface Props {
  stockSymbol: string;
}

const SummarizeAndRecommendSection = ({ stockSymbol }: Props) => {
  const { theme } = useTheme();
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [width, setWidth] = useState<number>(0);

  const [manualMode, setManualMode] = useState<boolean>(false);
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
    {
      key: "fundamental_analysis",
      name: "Phân tích cơ bản",
      value: true,
    },
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
    {
      key: "price",
      name: "Giá cổ phiếu",
      value: true,
    },
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
    {
      key: "risk_appetite",
      name: "Khẩu vị rủi ro",
      value: true,
    },
  ]);

  const getAnalysisData = useCallback(() => {
    setLoading(true);
    getAnalysis(stockSymbol)
      .then((res) => {
        if (res.status) {
          setData(res.data);
        }
      })
      .finally(() => setLoading(false));
  }, [stockSymbol]);

  const toggleExpanded = (key: string) => {
    setManualOptions((prev) =>
      prev.map((o) => (o.key === key ? { ...o, expanded: !o.expanded } : o)),
    );
  };

  const toggleSubItem = (
    parentKey: string,
    childKey: string,
    value: boolean,
  ) => {
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
  };

  const toggleBooleanOption = (key: string, value: boolean) => {
    setManualOptions((prev) =>
      prev.map((o) => (o.key === key ? { ...o, value } : o)),
    );
  };

  return (
    <View>
      {/* Manual mode toggle */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginHorizontal: 12,
        }}
      >
        <Text typography="titleLarge" style={{ marginBottom: 4 }}>
          Chế độ thủ công
        </Text>
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

      {/* Manual options */}
      {manualMode ? (
        <View style={{ marginHorizontal: 12 }}>
          <Text typography="titleMedium" style={{ marginBottom: 4 }}>
            Chọn các thông tin dùng để phân tích
          </Text>

          {manualOptions.map((option, index) => (
            <View key={option.key}>
              {/* Parent row */}
              <View
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginTop: index === 0 ? 12 : 8,
                }}
              >
                <Text typography="bodyLarge">{option.name}</Text>

                {/* Boolean toggle */}
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

                {/* Array — expand/collapse arrow */}
                {Array.isArray(option.value) ? (
                  <TouchableOpacity
                    onPress={() => toggleExpanded(option.key)}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  >
                    <SimpleLineIcons
                      name={option.expanded ? "arrow-up" : "arrow-down"}
                      size={12}
                      color="black"
                      style={{ marginRight: 4 }}
                    />
                  </TouchableOpacity>
                ) : null}
              </View>

              {/* Sub-items (shown when expanded) */}
              {Array.isArray(option.value) && option.expanded
                ? option.value.map((child: any) => (
                    <View
                      key={child.key}
                      style={{
                        flexDirection: "row",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginTop: 6,
                        paddingLeft: 16,
                      }}
                    >
                      <Text typography="bodyMedium" style={{ flex: 1 }}>
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
                  ))
                : null}
            </View>
          ))}
        </View>
      ) : null}

      {/* Analysis result + loading */}
      {loading ? (
        <ActivityIndicator
          size="large"
          color={theme.base.primary}
          style={{ marginVertical: 24 }}
        />
      ) : data != null ? (
        <View style={{ marginVertical: 12, marginHorizontal: 12 }}>
          <Text typography="titleLarge" style={{ marginBottom: 4 }}>
            Tóm tắt
          </Text>
          <Text typography="bodyLarge" style={{ marginBottom: 8 }}>
            {data?.summary}
          </Text>

          <Text typography="titleLarge" style={{ marginBottom: 4 }}>
            Gợi ý
          </Text>
          <Text typography="bodyLarge" style={{ marginBottom: 8 }}>
            {data?.recommendation}
          </Text>

          <Text typography="titleLarge" style={{ marginBottom: 4 }}>
            Lý do
          </Text>
          <Text typography="bodyLarge" style={{ marginBottom: 8 }}>
            {data?.reasoning}
          </Text>

          <Text typography="titleLarge" style={{ marginBottom: 16 }}>
            Độ tin cậy
          </Text>

          <View style={{ flexDirection: "row", alignItems: "center" }}>
            <Text style={{ marginRight: 4 }}>0</Text>
            <View
              style={{ flex: 1, flexDirection: "row", alignItems: "center" }}
            >
              <View
                style={{
                  flex: 0.3,
                  height: 8,
                  backgroundColor: theme.base.error,
                  borderTopLeftRadius: 8,
                  borderBottomLeftRadius: 8,
                }}
              />
              <View
                style={{
                  flex: 0.4,
                  height: 8,
                  backgroundColor: theme.base.warning,
                }}
              />
              <View
                style={{
                  flex: 0.3,
                  height: 8,
                  backgroundColor: theme.base.success,
                  borderTopRightRadius: 8,
                  borderBottomRightRadius: 8,
                }}
              />

              <View
                style={{
                  height: 8,
                  width: "100%",
                  position: "absolute",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                onLayout={(e) => {
                  setWidth(e.nativeEvent.layout.width);
                }}
              >
                <View
                  style={{
                    position: "absolute",
                    left: (data?.confidence ?? 0) * width - 12,
                    bottom: -4,
                  }}
                >
                  <Text style={{ marginBottom: -8 }}>
                    {(data?.confidence ?? 0) * 100}%
                  </Text>
                  <Entypo name="triangle-down" size={24} color="black" />
                </View>
              </View>
            </View>

            <Text style={{ marginLeft: 4 }}>100</Text>
          </View>
        </View>
      ) : null}

      {/* Action button — always visible */}
      <TouchableOpacity
        onPress={getAnalysisData}
        disabled={loading}
        style={{
          marginHorizontal: 12,
          marginTop: 8,
          marginBottom: 16,
          backgroundColor: loading
            ? theme.base.primary + "80"
            : theme.base.primary,
          borderRadius: 8,
          paddingVertical: 12,
          alignItems: "center",
        }}
      >
        <Text typography="titleMedium" style={{ color: "#fff" }}>
          {data != null ? "Phân tích lại" : "Bắt đầu phân tích"}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default SummarizeAndRecommendSection;
