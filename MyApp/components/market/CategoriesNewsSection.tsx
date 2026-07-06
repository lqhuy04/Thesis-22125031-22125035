import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  FlatList,
  Image,
  NativeScrollEvent,
  NativeSyntheticEvent,
  ScrollView,
  TouchableOpacity,
  View,
} from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import { getNewsByCategoryId } from "@/helpers/MarketHelpers";
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

const CategorySkeleton = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const opacity = useShimmer();

  return (
    <View style={{ marginTop: 24, marginHorizontal: 12 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12 }}
      >
        {t("market.newsByIndustry")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          padding: 12,
          borderRadius: 12,
        }}
      >
        {/* Tab pills skeleton */}
        <View style={{ flexDirection: "row", marginBottom: 12, gap: 8 }}>
          {[80, 60, 100].map((width, i) => (
            <Animated.View
              key={i}
              style={{
                height: 28,
                width,
                borderRadius: 16,
                borderWidth: 2,
                borderColor: theme.border.default,
                backgroundColor: theme.border.default,
                opacity,
              }}
            />
          ))}
        </View>

        {/* Featured skeleton */}
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

        {/* News items skeleton */}
        {Array.from({ length: 2 }).map((_, i) => (
          <View key={i}>
            {i !== 0 && (
              <View
                style={{ height: 1, backgroundColor: theme.border.default }}
              />
            )}
            <NewsItemSkeleton opacity={opacity} />
          </View>
        ))}

        <View style={{ height: 1, backgroundColor: theme.border.default }} />
        <Animated.View
          style={{
            height: 16,
            width: 80,
            borderRadius: 4,
            backgroundColor: theme.border.default,
            opacity,
            alignSelf: "center",
            marginTop: 12,
          }}
        />
      </View>
    </View>
  );
};

type CategoryData = {
  category_id: string;
  category_name: string;
  news: New[];
};

const CategoryContent = ({
  data,
  onViewAll,
}: {
  data: CategoryData;
  onViewAll: () => void;
}) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [activeIndex, setActiveIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  const chunks = chunkArray(data.news.slice(1));
  const featured = data.news[0];

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    setActiveIndex(Math.round(offsetX / SNAP_INTERVAL));
  };

  // Reset carousel khi đổi category
  useEffect(() => {
    setActiveIndex(0);
    flatListRef.current?.scrollToOffset({ offset: 0, animated: false });
  }, [data.category_id]);

  if (!featured) return null;

  return (
    <>
      {/* Featured article */}
      <View style={{ marginHorizontal: 0 }}>
        <Image
          source={{ uri: featured.thumbnail }}
          style={{ width: "100%", height: 200, borderRadius: 8 }}
        />
        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ marginTop: 12 }}
        >
          {featured.title}
        </Text>
        <Text
          typography="bodySmall"
          numberOfLines={2}
          color={theme.text.primary + "80"}
          style={{ marginTop: 8, marginBottom: 12 }}
        >
          {featured.source}
          {" • "}
          {featured.time.slice(0, 10)}
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
        style={{ marginHorizontal: -12 }}
        contentContainerStyle={{ paddingHorizontal: 12 }}
        renderItem={({ item: chunk }) => (
          <View style={{ width: ITEM_WIDTH - 12, marginLeft: 12 }}>
            {chunk.map((newsItem: New, i: number) => (
              <View key={newsItem.title}>
                {i !== 0 && (
                  <View
                    style={{ height: 1, backgroundColor: theme.border.default }}
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
          marginTop: 4,
          backgroundColor: theme.border.default,
        }}
      />

      {/* View All */}
      <TouchableOpacity
        style={{ alignSelf: "center", marginTop: 12 }}
        onPress={onViewAll}
      >
        <Text typography="titleMedium" color={theme.base.primary}>
          {t("market.viewAll")}
        </Text>
      </TouchableOpacity>
    </>
  );
};

const CategoriesNewsSection = () => {
  const realEstateId = "8600";
  const bankId = "8300";
  const consumerGoodsId = "3700";

  const { theme } = useTheme();
  const { t } = useLocalization();

  const [chosenIndex, setChosenIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Cache: map category_id → news[]
  const cacheRef = useRef<Record<string, New[]>>({});
  const [categoryArticles, setCategoryArticles] = useState<CategoryData[]>([]);
  // Track loading state riêng cho từng category khi lazy fetch
  const [loadingCategoryId, setLoadingCategoryId] = useState<string | null>(
    null,
  );

  const categories = useMemo(() => {
    return [
      { id: realEstateId, name: t("market.categoryRealEstate") },
      { id: bankId, name: t("market.categoryBank") },
      { id: consumerGoodsId, name: t("market.categoryConsumerGoods") },
    ];
  }, [t]);

  // Fetch tất cả song song lần đầu
  useEffect(() => {
    const fetchAll = async () => {
      const results = await Promise.allSettled(
        categories.map((cat) => getNewsByCategoryId(cat.id, 9)),
      );

      const formatted: CategoryData[] = results.map((res, index) => {
        const news =
          res.status === "fulfilled" && res.value.status ? res.value.data : [];
        // Lưu vào cache
        cacheRef.current[categories[index].id] = news;
        return {
          category_id: categories[index].id,
          category_name: categories[index].name,
          news,
        };
      });

      setCategoryArticles(formatted);
      setIsLoading(false);
    };

    fetchAll();
  }, [categories]);

  const handleSelectCategory = async (index: number) => {
    setChosenIndex(index);

    const categoryId = categories[index].id;

    // Đã có cache → không fetch lại
    if (cacheRef.current[categoryId]?.length > 0) return;

    // Chưa có cache → fetch lazy
    setLoadingCategoryId(categoryId);
    const result = await getNewsByCategoryId(categoryId, 9);
    const news = result.status ? result.data : [];
    cacheRef.current[categoryId] = news;

    setCategoryArticles((prev) =>
      prev.map((cat) =>
        cat.category_id === categoryId ? { ...cat, news } : cat,
      ),
    );
    setLoadingCategoryId(null);
  };

  if (isLoading) return <CategorySkeleton />;
  if (categoryArticles.length === 0) return null;

  const currentCategory = categoryArticles[chosenIndex];
  const isCurrentLoading = loadingCategoryId === currentCategory.category_id;

  return (
    <View style={{ marginTop: 24, marginHorizontal: 12 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12 }}
      >
        {t("market.newsByIndustry")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          padding: 12,
          borderRadius: 12,
        }}
      >
        {/* Category tabs */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{
            marginBottom: 12,
          }}
        >
          {categoryArticles.map((item, index) => (
            <TouchableOpacity
              key={item.category_id}
              onPress={() => handleSelectCategory(index)}
              style={{
                backgroundColor:
                  chosenIndex === index
                    ? theme.base.primary
                    : theme.border.default,
                paddingVertical: 4,
                paddingHorizontal: 12,
                borderRadius: 24,
                marginRight: 8,
              }}
            >
              <Text
                typography="bodyMedium"
                color={
                  chosenIndex === index
                    ? theme.text.onPrimary
                    : theme.text.primary
                }
              >
                {item.category_name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Content hoặc skeleton khi lazy load */}
        {isCurrentLoading ? (
          <CategorySkeleton />
        ) : (
          <CategoryContent
            data={currentCategory}
            onViewAll={() => {
              router.push({
                pathname: "/AllNews",
                params: {
                  data: JSON.stringify({
                    title: currentCategory.category_name,
                    category_id: currentCategory.category_id,
                    type: "category",
                  }),
                },
              });
            }}
          />
        )}
      </View>
    </View>
  );
};

export default CategoriesNewsSection;
