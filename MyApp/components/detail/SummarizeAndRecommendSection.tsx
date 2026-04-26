import { AnalysisData, getAnalysis } from "@/helpers/DetailHelpers";
import React, { useEffect, useState } from "react";
import { TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import Entypo from "@expo/vector-icons/Entypo";
import { Switch } from "react-native-gesture-handler";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import CheckBox from "@react-native-community/checkbox";

interface Props {
  stockSymbol: string;
}

const SummarizeAndRecommendSection = ({ stockSymbol }: Props) => {
  const { theme } = useTheme();
  const [data, setData] = useState<AnalysisData | null>(null);

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
      value: [],
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
      value: [],
    },
    {
      key: "risk_appetite",
      name: "Khẩu vị rủi ro",
      value: true,
    },
  ]);

  // useEffect(() => {
  //   getAnalysis(stockSymbol).then((res) => {
  //     if (res.status) {
  //       setData(res.data);
  //     }
  //   });
  // }, [stockSymbol]);

  return (
    <View>
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

      {manualMode ? (
        <View style={{ marginHorizontal: 12 }}>
          <Text typography="titleMedium" style={{ marginBottom: 4 }}>
            Chọn các thông tin dùng để phân tích
          </Text>

          {manualOptions.map((option, index) => (
            <View
              key={option.key}
              style={{
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
                marginTop: index === 0 ? 12 : 0,
              }}
            >
              <Text typography="bodyLarge">{option.name}</Text>
              {typeof option.value === "boolean" ? (
                <Switch
                  value={option.value}
                  onValueChange={(value) => {
                    const newOptions = [...manualOptions];
                    const index = newOptions.findIndex(
                      (o) => o.key === option.key,
                    );
                    if (index !== -1) {
                      newOptions[index].value = value;
                      setManualOptions(newOptions);
                    }
                  }}
                  thumbColor={theme.base.primary}
                  trackColor={{
                    false: theme.border.default,
                    true: theme.base.primary + "80",
                  }}
                />
              ) : null}

              {typeof option.value === "object" ? (
                <TouchableOpacity
                  onPress={() => {
                    setManualMode();
                  }}
                >
                  <SimpleLineIcons
                    name="arrow-down"
                    size={12}
                    color="black"
                    style={{ marginRight: 12 }}
                  />
                </TouchableOpacity>
              ) : null}
            </View>
          ))}
        </View>
      ) : null}

      {data != null ? (
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
    </View>
  );
};

export default SummarizeAndRecommendSection;
