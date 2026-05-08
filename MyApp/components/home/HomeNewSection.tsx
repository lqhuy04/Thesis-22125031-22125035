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
  const { theme } = useTheme();
  const [articles, setArticles] = useState<New[]>([]);
  const [loading, setLoading] = useState(true);

  const realEstateId = "afb4b18d-dc88-4ed0-b17b-28792868b460";
  const bankId = "1fbbad10-a283-47e8-b126-8360ffa225ae";

  const categories = useMemo(
    () => [
      { id: "business", name: "Doanh nghiệp" },
      { id: "macro", name: "Kinh tế - Vĩ mô" },
      { id: "bank", name: "Ngân hàng" },
      { id: "real-estate", name: "Bất động sản" },
    ],
    [],
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
        ? { data: JSON.stringify({ title: "Doanh nghiệp", type: "business" }) }
        : chosenCategory === "macro"
          ? {
              data: JSON.stringify({
                title: "Tin tức kinh tế - vĩ mô",
                type: "macro",
              }),
            }
          : chosenCategory === "bank"
            ? {
                data: JSON.stringify({
                  title: "Ngân hàng",
                  category_id: bankId,
                  type: "category",
                }),
              }
            : {
                data: JSON.stringify({
                  title: "Bất động sản",
                  category_id: realEstateId,
                  type: "category",
                }),
              };

    router.push({ pathname: "/AllNews", params });
  }, [chosenCategory]);

  return (
    <View style={{ marginHorizontal: 12, marginTop: 24 }}>
      <Text typography="titleMedium" style={{ marginBottom: 8 }}>
        Hôm nay có gì hot?
      </Text>

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
                  ? theme.base.primary + "12"
                  : theme.text.secondary + "80",
              borderWidth: 2,
              borderColor:
                chosenCategory === item.id
                  ? theme.base.primary + "80"
                  : theme.text.secondary + "80",
              paddingVertical: 4,
              paddingHorizontal: 8,
              borderRadius: 16,
              marginRight: 8,
              marginBottom: 8,
            }}
          >
            <Text
              typography="labelMedium"
              color={
                chosenCategory === item.id
                  ? theme.base.primary
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
          <NewsItem key={index.toString()} newItem={item} />
        ))
      )}

      <TouchableOpacity onPress={onViewAll} style={{ marginTop: 12 }}>
        <Text
          typography="labelLarge"
          color={theme.base.primary}
          style={{ alignSelf: "center" }}
        >
          Xem tất cả
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default HomeNewSection;
