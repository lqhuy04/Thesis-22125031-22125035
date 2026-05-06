import { New } from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { TouchableOpacity } from "react-native";
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
        backgroundColor: theme.base.primary + "12",
        borderRadius: 12,
        marginBottom: 8,
      }}
      onPress={() => {
        router.push({
          pathname: "/NewDetail",
          params: { data: JSON.stringify(newItem) },
        });
      }}
    >
      <Text
        typography="labelLarge"
        style={{ marginBottom: 4 }}
        numberOfLines={2}
      >
        {newItem.title}
      </Text>
      <Text typography="bodyMedium" numberOfLines={1}>
        {newItem.description}
      </Text>

      <Text
        typography="bodySmall"
        numberOfLines={1}
        color={theme.text.primary + "80"}
      >
        {newItem.source}
        {" • "}
        {newItem.time.slice(0, 10)}
      </Text>
    </TouchableOpacity>
  );
};

export default NewsItem;
