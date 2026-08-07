import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  FlatList,
  NativeScrollEvent,
  NativeSyntheticEvent,
  View,
} from "react-native";
import { Text } from "../ui/Text";
import { getTodayHighlights, TodayHighlight } from "@/helpers/MarketHelpers";
import TodayHighlightCard from "../ui/TodayHighlightCard";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const ITEM_WIDTH = SCREEN_WIDTH - 120;
const ITEM_MARGIN = 12;
const SNAP_INTERVAL = ITEM_WIDTH + ITEM_MARGIN;

// Hook tạo shimmer animation dùng chung
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

  const opacity = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.4, 0.85],
  });

  return opacity;
};

// Skeleton cho một card highlight
const TodayHighlightCardSkeleton = ({
  opacity,
}: {
  opacity: Animated.AnimatedInterpolation<number>;
}) => {
  const { theme } = useTheme();

  const Block = ({
    width,
    height,
    style,
  }: {
    width: number | `${number}%`;
    height: number;
    style?: object;
  }) => (
    <Animated.View
      style={{
        width,
        height,
        borderRadius: 4,
        backgroundColor: theme.border.default,
        opacity,
        ...style,
      }}
    />
  );

  return (
    <View
      style={{
        backgroundColor: theme.background.bg,
        borderRadius: 12,
        borderColor: theme.border.default,
        borderWidth: 1,
        marginRight: ITEM_MARGIN,
        width: ITEM_WIDTH,
      }}
    >
      {/* Header: logo + tên + giá */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginHorizontal: 12,
          marginVertical: 12,
        }}
      >
        <Animated.View
          style={{
            width: 36,
            height: 36,
            marginRight: 12,
            borderRadius: 8,
            backgroundColor: theme.border.default,
            opacity,
          }}
        />
        <View style={{ flex: 1, marginRight: 12, gap: 6 }}>
          <Block width={50} height={14} />
          <Block width="80%" height={11} />
        </View>
        <View style={{ marginRight: 16, gap: 6, alignItems: "flex-end" }}>
          <Block width={44} height={14} />
          <Block width={30} height={11} />
        </View>
        <Block width={48} height={24} style={{ borderRadius: 6 }} />
      </View>

      {/* News list */}
      <View
        style={{
          borderTopWidth: 1,
          borderColor: theme.border.default,
          paddingHorizontal: 12,
          paddingVertical: 6,
          backgroundColor: theme.background.surface,
          borderBottomLeftRadius: 12,
          borderBottomRightRadius: 12,
        }}
      >
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginVertical: 6,
          }}
        >
          <Animated.View
            style={{
              width: 18,
              height: 18,
              borderRadius: 4,
              backgroundColor: theme.border.default,
              opacity,
            }}
          />
          <View style={{ flex: 1, marginLeft: 12, gap: 6 }}>
            <Block width="95%" height={12} />
            <Block width="60%" height={12} />
          </View>
        </View>
      </View>
    </View>
  );
};

// Skeleton toàn bộ section
const TodayHighlightSkeleton = ({
  opacity,
}: {
  opacity: Animated.AnimatedInterpolation<number>;
}) => {
  return (
    <View style={{ flexDirection: "row", marginTop: 12, overflow: "hidden" }}>
      {Array.from({ length: 2 }).map((_, i) => (
        <TodayHighlightCardSkeleton key={i} opacity={opacity} />
      ))}
    </View>
  );
};

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

const TodayHighlightSection = ({ registerRefresh }: Props) => {
  const [data, setData] = useState<TodayHighlight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);
  const { theme } = useTheme();
  const { t } = useLocalization();
  const shimmerOpacity = useShimmer();

  const fetchData = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setIsLoading(true);
    }
    try {
      const result = await getTodayHighlights();
      if (result.status) {
        setData(result.data);
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
    const unregister = registerRefresh?.(() => fetchData(false));
    return () => unregister?.();
  }, [registerRefresh, fetchData]);

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    const index = Math.round(offsetX / SNAP_INTERVAL);
    setActiveIndex(index);
  };

  if (!isLoading && data.length === 0) {
    return null;
  }

  return (
    <View
      style={{
        marginHorizontal: 12,
        paddingLeft: 12,
        paddingVertical: 12,
        backgroundColor: theme.background.bg,
        borderRadius: 12,
      }}
    >
      <Text typography="titleMedium" color={theme.text.primary}>
        {t("market.todayHighlight")}
      </Text>

      {isLoading ? (
        <TodayHighlightSkeleton opacity={shimmerOpacity} />
      ) : (
        <FlatList
          ref={flatListRef}
          horizontal
          showsHorizontalScrollIndicator={false}
          data={data}
          keyExtractor={(item) => item.stock_id}
          renderItem={({ item }) => <TodayHighlightCard item={item} />}
          style={{ marginTop: 12 }}
          // Carousel config
          snapToInterval={SNAP_INTERVAL}
          snapToAlignment="start"
          decelerationRate="fast"
          onScroll={onScroll}
          scrollEventThrottle={16}
          contentContainerStyle={{ paddingRight: ITEM_MARGIN }}
        />
      )}

      {/* Pagination Dots */}
      {!isLoading && data.length > 1 && (
        <View
          style={{
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            marginTop: 12,
            gap: 6,
          }}
        >
          {data.map((_, index) => (
            <View
              key={index}
              style={{
                width: activeIndex === index ? 16 : 6,
                height: 6,
                borderRadius: 3,
                backgroundColor:
                  activeIndex === index
                    ? theme.base.primary
                    : theme.background.surface,
              }}
            />
          ))}
        </View>
      )}
    </View>
  );
};

export default TodayHighlightSection;
