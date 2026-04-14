import { New } from "@/helpers/DetailHelpers";
import React from "react";
import { View, Image, Dimensions, TouchableOpacity } from "react-native";
import { Text } from "./Text";
import { useTheme } from "@/hooks/ThemeContext";
import NewsItem from "./NewsItem";
import { router } from "expo-router";

interface Props {
  articles: New[];
}

const NewsComponent = ({ articles }: Props) => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;

  return articles.length > 0 ? (
    <View>
      <TouchableOpacity
        style={{
          padding: 12,
          backgroundColor: theme.base.primary + "08",
          marginTop: 12,
        }}
        onPress={() => {
          router.push({
            pathname: "/NewDetail",
            params: { data: JSON.stringify(articles[0]) },
          });
        }}
      >
        <Image
          source={{ uri: articles[0].image_url }}
          style={{
            width: screenWidth - 48,
            height: (screenWidth - 48) * 0.6,
            borderRadius: 4,
            marginBottom: 8,
          }}
        />
        <Text
          typography="titleLarge"
          style={{ marginVertical: 4 }}
          numberOfLines={2}
          color={theme.text.primary}
        >
          {articles[0].title}
        </Text>
        <Text typography="bodyLarge" numberOfLines={1}>
          {articles[0].description}
        </Text>

        <Text
          typography="bodyMedium"
          numberOfLines={2}
          color={theme.text.primary + "80"}
          style={{ marginTop: 2 }}
        >
          {articles[0].source}
          {" • "}
          {articles[0].time.slice(0, 10)}
        </Text>
      </TouchableOpacity>
      {articles.slice(1, 3).map((item, index) => {
        return <NewsItem key={index.toString()} newItem={item} />;
      })}
    </View>
  ) : null;
};

export default NewsComponent;
