import { New } from "@/helpers/DetailHelpers";
import { getMacroEcomNews } from "@/helpers/MarketHelpers";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Animated,
  Dimensions,
  FlatList,
  Image,
  NativeScrollEvent,
  NativeSyntheticEvent,
  TouchableOpacity,
  View,
} from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import NewsItem from "../ui/NewsItem";
import { useLocalization } from "@/hooks/LocalizationContext";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const ITEM_WIDTH = SCREEN_WIDTH - 48;
const SNAP_INTERVAL = ITEM_WIDTH;

function chunkArray<T>(arr: T[], size: number = 2): T[][] {
  const result: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    result.push(arr.slice(i, i + size));
  }
  return result;
}

const useShimmer = () => {
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0,
          duration: 900,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, [shimmerAnim]);

  return shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.4, 0.85],
  });
};

const NewsItemSkeleton = ({
  opacity,
}: {
  opacity: Animated.AnimatedInterpolation<number>;
}) => {
  const { theme } = useTheme();

  return (
    <View style={{ paddingHorizontal: 12, paddingVertical: 12 }}>
      <View style={{ flexDirection: "row", gap: 12 }}>
        <Animated.View
          style={{
            width: 80,
            height: 80,
            borderRadius: 8,
            backgroundColor: theme.border.default,
            opacity,
          }}
        />
        <View style={{ flex: 1, gap: 8, justifyContent: "center" }}>
          <Animated.View
            style={{
              height: 14,
              borderRadius: 4,
              backgroundColor: theme.border.default,
              opacity,
              width: "90%",
            }}
          />
          <Animated.View
            style={{
              height: 14,
              borderRadius: 4,
              backgroundColor: theme.border.default,
              opacity,
              width: "70%",
            }}
          />
          <Animated.View
            style={{
              height: 11,
              borderRadius: 4,
              backgroundColor: theme.border.default,
              opacity,
              width: "45%",
            }}
          />
        </View>
      </View>
    </View>
  );
};

const MacroEcomNewsSkeleton = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const opacity = useShimmer();

  return (
    <View style={{ marginHorizontal: 12, marginTop: 24 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12 }}
      >
        {t("market.macroNews")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          paddingTop: 12,
        }}
      >
        {/* Featured skeleton */}
        <View style={{ marginHorizontal: 12 }}>
          <Animated.View
            style={{
              width: "100%",
              height: 200,
              borderRadius: 8,
              backgroundColor: theme.border.default,
              opacity,
            }}
          />
          <Animated.View
            style={{
              height: 16,
              borderRadius: 4,
              backgroundColor: theme.border.default,
              opacity,
              marginTop: 12,
              width: "85%",
            }}
          />
          <Animated.View
            style={{
              height: 16,
              borderRadius: 4,
              backgroundColor: theme.border.default,
              opacity,
              marginTop: 8,
              width: "60%",
            }}
          />
          <Animated.View
            style={{
              height: 11,
              borderRadius: 4,
              backgroundColor: theme.border.default,
              opacity,
              marginTop: 8,
              marginBottom: 12,
              width: "40%",
            }}
          />
          <View style={{ height: 1, backgroundColor: theme.border.default }} />
        </View>

        {/* News list skeleton */}
        {Array.from({ length: 2 }).map((_, i) => (
          <View key={i}>
            {i !== 0 && (
              <View
                style={{
                  height: 1,
                  marginHorizontal: 12,
                  backgroundColor: theme.border.default,
                }}
              />
            )}
            <NewsItemSkeleton opacity={opacity} />
          </View>
        ))}

        <View
          style={{
            height: 1,
            marginHorizontal: 12,
            backgroundColor: theme.border.default,
          }}
        />

        <Animated.View
          style={{
            height: 16,
            width: 80,
            borderRadius: 4,
            backgroundColor: theme.border.default,
            opacity,
            alignSelf: "center",
            marginVertical: 16,
          }}
        />
      </View>
    </View>
  );
};

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

const MacroEcomNewsSection = ({ registerRefresh }: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const [articles, setArticles] = useState<New[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await getMacroEcomNews(9);
      if (result.status) {
        setArticles(result.data);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Pull-to-refresh
  useEffect(() => {
    const unregister = registerRefresh?.(fetchData);
    return () => unregister?.();
  }, [registerRefresh, fetchData]);

  const chunks = useMemo(() => chunkArray(articles.slice(1)), [articles]);

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    const index = Math.round(offsetX / SNAP_INTERVAL);
    setActiveIndex(index);
  };

  if (isLoading) return <MacroEcomNewsSkeleton />;
  if (articles.length === 0) return null;

  return (
    <View style={{ marginHorizontal: 12, marginTop: 24 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12 }}
      >
        {t("market.macroNews")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          borderRadius: 12,
          paddingTop: 12,
        }}
      >
        {/* Featured article */}
        <View style={{ marginHorizontal: 12 }}>
          <Image
            source={{ uri: articles[0].thumbnail }}
            style={{ width: "100%", height: 200, borderRadius: 8 }}
          />
          <Text
            typography="titleMedium"
            color={theme.text.primary}
            style={{ marginTop: 12 }}
          >
            {articles[0].title}
          </Text>
          <Text
            typography="bodySmall"
            numberOfLines={2}
            color={theme.text.primary + "80"}
            style={{ marginTop: 8, marginBottom: 12 }}
          >
            {articles[0].source}
            {" • "}
            {articles[0].time.slice(0, 10)}
          </Text>
          <View style={{ height: 1, backgroundColor: theme.border.default }} />
        </View>

        {/* Carousel */}
        <FlatList
          ref={flatListRef}
          horizontal
          data={chunks}
          keyExtractor={(_, index) => index.toString()}
          showsHorizontalScrollIndicator={false}
          snapToInterval={SNAP_INTERVAL}
          snapToAlignment="start"
          decelerationRate="fast"
          onScroll={onScroll}
          scrollEventThrottle={16}
          renderItem={({ item: chunk }) => (
            <View style={{ width: ITEM_WIDTH - 12, marginLeft: 12 }}>
              {chunk.map((newsItem: New, i: number) => (
                <View key={newsItem.title}>
                  {i !== 0 && (
                    <View
                      style={{
                        height: 1,
                        backgroundColor: theme.border.default,
                      }}
                    />
                  )}
                  <NewsItem newItem={newsItem} />
                </View>
              ))}
            </View>
          )}
        />

        {/* Pagination dots */}
        {chunks.length > 1 && (
          <View
            style={{
              flexDirection: "row",
              justifyContent: "center",
              alignItems: "center",
              marginTop: 4,
              marginBottom: 8,
              gap: 6,
            }}
          >
            {chunks.map((_, index) => (
              <View
                key={index}
                style={{
                  width: activeIndex === index ? 16 : 6,
                  height: 6,
                  borderRadius: 3,
                  backgroundColor:
                    activeIndex === index
                      ? theme.base.primary
                      : theme.base.primary + "40",
                }}
              />
            ))}
          </View>
        )}

        <View
          style={{
            height: 1,
            marginHorizontal: 12,
            marginTop: 4,
            backgroundColor: theme.border.default,
          }}
        />

        {/* View All */}
        <TouchableOpacity
          style={{ alignSelf: "center", marginVertical: 12 }}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: t("market.macroNews"),
                  type: "macro",
                }),
              },
            });
          }}
        >
          <Text typography="titleMedium" color={theme.base.primary}>
            {t("market.viewAll")}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default MacroEcomNewsSection;
