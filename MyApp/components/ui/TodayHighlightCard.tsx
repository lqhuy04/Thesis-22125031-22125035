import { TodayHighlight } from "@/helpers/MarketHelpers";
import React from "react";
import { Dimensions, TouchableOpacity, View } from "react-native";
import { Text } from "./Text";
import { useTheme } from "@/hooks/ThemeContext";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
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
        backgroundColor: theme.base.primary + "10",
        borderRadius: 8,
        borderColor: theme.base.primary,
        borderWidth: 1,
        marginRight: 12,
        width: screenWidth - 24,
        padding: 12,
      }}
    >
      <TouchableOpacity
        style={{
          flexDirection: "row",
          alignItems: "center",
          width: screenWidth - 48,
        }}
        onPress={() => {
          router.push({
            pathname: "/Detail",
            params: { data: item.symbol },
          });
        }}
      >
        <View style={{ flex: 1, marginRight: 12 }}>
          <Text typography="titleMedium">{item.symbol}</Text>
          <Text numberOfLines={1} color={theme.text.primary + "88"}>
            {item.company_name}
          </Text>
        </View>
        <View style={{ marginRight: 16 }}>
          <Text typography="titleSmall">{item.CurrentPrice}</Text>
          <Text
            color={
              item.PriceChange >= 0 ? theme.base.success : theme.base.error
            }
          >
            {"("}
            {item.PriceChange >= 0 ? "+" : ""}
            {item.PriceChange}
            {")"}
          </Text>
        </View>
        <View
          style={{
            paddingRight: 4,
            backgroundColor:
              item.PriceChange >= 0
                ? theme.base.success + "18"
                : theme.base.error + "18",
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <MaterialIcons
            name={item.PriceChange >= 0 ? "arrow-drop-up" : "arrow-drop-down"}
            size={28}
            color={
              item.PriceChange >= 0 ? theme.base.success : theme.base.error
            }
          />
          <Text
            typography="titleSmall"
            color={
              item.PriceChange >= 0 ? theme.base.success : theme.base.error
            }
          >
            {item.PerPriceChange}%
          </Text>
        </View>
      </TouchableOpacity>

      <View
        style={{
          backgroundColor: theme.border.default,
          height: 1,
          width: "100%",
          marginTop: 12,
        }}
      />

      <View>
        {item.news.map((item, index) => {
          return (
            <TouchableOpacity
              key={index.toString()}
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginTop: 12,
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
                size={24}
                color={
                  item?.sentiment === "positive"
                    ? theme.base.success
                    : item?.sentiment === "negative"
                      ? theme.base.error
                      : theme.base.warning
                }
              />
              <View style={{ flex: 1, marginLeft: 12 }}>
                <Text numberOfLines={2}>{item.title}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

export default TodayHighlightCard;
