import { New } from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { View, Image } from "react-native";
import { Text } from "./Text";

interface NewsItemProps {
  newItem: New;
}

const NewsItem = ({ newItem }: NewsItemProps) => {
  const { theme } = useTheme();

  return (
    <View
      style={{
        borderRadius: 4,
        padding: 12,
        backgroundColor: theme.background.surface,
        marginTop: 16,
        flexDirection: "row",
        alignItems: "center",
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
          numberOfLines={1}
        >
          {newItem.title}
        </Text>
        <Text typography="bodyMedium" numberOfLines={2}>
          {newItem.description}
        </Text>
      </View>
    </View>
  );
};

export default NewsItem;
