import { AnalysisData, getAnalysis } from "@/helpers/DetailHelpers";
import React, { use, useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import Entypo from "@expo/vector-icons/Entypo";

interface Props {
  stockSymbol: string;
}

const SummarizeAndRecommendSection = ({ stockSymbol }: Props) => {
  const { theme } = useTheme();
  const [data, setData] = useState<AnalysisData | null>(null);

  const [width, setWidth] = useState<number>(0);

  useEffect(() => {
    getAnalysis(stockSymbol).then((res) => {
      if (res.status) {
        setData(res.data);
      }
    });
  }, [stockSymbol]);

  return data != null ? (
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
        <View style={{ flex: 1, flexDirection: "row", alignItems: "center" }}>
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
  ) : null;
};

export default SummarizeAndRecommendSection;
