import { Text } from "@/components/ui/Text";
import React from "react";
import { Image, ScrollView, View } from "react-native";
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
      <ScreenHeader title="Article Detail" />

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
          <Text typography="bodyLarge" style={{ marginRight: 12 }}>
            Stockbiz
          </Text>
          <Text typography="bodyMedium">- {item?.published_at}</Text>
        </View>

        <Text typography="titleLarge" style={{ marginHorizontal: 12 }}>
          {item?.description}
        </Text>

        {item?.content?.blocks.map((data, index) => {
          return data?.type === "text" ? (
            <Text
              key={index.toString()}
              typography="bodyLarge"
              style={{ marginVertical: 8, marginHorizontal: 12 }}
            >
              {data?.content ?? ""}
            </Text>
          ) : data?.type === "image" ? (
            <Image
              key={index.toString()}
              source={{ uri: data?.url }}
              style={{ width: "100%", height: 200, marginVertical: 16 }}
            />
          ) : null;
        })}

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
