import { New } from "@/helpers/DetailHelpers";
import { getMacroEcomNews } from "@/helpers/MarketHelpers";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import NewsItem from "../ui/NewsItem";
import { useLocalization } from "@/hooks/LocalizationContext";

const MacroEcomNewsSection = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    getMacroEcomNews(3).then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
    });
  }, []);

  return (
    <View style={{ marginTop: 24, marginHorizontal: 12 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 12,
        }}
      >
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("market.macroNews")}
        </Text>

        <Text
          typography="titleMedium"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: t("market.macroNews"),
                  type: "macro",
                }),
              },
            });
          }}
        >
          {t("market.viewAll")}
        </Text>
      </View>

      <View
        style={{
          backgroundColor: theme.background.bg,
          paddingHorizontal: 12,
          borderRadius: 12,
        }}
      >
        {articles.map((item, index) => {
          return (
            <View key={index.toString()}>
              {index !== 0 ? (
                <View
                  style={{
                    height: 1,
                    width: "100%",
                    backgroundColor: theme.border.default,
                  }}
                />
              ) : null}
              <NewsItem key={index.toString()} newItem={item} />
            </View>
          );
        })}
      </View>
    </View>
  );
};

export default MacroEcomNewsSection;
