import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { fetchNews, New } from "@/helpers/DetailHelpers";
import NewsItem from "../ui/NewsItem";
import SeeAllBtn from "@/components/ui/SeeAllBtn";


interface NewsSectionProps {
  stockSymbol: string;
}

const NewsSection = ({ stockSymbol }: NewsSectionProps) => {
  const { t } = useLocalization();

  const [newsItems, setNewsItems] = useState<New[]>([]);

  useEffect(() => {
    fetchNews(stockSymbol).then((data) => {
      if (data.status) {
        setNewsItems(data.data);
      }
    });
  }, [stockSymbol]);

  return (
    <View>
       <Text typography="titleLarge" style={{marginTop: 24}}>
          {t("detail.newsSectionTitle")}
        </Text>

      {newsItems.slice(0, 3).map((item) => (
        <NewsItem key={item.id} newItem={item} />
      ))}

      <SeeAllBtn />
    </View>
  );
};
export default NewsSection;
