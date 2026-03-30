import React, { useEffect, useState } from "react";
import { useTheme } from "@/hooks/ThemeContext";
import { SafeAreaView } from "react-native-safe-area-context";
import { Text } from "@/components/ui/Text";
import { View } from "react-native";
import { getMarketIndices, MarketIndex } from "@/helpers/MarketHelpers";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";

const Home = () => {
  const { theme } = useTheme();

  const [indices, setIndices] = useState<MarketIndex[]>([]);

  useEffect(() => {
    getMarketIndices().then((result) => {
      if (result.status) {
        setIndices(result.data);
      }
    });
  }, []);

  return (
    <SafeAreaView
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
        paddingTop: 12,
      }}
    >
      <Text typography="titleLarge">Thị trường hôm nay</Text>

      {indices.map((item, index) => {
        return (
          <View
            key={item.IndexId}
            style={{
              marginTop: 12,
              borderRadius: 8,
              backgroundColor: theme.background.surface,
              padding: 12,
            }}
          >
            <Text typography="bodyMedium">{item.IndexName}</Text>

            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginTop: 4,
              }}
            >
              <Text typography="titleLarge">{item.IndexValue}</Text>
              <View
                style={{
                  borderRadius: 4,
                  paddingVertical: 1,
                  paddingHorizontal: 4,
                  backgroundColor:
                    Number(item.Change) > 0
                      ? theme.base.success + "33"
                      : theme.base.error + "33",
                  marginLeft: 8,
                }}
              >
                <Text
                  typography="labelLarge"
                  color={
                    item.Change.startsWith("-")
                      ? theme.base.error
                      : theme.base.success
                  }
                >
                  {(Number(item.Change) * 100).toFixed(2)}
                </Text>
              </View>
              <Text
                typography="labelLarge"
                color={
                  item.Change.startsWith("-")
                    ? theme.base.error
                    : theme.base.success
                }
                style={{
                  marginLeft: 8,
                }}
              >
                {item.RatioChange}%
              </Text>
            </View>

            <Text
              typography="bodySmall"
              color={theme.text.primary + "80"}
              style={{ marginTop: 4 }}
            >
              {item.TotalVol} triệu cổ phiếu -{" "}
              {(Number(item.TotalVal) / 1000000000).toFixed(2)} tỷ đồng
            </Text>

            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Text typography="bodySmall" color={theme.base.success}>
                  {item.Advances} mã
                </Text>
                <MaterialIcons
                  name="arrow-drop-up"
                  size={28}
                  color={theme.base.success}
                />
              </View>

              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Text typography="bodySmall" color={theme.base.warning}>
                  {item.NoChanges} mã
                </Text>
                <MaterialIcons
                  name="arrow-drop-up"
                  size={28}
                  color={theme.base.warning}
                />
              </View>

              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Text typography="bodySmall" color={theme.base.error}>
                  {item.Declines} mã
                </Text>
                <MaterialIcons
                  name="arrow-drop-up"
                  size={28}
                  color={theme.base.error}
                />
              </View>
            </View>
          </View>
        );
      })}
    </SafeAreaView>
  );
};

export default Home;
