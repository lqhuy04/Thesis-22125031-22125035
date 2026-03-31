import { New } from "@/helpers/DetailHelpers";
import { getMacroEcomNews } from "@/helpers/MarketHelpers";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import NewsComponent from "../ui/NewsComponent";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";

const MacroEcomNewsSection = () => {
  const { theme } = useTheme();
  const [articles, setArticles] = useState<New[]>([]);

  useEffect(() => {
    getMacroEcomNews().then((result) => {
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
        <Text typography="titleLarge">{"Tin tức kinh tế - vĩ mô"}</Text>
        <Text
          typography="titleLarge"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: "Tin tức kinh tế - vĩ mô",
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

export default MacroEcomNewsSection;
