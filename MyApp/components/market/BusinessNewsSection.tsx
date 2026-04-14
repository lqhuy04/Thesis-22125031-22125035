import React, { useEffect, useState } from "react";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { New } from "@/helpers/DetailHelpers";
import { View } from "react-native";
import NewsComponent from "../ui/NewsComponent";
import { router } from "expo-router";
import { getBusinessNews } from "@/helpers/MarketHelpers";

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

  return (
    <View style={{ marginTop: 12 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Text typography="titleLarge">{"Doanh nghiệp"}</Text>
        <Text
          typography="titleMedium"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: "Doanh nghiệp",
                }),
              },
            });
          }}
        >
          Xem tất cả
        </Text>
      </View>

      <NewsComponent articles={articles} />
    </View>
  );
};

export default BusinessNewsSection;
