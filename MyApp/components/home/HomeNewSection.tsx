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
      {/* Thumbnail */}
      <Box w={80} h={80} />

      {/* Text lines */}
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

  const realEstateId = "afb4b18d-dc88-4ed0-b17b-28792868b460";
  const bankId = "1fbbad10-a283-47e8-b126-8360ffa225ae";

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

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      let result;
      if (chosenCategory === "business") {
        result = await getBusinessNews(3);
      } else if (chosenCategory === "macro") {
        result = await getMacroEcomNews(3);
      } else if (chosenCategory === "bank") {
        result = await getNewsByCategoryId(bankId, 3);
      } else {
        result = await getNewsByCategoryId(realEstateId, 3);
      }

      if (result?.status) {
        setArticles(result.data);
      }
    } finally {
      setLoading(false);
    }
  }, [chosenCategory]);

  useEffect(() => {
    fetchData();
    const unregister = registerRefresh?.(fetchData);
    return () => unregister?.();
  }, [fetchData, registerRefresh]);

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
        typography="titleMedium"
        color={theme.text.primary}
        style={{ marginBottom: 12 }}
      >
        {t("home.hotToday")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          padding: 12,
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
                    : theme.background.primarySurface,
                paddingVertical: 6,
                paddingHorizontal: 12,
                borderRadius: 16,
                marginRight: 8,
              }}
            >
              <Text
                typography="labelLarge"
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
            <>
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
            </>
          ))
        )}

        <TouchableOpacity onPress={onViewAll} style={{ marginTop: 8 }}>
          <Text
            typography="labelLarge"
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
