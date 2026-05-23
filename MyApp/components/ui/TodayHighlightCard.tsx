import { TodayHighlight } from "@/helpers/MarketHelpers";
import React from "react";
import { Dimensions, TouchableOpacity, View, Image } from "react-native";
import { Text } from "./Text";
import { useTheme } from "@/hooks/ThemeContext";
import AntDesign from "@expo/vector-icons/AntDesign";
import { router } from "expo-router";

interface Props {
  item: TodayHighlight;
}

const TodayHighlightCard = ({ item }: Props) => {
  const screenWidth = Dimensions.get("window").width;
  const { theme } = useTheme();

  return (
    <View
      style={{
        backgroundColor: theme.background.bg,
        borderRadius: 12,
        borderColor: theme.border.default,
        borderWidth: 1,
        marginRight: 12,
        width: screenWidth - 120,
      }}
    >
      <TouchableOpacity
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginHorizontal: 12,
          marginVertical: 12,
        }}
        onPress={() => {
          router.push({
            pathname: "/Detail",
            params: { data: item.symbol },
          });
        }}
      >
        <Image
          source={{
            uri:
              item.logo ??
              "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png",
          }}
          style={{ width: 36, height: 36, marginRight: 12, borderRadius: 8 }}
        />
        <View style={{ flex: 1, marginRight: 12 }}>
          <Text typography="titleSmall" color={theme.text.primary}>
            {item.symbol}
          </Text>
          <Text
            typography="bodySmall"
            numberOfLines={1}
            color={theme.text.primary + "88"}
          >
            {item.company_name}
          </Text>
        </View>
        <View style={{ marginRight: 16 }}>
          <Text typography="titleSmall" color={theme.text.primary}>
            {item.CurrentPrice}
          </Text>
          <Text
            color={
              item.PriceChange > 0
                ? theme.base.success
                : item.PriceChange < 0
                  ? theme.base.error
                  : theme.base.warning
            }
            typography="bodySmall"
          >
            {"("}
            {item.PriceChange >= 0 ? "+" : ""}
            {item.PriceChange}
            {")"}
          </Text>
        </View>
        <View
          style={{
            paddingHorizontal: 4,
            paddingVertical: 4,
            backgroundColor:
              item.PriceChange > 0
                ? theme.base.success + "18"
                : item.PriceChange < 0
                  ? theme.base.error + "18"
                  : theme.base.warning + "18",
            flexDirection: "row",
            alignItems: "center",
            borderRadius: 6,
          }}
        >
          <Text
            typography="titleSmall"
            color={
              item.PriceChange > 0
                ? theme.base.success
                : item.PriceChange < 0
                  ? theme.base.error
                  : theme.base.warning
            }
          >
            {item.PerPriceChange > 0
              ? "▲"
              : item.PerPriceChange === 0
                ? ""
                : "▼"}{" "}
            {Math.abs(item.PerPriceChange).toFixed(2)}%
          </Text>
        </View>
      </TouchableOpacity>

      <View
        style={{
          borderLeftWidth: 0.5,
          borderRightWidth: 0.5,
          borderTopWidth: 1,
          borderBottomWidth: 0,
          borderColor: theme.border.default,
          borderRadius: 12,
          paddingHorizontal: 12,
          paddingVertical: 6,
          backgroundColor: theme.background.surface,
          flex: 1,
        }}
      >
        {item.news.map((item, index) => {
          return (
            <TouchableOpacity
              key={index.toString()}
              style={{
                flexDirection: "row",
                alignItems: "center",
                flex: 1,
                justifyContent: "center",
                marginVertical: 6,
              }}
              onPress={() => {
                router.push({
                  pathname: "/NewDetail",
                  params: { data: JSON.stringify(item) },
                });
              }}
            >
              <AntDesign
                name={
                  item?.sentiment === "positive"
                    ? "rise"
                    : item?.sentiment === "negative"
                      ? "fall"
                      : "line"
                }
                size={18}
                color={
                  item?.sentiment === "positive"
                    ? theme.base.success
                    : item?.sentiment === "negative"
                      ? theme.base.error
                      : theme.base.warning
                }
              />
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text
                  numberOfLines={2}
                  color={theme.text.primary}
                  typography="bodyMedium"
                >
                  {item.title}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

export default TodayHighlightCard;
