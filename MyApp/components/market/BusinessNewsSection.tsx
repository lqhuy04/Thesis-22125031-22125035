import React, { useEffect, useState } from "react";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { New } from "@/helpers/DetailHelpers";
import { View } from "react-native";
import { router } from "expo-router";
import { getBusinessNews } from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";
import { useLocalization } from "@/hooks/LocalizationContext";

const BusinessNewsSection = () => {
  const { theme } = useTheme();
  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    getBusinessNews(3).then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
    });
  }, []);

  const { t } = useLocalization();

  return (
    <View style={{ marginHorizontal: 12, marginTop: 24 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 12,
        }}
      >
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("market.business")}
        </Text>
        <Text
          typography="titleMedium"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: t("market.business"),
                  type: "business",
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

export default BusinessNewsSection;
