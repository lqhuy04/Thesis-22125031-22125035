import React, { useEffect, useRef, useState } from "react";
import { Animated, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { router } from "expo-router";
import { New } from "@/helpers/DetailHelpers";
import { getAllNews } from "@/helpers/MarketHelpers";
import NewsItem from "../ui/NewsItem";
import { useLocalization } from "@/hooks/LocalizationContext";

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
    <View style={{ paddingVertical: 12 }}>
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

const AllNewsSkeleton = () => {
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
        {t("market.marketOverview")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          paddingHorizontal: 12,
          borderRadius: 12,
        }}
      >
        {Array.from({ length: 10 }).map((_, i) => (
          <View key={i}>
            <NewsItemSkeleton opacity={opacity} />
            <View
              style={{ height: 1, backgroundColor: theme.border.default }}
            />
          </View>
        ))}

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

const AllNewsSection = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [articles, setArticles] = useState<New[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getAllNews(10).then((result) => {
      if (result.status) {
        setArticles(result.data);
      }
      setIsLoading(false);
    });
  }, []);

  if (isLoading) return <AllNewsSkeleton />;
  if (articles.length === 0) return null;

  return (
    <View style={{ marginTop: 24, marginHorizontal: 12 }}>
      <Text
        typography="titleLarge"
        color={theme.text.primary}
        style={{ marginBottom: 12 }}
      >
        {t("market.marketOverview")}
      </Text>

      <View
        style={{
          backgroundColor: theme.background.bg,
          paddingHorizontal: 12,
          borderRadius: 12,
        }}
      >
        {articles.map((item, index) => (
          <View key={index.toString()}>
            <NewsItem newItem={item} />
            <View
              style={{
                height: 1,
                width: "100%",
                backgroundColor: theme.border.default,
              }}
            />
          </View>
        ))}

        <TouchableOpacity
          style={{ alignSelf: "center", marginVertical: 12 }}
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: t("market.marketOverview"),
                  type: "all",
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

export default AllNewsSection;
