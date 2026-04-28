import React, { useEffect, useState } from "react";
import { Dimensions, FlatList, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { getMarketIndices, MarketIndex } from "@/helpers/MarketHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";

const { width } = Dimensions.get("window");
const CARD_WIDTH = width * 0.72;
const CARD_GAP = 12;

const MarketIndicesSection = () => {
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
    <View>
      <Text typography="titleLarge">Thị trường hôm nay</Text>

      <FlatList
        data={indices}
        keyExtractor={(item) => item.IndexId}
        horizontal
        showsHorizontalScrollIndicator={false}
        snapToInterval={CARD_WIDTH + CARD_GAP}
        snapToAlignment="start"
        decelerationRate="fast"
        contentContainerStyle={{ paddingRight: width - CARD_WIDTH }}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() =>
              router.push({
                pathname: "/IndexDetail" as any,
                params: { data: JSON.stringify(item) },
              })
            }
            style={{
              width: CARD_WIDTH,
              marginRight: CARD_GAP,
              marginTop: 12,
              borderRadius: 8,
              backgroundColor: theme.base.primary + "12",
              borderWidth: 1,
              borderColor: theme.base.primary,
              padding: 12,
              paddingBottom: 6,
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
                    item.Change < 0 ? theme.base.error : theme.base.success
                  }
                >
                  {item.Change}
                </Text>
              </View>
              <Text
                typography="labelLarge"
                color={item.Change < 0 ? theme.base.error : theme.base.success}
                style={{ marginLeft: 8 }}
              >
                {item.RatioChange}%
              </Text>
            </View>

            <Text
              typography="bodySmall"
              color={theme.text.primary + "80"}
              style={{ marginTop: 4 }}
            >
              {(Number(item.TotalVol) / 1000000).toFixed(0)} triệu cổ phiếu -{" "}
              {(Number(item.TotalVal) / 1000000000).toFixed(2)} tỷ đồng
            </Text>

            {(() => {
              const adv = Number(item.Advances) || 0;
              const noChg = Number(item.NoChanges) || 0;
              const dec = Number(item.Declines) || 0;
              const total = adv + noChg + dec;

              const advPct = total === 0 ? 33.33 : (adv / total) * 100;
              const noChgPct = total === 0 ? 33.33 : (noChg / total) * 100;
              const decPct = total === 0 ? 33.34 : (dec / total) * 100;

              return (
                <View
                  style={{
                    flexDirection: "row",
                    height: 4,
                    borderRadius: 2,
                    overflow: "hidden",
                    marginTop: 8,
                    marginBottom: 2,
                  }}
                >
                  <View
                    style={{
                      flex: advPct,
                      backgroundColor: theme.base.success,
                    }}
                  />
                  <View
                    style={{
                      flex: noChgPct,
                      backgroundColor: theme.base.warning,
                    }}
                  />
                  <View
                    style={{ flex: decPct, backgroundColor: theme.base.error }}
                  />
                </View>
              );
            })()}

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
                <View
                  style={{
                    width: 6,
                    height: 2,
                    backgroundColor: theme.base.warning,
                    marginLeft: 8,
                  }}
                />
              </View>

              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Text typography="bodySmall" color={theme.base.error}>
                  {item.Declines} mã
                </Text>
                <MaterialIcons
                  name="arrow-drop-down"
                  size={28}
                  color={theme.base.error}
                />
              </View>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
};

export default MarketIndicesSection;
