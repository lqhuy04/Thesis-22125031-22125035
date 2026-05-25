import NewsItem from "@/components/ui/NewsItem";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { fetchNews, New } from "@/helpers/DetailHelpers";
import {
  getAllNews,
  getBusinessNews,
  getMacroEcomNews,
  getNewsByCategoryId,
} from "@/helpers/MarketHelpers";
import { useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import { Animated, View } from "react-native";
import { FlatList } from "react-native-gesture-handler";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTheme } from "@/hooks/ThemeContext";

// --- Skeleton Item ---
const NewsItemSkeleton = () => {
  const { theme } = useTheme();
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: 800,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, [shimmer]);

  const opacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [0.4, 1],
  });

  const bg = theme.text.primary + "20";

  const Box = ({
    w,
    h,
    mt = 0,
  }: {
    w: string | number;
    h: number;
    mt?: number;
  }) => (
    <View
      style={{
        width: w as any,
        height: h,
        marginTop: mt,
        borderRadius: 4,
        backgroundColor: bg,
      }}
    />
  );

  return (
    <Animated.View
      style={{
        opacity,
        flexDirection: "row",
        paddingVertical: 10,
        gap: 10,
        borderBottomWidth: 1,
        borderBottomColor: theme.text.primary + "10",
      }}
    >
      <Box w={80} h={80} />
      <View style={{ flex: 1, justifyContent: "center", gap: 6 }}>
        <Box w="90%" h={13} />
        <Box w="70%" h={13} />
        <Box w="40%" h={11} mt={4} />
      </View>
    </Animated.View>
  );
};

const SKELETON_COUNT = 10;

// --- Main Screen ---
const AllNews = () => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { data } = useLocalSearchParams() || {};

  const {
    title = "",
    category_id = "",
    type = "",
    symbol = "",
  } = data ? (JSON.parse(data as string) as any) : {};

  const [articles, setArticles] = useState<New[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    let promise;
    if (type === "macro") {
      promise = getMacroEcomNews();
    } else if (type === "business") {
      promise = getBusinessNews();
    } else if (type === "all") {
      promise = getAllNews();
    } else if (typeof category_id === "string" && category_id.length > 0) {
      promise = getNewsByCategoryId(String(category_id));
    } else {
      promise = fetchNews(symbol);
    }

    promise.then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
      setLoading(false);
    });
  }, [category_id, symbol, type]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={title} />

      {loading ? (
        <View
          style={{
            marginHorizontal: 12,
            marginTop: 12,
            marginBottom: insets.bottom,
            borderRadius: 12,
            paddingHorizontal: 12,
            backgroundColor: theme.background.bg,
            overflow: "hidden",
          }}
        >
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <NewsItemSkeleton key={i} />
          ))}
        </View>
      ) : (
        <FlatList
          style={{
            marginHorizontal: 12,
            marginBottom: insets.bottom,
            borderRadius: 12,
            paddingHorizontal: 12,
            backgroundColor: theme.background.bg,
            marginTop: 12,
          }}
          data={articles}
          renderItem={({ item, index }) => (
            <View>
              {index !== 0 && (
                <View
                  style={{
                    width: "100%",
                    height: 1,
                    backgroundColor: theme.border.default,
                  }}
                />
              )}
              <NewsItem newItem={item} />
            </View>
          )}
        />
      )}
    </View>
  );
};

export default AllNews;
