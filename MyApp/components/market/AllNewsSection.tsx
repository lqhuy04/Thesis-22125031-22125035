import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import { getAllNews } from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";
import { useLocalization } from "@/hooks/LocalizationContext";

const AllNewsSection = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    getAllNews(10).then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
    });
  }, []);

  return (
    <View style={{ marginTop: 16, marginHorizontal: 12 }}>
      <View style={{ marginBottom: 12 }}>
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Text typography="titleMedium" color={theme.text.primary}>
            {t("market.marketOverview")}
          </Text>
          <Text
            typography="titleMedium"
            color={theme.base.primary}
            onPress={() => {
              router.push({
                pathname: "/AllNews",
                params: {
                  data: JSON.stringify({
                    title: t("market.marketOverview"),
                    type: "all",
                  }),
                },
              });
            }}
          >
            {t("market.viewAll")}
          </Text>
        </View>
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

export default AllNewsSection;
