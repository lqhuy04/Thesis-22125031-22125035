import NewsItem from "@/components/ui/NewsItem";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { fetchNews, New } from "@/helpers/DetailHelpers";
import {
  getAllNews,
  getBusinessNews,
  getMacroEcomNews,
  getNewsByCategoryId,
} from "@/helpers/MarketHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Animated, View } from "react-native";
import { FlatList } from "react-native-gesture-handler";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const PAGE_SIZE = 20;

type NewsFetchResult = {
  status: boolean;
  data: New[];
};

const sortNewestFirst = (items: New[]) =>
  [...items].sort((first, second) => {
    const firstTime = Date.parse(first.time || "");
    const secondTime = Date.parse(second.time || "");
    const normalizedFirstTime = Number.isNaN(firstTime) ? 0 : firstTime;
    const normalizedSecondTime = Number.isNaN(secondTime) ? 0 : secondTime;

    if (normalizedFirstTime !== normalizedSecondTime) {
      return normalizedSecondTime - normalizedFirstTime;
    }

    return second.id.localeCompare(first.id);
  });

const mergeUniqueArticles = (current: New[], incoming: New[]) => {
  const articlesById = new Map(current.map((article) => [article.id, article]));

  incoming.forEach((article) => {
    articlesById.set(article.id, article);
  });

  return sortNewestFirst(Array.from(articlesById.values()));
};

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
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const nextOffsetRef = useRef(0);
  const isLoadingMoreRef = useRef(false);
  const requestGenerationRef = useRef(0);

  const fetchArticlesPage = useCallback(
    (offset: number): Promise<NewsFetchResult> => {
      if (type === "macro") {
        return getMacroEcomNews(PAGE_SIZE, offset);
      }
      if (type === "business") {
        return getBusinessNews(PAGE_SIZE, offset);
      }
      if (type === "all") {
        return getAllNews(PAGE_SIZE, offset);
      }
      if (typeof category_id === "string" && category_id.length > 0) {
        return getNewsByCategoryId(String(category_id), PAGE_SIZE, offset);
      }

      return fetchNews(symbol, PAGE_SIZE, offset);
    },
    [category_id, symbol, type],
  );

  useEffect(() => {
    const requestGeneration = ++requestGenerationRef.current;
    nextOffsetRef.current = 0;
    isLoadingMoreRef.current = false;
    setArticles([]);
    setHasMore(true);
    setLoadingMore(false);
    setLoading(true);

    const loadInitialPage = async () => {
      const result = await fetchArticlesPage(0);
      if (requestGenerationRef.current !== requestGeneration) {
        return;
      }

      if (result.status) {
        setArticles(sortNewestFirst(result.data));
        nextOffsetRef.current = PAGE_SIZE;
      }

      setHasMore(result.status && result.data.length === PAGE_SIZE);
      setLoading(false);
    };

    loadInitialPage();

    return () => {
      if (requestGenerationRef.current === requestGeneration) {
        requestGenerationRef.current += 1;
      }
    };
  }, [fetchArticlesPage]);

  const loadMoreArticles = useCallback(async () => {
    if (loading || !hasMore || isLoadingMoreRef.current) {
      return;
    }

    const requestGeneration = requestGenerationRef.current;
    const offset = nextOffsetRef.current;
    isLoadingMoreRef.current = true;
    setLoadingMore(true);

    try {
      const result = await fetchArticlesPage(offset);
      if (requestGenerationRef.current !== requestGeneration) {
        return;
      }

      if (result.status) {
        setArticles((current) => mergeUniqueArticles(current, result.data));
        nextOffsetRef.current = offset + PAGE_SIZE;
      }

      setHasMore(result.status && result.data.length === PAGE_SIZE);
    } finally {
      if (requestGenerationRef.current === requestGeneration) {
        isLoadingMoreRef.current = false;
        setLoadingMore(false);
      }
    }
  }, [fetchArticlesPage, hasMore, loading]);

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
            marginBottom: insets.bottom + 12,
            borderRadius: 12,
            paddingHorizontal: 12,
            backgroundColor: theme.background.bg,
            marginTop: 12,
          }}
          data={articles}
          keyExtractor={(item) => item.id}
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
          onEndReached={loadMoreArticles}
          onEndReachedThreshold={0.4}
          ListFooterComponent={loadingMore ? <NewsItemSkeleton /> : null}
        />
      )}
    </View>
  );
};

export default AllNews;
