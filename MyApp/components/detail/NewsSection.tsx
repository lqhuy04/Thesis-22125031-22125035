import React, { useCallback, useEffect, useRef, useState } from "react";
import { Animated, StyleSheet, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { fetchNews, New } from "@/helpers/DetailHelpers";
import NewsItem from "../ui/NewsItem";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { router } from "expo-router";

// ─── Skeleton ──────────────────────────────────────────────────────────────────

const usePulse = () => {
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, {
          toValue: 1,
          duration: 800,
          useNativeDriver: false,
        }),
        Animated.timing(anim, {
          toValue: 0,
          duration: 800,
          useNativeDriver: false,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [anim]);

  return anim;
};

const NewsSkeleton = ({
  base,
  highlight,
  divider,
  cardBg,
}: {
  base: string;
  highlight: string;
  divider: string;
  cardBg: string;
}) => {
  const anim = usePulse();

  const bg = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [base, highlight],
  });

  const Box = ({
    width,
    height,
    style,
  }: {
    width: number | `${number}%`;
    height: number;
    style?: object;
  }) => (
    <Animated.View
      style={[{ width, height, borderRadius: 6, backgroundColor: bg }, style]}
    />
  );

  return (
    <View>
      {/* Header row */}
      <View style={[styles.header, { marginTop: 12, marginHorizontal: 12 }]}>
        <Box width="55%" height={18} />
        <Box width="20%" height={14} />
      </View>

      {/* News card */}
      <View
        style={[
          styles.card,
          { backgroundColor: cardBg, marginHorizontal: 12, marginTop: 12 },
        ]}
      >
        {Array.from({ length: 3 }).map((_, i) => (
          <React.Fragment key={i}>
            {/* Thumbnail + text block */}
            <View style={styles.newsRow}>
              <Box width={64} height={64} style={{ borderRadius: 8 }} />
              <View style={styles.newsText}>
                <Box width="100%" height={13} />
                <Box width="80%" height={13} style={{ marginTop: 6 }} />
                <Box width="40%" height={11} style={{ marginTop: 8 }} />
              </View>
            </View>
            {i < 3 && (
              <View style={[styles.divider, { backgroundColor: divider }]} />
            )}
          </React.Fragment>
        ))}
      </View>
    </View>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────────

const NewsSection = ({
  stockSymbol,
  registerRefresh,
}: {
  stockSymbol: string;
  registerRefresh?: (fn: () => Promise<void>) => () => void;
}) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [newsItems, setNewsItems] = useState<New[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setNewsItems([]);
    try {
      const data = await fetchNews(stockSymbol, 3);
      if (data.status) setNewsItems(data.data);
    } finally {
      setIsLoading(false);
    }
  }, [stockSymbol]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Pull-to-refresh
  useEffect(() => {
    const unregister = registerRefresh?.(fetchData);
    return () => unregister?.();
  }, [registerRefresh, fetchData]);

  if (isLoading) {
    return (
      <NewsSkeleton
        base={theme.border.default}
        highlight={theme.background.bg}
        divider={theme.border.default}
        cardBg={theme.background.bg}
      />
    );
  }

  return (
    <View>
      <View style={[styles.header, { marginTop: 12, marginHorizontal: 12 }]}>
        <Text typography="titleLarge" color={theme.text.primary}>
          {t("detail.newsSectionHotTitle").replace("{symbol}", stockSymbol)}
        </Text>
        <TouchableOpacity
          onPress={() => {
            router.push({
              pathname: "/AllNews",
              params: {
                data: JSON.stringify({
                  title: stockSymbol,
                  symbol: stockSymbol,
                }),
              },
            });
          }}
        >
          <Text typography="titleMedium" color={theme.base.primary}>
            {t("detail.newsSectionViewAll")}
          </Text>
        </TouchableOpacity>
      </View>
      <View
        style={[
          styles.card,
          {
            backgroundColor: theme.background.bg,
            marginHorizontal: 12,
            marginTop: 12,
          },
        ]}
      >
        {newsItems.map((item, index) => (
          <View key={item.id}>
            {index !== 0 ? (
              <View
                style={{
                  width: "100%",
                  height: 1,
                  backgroundColor: theme.border.default,
                }}
              />
            ) : null}
            <NewsItem newItem={item} />
          </View>
        ))}
      </View>
    </View>
  );
};

// ─── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  card: { borderRadius: 12, paddingHorizontal: 12 },
  newsRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    gap: 12,
  },
  newsText: { flex: 1 },
  divider: { height: 1 },
});

export default NewsSection;
