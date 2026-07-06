import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Animated, FlatList, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { New } from "@/helpers/DetailHelpers";
import {
  getBusinessNews,
  getMacroEcomNews,
  getNewsByCategoryId,
} from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";
import { router } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

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
        backgroundColor: theme.text.primary + "20",
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

const HomeNewSection = ({ registerRefresh }: Props) => {
  const { t } = useLocalization();
  const { theme } = useTheme();
  const [articles, setArticles] = useState<New[]>([]);
  const [loading, setLoading] = useState(true);

  const cache = useRef<Record<string, New[]>>({});
  const abortRef = useRef<AbortController | null>(null);

  const realEstateId = "8600";
  const bankId = "8300";

  const categories = useMemo(
    () => [
      { id: "business", name: t("home.categoryBusiness") },
      { id: "macro", name: t("home.categoryMacro") },
      { id: "bank", name: t("home.categoryBank") },
      { id: "real-estate", name: t("home.categoryRealEstate") },
    ],
    [t],
  );

  const [chosenCategory, setChosenCategory] = useState<string>(
    categories[0].id,
  );

  const fetchData = useCallback(
    async (forceRefresh = false) => {
      const key = chosenCategory;

      // Cache hit — chỉ skip nếu không phải force refresh
      if (!forceRefresh && cache.current[key]) {
        setArticles(cache.current[key]);
        setLoading(false);
        return;
      }

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);

      try {
        let result;
        if (key === "business") {
          result = await getBusinessNews(3);
        } else if (key === "macro") {
          result = await getMacroEcomNews(3);
        } else if (key === "bank") {
          result = await getNewsByCategoryId(bankId, 3);
        } else {
          result = await getNewsByCategoryId(realEstateId, 3);
        }

        if (controller.signal.aborted) return;

        if (result?.status) {
          cache.current[key] = result.data;
          setArticles(result.data);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    },
    [chosenCategory],
  );

  // Đổi category — dùng cache nếu có
  useEffect(() => {
    fetchData(false);
    return () => {
      abortRef.current?.abort();
    };
  }, [fetchData]);

  // Pull-to-refresh — luôn fetch mới và invalidate cache
  useEffect(() => {
    const refreshFn = async () => {
      delete cache.current[chosenCategory];
      await fetchData(true);
    };
    const unregister = registerRefresh?.(refreshFn);
    return () => unregister?.();
  }, [registerRefresh, fetchData, chosenCategory]);

  const onViewAll = useCallback(() => {
    const params =
      chosenCategory === "business"
        ? {
            data: JSON.stringify({
              title: t("home.newsTitleBusiness"),
              type: "business",
            }),
          }
        : chosenCategory === "macro"
          ? {
              data: JSON.stringify({
                title: t("home.newsTitleMacro"),
                type: "macro",
              }),
            }
          : chosenCategory === "bank"
            ? {
                data: JSON.stringify({
                  title: t("home.newsTitleBank"),
                  category_id: bankId,
                  type: "category",
                }),
              }
            : {
                data: JSON.stringify({
                  title: t("home.newsTitleRealEstate"),
                  category_id: realEstateId,
                  type: "category",
                }),
              };

    router.push({ pathname: "/AllNews", params });
  }, [chosenCategory, t]);

  return (
    <View style={{ marginHorizontal: 12, marginTop: 24 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12 }}
      >
        {t("home.hotToday")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          paddingLeft: 12,
          paddingVertical: 12,
          borderRadius: 12,
        }}
      >
        {/* Category chips */}
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={categories}
          style={{ marginBottom: 8 }}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => setChosenCategory(item.id)}
              style={{
                backgroundColor:
                  chosenCategory === item.id
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
                  chosenCategory === item.id
                    ? theme.text.onPrimary
                    : theme.text.primary
                }
              >
                {item.name}
              </Text>
            </TouchableOpacity>
          )}
        />

        {/* News list hoặc skeleton */}
        {loading ? (
          <>
            <NewsItemSkeleton />
            <NewsItemSkeleton />
            <NewsItemSkeleton />
          </>
        ) : (
          articles.map((item, index) => (
            <View key={index.toString()}>
              {index !== 0 ? (
                <View
                  style={{
                    height: 1,
                    width: "100%",
                    backgroundColor: theme.border.default,
                  }}
                />
              ) : null}
              <NewsItem key={index.toString()} newItem={item} />
            </View>
          ))
        )}

        <TouchableOpacity onPress={onViewAll} style={{ marginTop: 8 }}>
          <Text
            typography="titleMedium"
            color={theme.base.primary}
            style={{ alignSelf: "center" }}
          >
            {t("home.viewAll")}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default HomeNewSection;
