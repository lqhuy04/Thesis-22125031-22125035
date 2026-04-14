import { New } from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { View, Image, TouchableOpacity } from "react-native";
import { Text } from "./Text";
import { router } from "expo-router";

interface NewsItemProps {
  newItem: New;
}

const NewsItem = ({ newItem }: NewsItemProps) => {
  const { theme } = useTheme();

  return (
    <TouchableOpacity
      style={{
        padding: 12,
        backgroundColor: theme.base.primary + "08",
        flexDirection: "row",
        alignItems: "center",
      }}
      onPress={() => {
        router.push({
          pathname: "/NewDetail",
          params: { data: JSON.stringify(newItem) },
        });
      }}
    >
      <Image
        source={{ uri: newItem.image_url }}
        style={{
          width: 72,
          height: 72,
          borderRadius: 4,
          marginRight: 8,
        }}
      />
      <View style={{ flex: 1 }}>
        <Text
          typography="titleMedium"
          style={{ marginBottom: 4 }}
          numberOfLines={2}
        >
          {newItem.title}
        </Text>
        <Text typography="bodyMedium" numberOfLines={1}>
          {newItem.description}
        </Text>

        <Text
          typography="bodyMedium"
          numberOfLines={1}
          color={theme.text.primary + "80"}
        >
          {newItem.source}
          {" • "}
          {newItem.time.slice(0, 10)}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

export default NewsItem;
