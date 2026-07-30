import { Text } from "@/components/ui/Text";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  type DimensionValue,
  Linking,
  ScrollView,
  View,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import {
  ArticleDetail,
  fetchArticleById,
} from "@/helpers/DetailHelpers";
import ScreenHeader from "@/components/ui/ScreenHeader";
import RelatedStockBadges from "@/components/ui/RelatedStockBadges";
import { useTheme } from "@/hooks/ThemeContext";
import { useSafeAreaInsets } from "react-native-safe-area-context";

type SkeletonLineProps = {
  color: string;
  height: number;
  opacity: Animated.Value;
  width: DimensionValue;
};

const SkeletonLine = ({
  color,
  height,
  opacity,
  width,
}: SkeletonLineProps) => (
  <Animated.View
    style={{
      width,
      height,
      borderRadius: 5,
      backgroundColor: color,
      opacity,
    }}
  />
);

const NewDetailSkeleton = () => {
  const { theme } = useTheme();
  const shimmer = useRef(new Animated.Value(0.35)).current;
  const skeletonColor = theme.text.primary + "24";
  const bodyParagraphs: DimensionValue[][] = [
    ["100%", "96%", "92%", "68%"],
    ["98%", "100%", "88%"],
    ["96%", "92%", "100%", "74%"],
    ["100%", "95%", "82%"],
  ];

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 0.85,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0.35,
          duration: 800,
          useNativeDriver: true,
        }),
      ]),
    );

    animation.start();
    return () => animation.stop();
  }, [shimmer]);

  return (
    <ScrollView
      style={{ margin: 12, flex: 1 }}
      scrollEnabled={false}
      showsVerticalScrollIndicator={false}
    >
      <View style={{ gap: 8 }}>
        <SkeletonLine
          color={skeletonColor}
          height={28}
          opacity={shimmer}
          width="96%"
        />
        <SkeletonLine
          color={skeletonColor}
          height={28}
          opacity={shimmer}
          width="92%"
        />
        <SkeletonLine
          color={skeletonColor}
          height={28}
          opacity={shimmer}
          width="72%"
        />
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          gap: 4,
          marginTop: 10,
        }}
      >
        {[62, 72, 66].map((width) => (
          <SkeletonLine
            key={width}
            color={skeletonColor}
            height={30}
            opacity={shimmer}
            width={width + 12}
          />
        ))}
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          gap: 8,
          marginVertical: 12,
        }}
      >
        <SkeletonLine
          color={skeletonColor}
          height={14}
          opacity={shimmer}
          width={82}
        />
        <SkeletonLine
          color={skeletonColor}
          height={14}
          opacity={shimmer}
          width={92}
        />
      </View>

      <View style={{ gap: 7 }}>
        {(["100%", "96%", "88%"] as DimensionValue[]).map((width, index) => (
          <SkeletonLine
            key={index}
            color={skeletonColor}
            height={18}
            opacity={shimmer}
            width={width}
          />
        ))}
      </View>

      <View style={{ marginTop: 18 }}>
        {bodyParagraphs.map((paragraph, paragraphIndex) => (
          <View
            key={paragraphIndex}
            style={{
              gap: 7,
              marginTop: paragraphIndex === 0 ? 0 : 22,
            }}
          >
            {paragraph.map((width, lineIndex) => (
              <SkeletonLine
                key={lineIndex}
                color={skeletonColor}
                height={15}
                opacity={shimmer}
                width={width}
              />
            ))}
          </View>
        ))}
      </View>
    </ScrollView>
  );
};

const getFirstParam = (value?: string | string[]) =>
  Array.isArray(value) ? value[0] : value;

const resolveArticleId = (
  articleIdParam?: string | string[],
  legacyDataParam?: string | string[],
) => {
  const articleId = getFirstParam(articleIdParam);
  if (articleId) {
    return articleId;
  }

  const legacyData = getFirstParam(legacyDataParam);
  if (!legacyData) {
    return "";
  }

  try {
    const parsed = JSON.parse(legacyData);
    return typeof parsed === "string" ? parsed : (parsed?.id ?? "");
  } catch {
    return legacyData;
  }
};

const NewDetail = () => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { articleId: articleIdParam, data: legacyDataParam } =
    useLocalSearchParams<{
      articleId?: string | string[];
      data?: string | string[];
    }>();
  const articleId = resolveArticleId(articleIdParam, legacyDataParam);
  const [item, setItem] = useState<ArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    if (!articleId) {
      setItem(null);
      setLoading(false);
      return () => {
        isActive = false;
      };
    }

    setItem(null);
    setLoading(true);

    fetchArticleById(articleId).then((result) => {
      if (!isActive) {
        return;
      }

      setItem(result.status ? result.data : null);
      setLoading(false);
    });

    return () => {
      isActive = false;
    };
  }, [articleId]);

  const handleOpenLink = async () => {
    const url = item?.link?.trim();

    if (!url) return;

    try {
      await Linking.openURL(url);
    } catch (error) {
      console.error("Failed to open article link:", error);
    }
  };

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: theme.background.surface,
      }}
    >
      <ScreenHeader title="Chi tiết bài viết" />

      {loading ? (
        <NewDetailSkeleton />
      ) : item ? (
        <ScrollView style={{ margin: 12, flex: 1 }}>
          <Text typography="headlineLarge" color={theme.text.primary}>
            {item.title}
          </Text>

          <RelatedStockBadges
            size="large"
            stocks={item.related_stocks}
            style={{ marginTop: 8 }}
          />

          <View
            style={{
              flexDirection: "row",
              alignItems: "flex-end",
              marginVertical: 8,
            }}
          >
            <Text typography="bodyLarge" color={theme.text.primary}>
              {item.source ?? ""}
            </Text>
            <Text typography="bodyMedium" color={theme.text.primary}>
              - {item.time?.slice(0, 10) ?? ""}
            </Text>
          </View>

          <Text typography="titleLarge" color={theme.text.primary}>
            {item.description ?? ""}
          </Text>

          <Text
            typography="bodyLarge"
            color={theme.text.primary}
            style={{ marginVertical: 8 }}
          >
            {item.content ?? ""}
          </Text>

          {item.link ? (
            <Text
              typography="bodyLarge"
              color={theme.text.primary}
              style={{ marginTop: 24 }}
            >
              Link:{" "}
              <Text
                typography="bodyLarge"
                color={theme.text.primary}
                accessibilityRole="link"
                onPress={handleOpenLink}
                style={{
                  color: theme.base.primary,
                  textDecorationLine: "underline",
                  textDecorationColor: theme.base.primary,
                }}
              >
                {item.link}
              </Text>
            </Text>
          ) : null}
          <View style={{ height: insets.bottom + 12 }} />
        </ScrollView>
      ) : (
        <View
          style={{
            flex: 1,
            alignItems: "center",
            justifyContent: "center",
            paddingHorizontal: 24,
          }}
        >
          <Text
            typography="bodyLarge"
            color={theme.text.primary}
          >
            Không thể tải chi tiết bài viết.
          </Text>
        </View>
      )}
    </View>
  );
};

export default NewDetail;
