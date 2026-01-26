import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { fetchNews, New } from "@/helpers/DetailHelpers";
import NewsItem from "../ui/NewsItem";

interface NewsSectionProps {
  stockSymbol: string;
}

const NewsSection = ({ stockSymbol }: NewsSectionProps) => {
  const { t } = useLocalization();

  const [newsItems, setNewsItems] = useState<New[]>([]);

  useEffect(() => {
    fetchNews(stockSymbol).then((data) => {
      setNewsItems(data);
    });
  }, [stockSymbol]);

  return (
    <View>
      <View
        style={{ flexDirection: "row", alignItems: "center", marginTop: 24 }}
      >
        <Text typography="titleLarge" style={{ flex: 1 }}>
          {t("detail.newsSectionTitle")}
        </Text>
      </View>

      {newsItems.slice(0, 3).map((item) => (
        <NewsItem key={item.id} newItem={item} />
      ))}
    </View>
  );
};
export default NewsSection;
