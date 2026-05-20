import { New } from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { Image, TouchableOpacity, View } from "react-native";
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
        marginVertical: 12,
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
        source={{ uri: newItem.thumbnail }}
        style={{ width: 64, height: 64, borderRadius: 8, marginRight: 12 }}
      />

      <View style={{ flex: 1 }}>
        <Text
          typography="labelLarge"
          style={{ marginBottom: 4 }}
          numberOfLines={2}
          color={theme.text.primary}
        >
          {newItem.title}
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
      </View>
    </TouchableOpacity>
  );
};

export default NewsItem;
