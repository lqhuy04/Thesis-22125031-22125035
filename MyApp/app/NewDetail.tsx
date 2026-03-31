import { Text } from "@/components/ui/Text";
import React from "react";
import { ScrollView, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useTheme } from "@/hooks/ThemeContext";

const NewDetal = () => {
  const { theme } = useTheme();

  const { data } = useLocalSearchParams() || {};
  const item = data ? (JSON.parse(data as string) as New) : null;

  return (
    <SafeAreaView>
      <ScreenHeader title="Chi tiết bài viết" />

      <ScrollView>
        <Text typography="headlineLarge" style={{ marginHorizontal: 12 }}>
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
          <Text typography="bodyLarge">{item?.source} </Text>
          <Text typography="bodyMedium">- {item?.time?.slice(0, 10)}</Text>
        </View>

        <Text typography="titleLarge" style={{ marginHorizontal: 12 }}>
          {item?.description}
        </Text>

        <Text
          typography="bodyLarge"
          style={{ marginVertical: 8, marginHorizontal: 12 }}
        >
          {item?.content ?? ""}
        </Text>

        <Text
          typography="bodyLarge"
          style={{ marginHorizontal: 12, marginTop: 24 }}
        >
          Link:
          <Text
            typography="bodyLarge"
            style={{
              color: theme.base.primary,
              textDecorationLine: "underline",
              textDecorationColor: theme.base.primary,
            }}
          >
            {item?.link}
          </Text>
        </Text>

        <View style={{ height: 48 }} />
      </ScrollView>
    </SafeAreaView>
  );
};

export default NewDetal;
