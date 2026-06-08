import { Text } from "@/components/ui/Text";
import React from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const NewDetal = () => {
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const item = data ? (JSON.parse(data as string) as New) : null;

  const insets = useSafeAreaInsets();

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
      }}
    >
      <ScreenHeader title="Chi tiết bài viết" />

      <ScrollView style={{ margin: 12, flex: 1 }}>
        <Text typography="headlineLarge" color={theme.text.primary}>
          {item?.title}
        </Text>

        <View
          style={{
            flexDirection: "row",
            alignItems: "flex-end",
            marginVertical: 8,
            marginHorizontal: 12,
          }}
        >
          <Text typography="bodyLarge" color={theme.text.primary}>
            {item?.source}
          </Text>
          <Text typography="bodyMedium" color={theme.text.primary}>
            - {item?.time?.slice(0, 10)}
          </Text>
        </View>

        <Text
          typography="titleLarge"
          color={theme.text.primary}
          style={{ marginHorizontal: 12 }}
        >
          {item?.description}
        </Text>

        <Text
          typography="bodyLarge"
          color={theme.text.primary}
          style={{ marginVertical: 8, marginHorizontal: 12 }}
        >
          {item?.content ?? ""}
        </Text>

        <Text
          typography="bodyLarge"
          color={theme.text.primary}
          style={{ marginHorizontal: 12, marginTop: 24 }}
        >
          Link:{" "}
          <Text
            typography="bodyLarge"
            color={theme.text.primary}
            style={{
              color: theme.base.primary,
              textDecorationLine: "underline",
              textDecorationColor: theme.base.primary,
            }}
          >
            {item?.link}
          </Text>
        </Text>
        <View style={{ height: insets.bottom + 12 }} />
      </ScrollView>
    </View>
  );
};

export default NewDetal;
