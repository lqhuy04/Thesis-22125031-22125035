import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ActivityIndicator,
  Animated,
  Dimensions,
  FlatList,
  Image,
  RefreshControl,
  ScrollView,
  TouchableOpacity,
  View,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import LinearGradient from "react-native-linear-gradient";
import ScreenHeader from "@/components/ui/ScreenHeader";
import {
  getInvestingIdea,
  SuggestionInterval,
  SuggestionItem,
  SuggestionMsgType,
} from "@/helpers/MarketHelpers";
import { Text } from "@/components/ui/Text";
import IntervalBottomsheet, {
  INTERVAL_OPTIONS,
} from "@/components/ui/IntervalBottomsheet";
import AntDesign from "@expo/vector-icons/build/AntDesign";
import Entypo from "@expo/vector-icons/build/Entypo";
import Feather from "@expo/vector-icons/build/Feather";
import MaterialCommunityIcons from "@expo/vector-icons/build/MaterialCommunityIcons";
import Ionicons from "@expo/vector-icons/build/Ionicons";
import { router, useLocalSearchParams } from "expo-router";
import {
  formatPercentageChange,
  formatPriceChange,
  getStockChangeColor,
} from "@/helpers/stockChange";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

// Pagination: fetch 20 items per page, capped at 100 items total per list.
const PAGE_SIZE = 20;
const MAX_TOTAL_ITEMS = 100;

// Trend categories support a time-window `interval`; others ignore it.
const TREND_MSG_TYPES: SuggestionMsgType[] = [
  "top_gainers",
  "top_decliners",
  "top_volume",
];
const isTrendMsgType = (msgType: SuggestionMsgType) =>
  TREND_MSG_TYPES.includes(msgType);

// Cache key includes the interval only for trend tabs so each (tab, interval)
// pair is fetched and cached independently; non-trend tabs key by msgType alone.
const cacheKeyFor = (
  msgType: SuggestionMsgType,
  interval: SuggestionInterval,
) => (isTrendMsgType(msgType) ? `${msgType}__${interval}` : msgType);

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------
const SkeletonBox = ({
  width,
  height,
  borderRadius = 4,
  style,
  animatedOpacity,
}: {
  width: number | string;
  height: number;
  borderRadius?: number;
  style?: object;
  animatedOpacity: Animated.Value;
}) => {
  const { theme } = useTheme();
  return (
    <Animated.View
      style={[
        {
          width: width as any,
          height,
          borderRadius,
          backgroundColor: theme.text.primary + "20",
          opacity: animatedOpacity,
        },
        style,
      ]}
    />
  );
};

const InvestmentIdeasSkeleton = () => {
  const { theme } = useTheme();
  const animatedOpacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(animatedOpacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(animatedOpacity, {
          toValue: 0.3,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    shimmer.start();
    return () => shimmer.stop();
  }, [animatedOpacity]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.bg }}>
      {/* Sub-tabs (underline style) */}
      <View
        style={{
          flexDirection: "row",
          backgroundColor: theme.background.bg,
          borderTopLeftRadius: 12,
          borderTopRightRadius: 12,
        }}
      >
        {[90, 100, 85].map((w, i) => (
          <View
            key={i}
            style={{
              paddingHorizontal: 16,
              paddingVertical: 12,
              borderBottomWidth: 2,
              borderBottomColor: i === 0 ? theme.base.primary : "transparent",
            }}
          >
            <SkeletonBox
              width={w}
              height={14}
              borderRadius={4}
              animatedOpacity={animatedOpacity}
            />
          </View>
        ))}
      </View>

      {/* Table header */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          paddingHorizontal: 16,
          paddingVertical: 10,
          backgroundColor: theme.background.bg,
        }}
      >
        <SkeletonBox
          width={50}
          height={11}
          animatedOpacity={animatedOpacity}
          style={{ flex: 6, marginRight: 12 }}
        />
        <SkeletonBox
          width={36}
          height={11}
          animatedOpacity={animatedOpacity}
          style={{ flex: 1.5, marginRight: 12 }}
        />
        <SkeletonBox
          width={52}
          height={11}
          animatedOpacity={animatedOpacity}
          style={{ flex: 2.5 }}
        />
      </View>

      {/* Stock rows */}
      {Array.from({ length: 10 }).map((_, i) => (
        <View
          key={i}
          style={{
            flexDirection: "row",
            alignItems: "center",
            paddingHorizontal: 16,
            paddingVertical: 12,
            borderTopWidth: i === 0 ? 0 : 1,
            borderTopColor: theme.border.default,
            backgroundColor: theme.background.bg,
          }}
        >
          {/* Index number */}
          <SkeletonBox
            width={12}
            height={13}
            borderRadius={3}
            animatedOpacity={animatedOpacity}
            style={{ marginRight: 8 }}
          />
          {/* Logo */}
          <SkeletonBox
            width={32}
            height={32}
            borderRadius={8}
            animatedOpacity={animatedOpacity}
          />
          {/* Symbol + Company name */}
          <View style={{ flex: 6, marginLeft: 10, gap: 5, marginRight: 12 }}>
            <SkeletonBox
              width={44}
              height={13}
              animatedOpacity={animatedOpacity}
            />
            <SkeletonBox
              width={130}
              height={10}
              animatedOpacity={animatedOpacity}
            />
          </View>
          {/* Price + change */}
          <View style={{ flex: 1.5, marginRight: 12, gap: 4 }}>
            <SkeletonBox
              width={30}
              height={13}
              animatedOpacity={animatedOpacity}
            />
            <SkeletonBox
              width={24}
              height={10}
              animatedOpacity={animatedOpacity}
            />
          </View>
          {/* % badge */}
          <SkeletonBox
            width={"100%"}
            height={30}
            style={{ flex: 2.5 }}
            borderRadius={6}
            animatedOpacity={animatedOpacity}
          />
        </View>
      ))}
    </View>
  );
};

// Skeleton for a single full-screen page body (table only) — used when
// switching to a tab whose data is still loading.
const PageTableSkeleton = () => {
  const { theme } = useTheme();
  const animatedOpacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(animatedOpacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(animatedOpacity, {
          toValue: 0.3,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    shimmer.start();
    return () => shimmer.stop();
  }, [animatedOpacity]);

  return (
    <View
      style={{
        width: SCREEN_WIDTH,
        flex: 1,
        backgroundColor: theme.background.bg,
      }}
    >
      {/* Table header */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          paddingHorizontal: 16,
          paddingTop: 12,
          paddingBottom: 10,
          backgroundColor: theme.background.bg,
        }}
      >
        <SkeletonBox
          width={50}
          height={11}
          animatedOpacity={animatedOpacity}
          style={{ flex: 6, marginRight: 12 }}
        />
        <SkeletonBox
          width={36}
          height={11}
          animatedOpacity={animatedOpacity}
          style={{ flex: 1.5, marginRight: 12 }}
        />
        <SkeletonBox
          width={52}
          height={11}
          animatedOpacity={animatedOpacity}
          style={{ flex: 2.5 }}
        />
      </View>

      {/* Stock rows */}
      {Array.from({ length: 10 }).map((_, i) => (
        <View
          key={i}
          style={{
            flexDirection: "row",
            alignItems: "center",
            paddingHorizontal: 16,
            paddingVertical: 12,
            borderTopWidth: i === 0 ? 0 : 1,
            borderTopColor: theme.border.default,
            backgroundColor: theme.background.bg,
          }}
        >
          {/* Index number */}
          <SkeletonBox
            width={12}
            height={13}
            borderRadius={3}
            animatedOpacity={animatedOpacity}
            style={{ marginRight: 8 }}
          />
          {/* Logo */}
          <SkeletonBox
            width={32}
            height={32}
            borderRadius={8}
            animatedOpacity={animatedOpacity}
          />
          {/* Symbol + Company name */}
          <View style={{ flex: 6, marginLeft: 10, gap: 5, marginRight: 12 }}>
            <SkeletonBox
              width={44}
              height={13}
              animatedOpacity={animatedOpacity}
            />
            <SkeletonBox
              width={130}
              height={10}
              animatedOpacity={animatedOpacity}
            />
          </View>
          {/* Price + change */}
          <View style={{ flex: 1.5, marginRight: 12, gap: 4 }}>
            <SkeletonBox
              width={30}
              height={13}
              animatedOpacity={animatedOpacity}
            />
            <SkeletonBox
              width={24}
              height={10}
              animatedOpacity={animatedOpacity}
            />
          </View>
          {/* % badge */}
          <SkeletonBox
            width={"100%"}
            height={30}
            style={{ flex: 2.5 }}
            borderRadius={6}
            animatedOpacity={animatedOpacity}
          />
        </View>
      ))}
    </View>
  );
};

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------
type InvestingIdeaPageState = {
  items: SuggestionItem[];
  hasMore: boolean;
  loadingMore: boolean;
};

const InvestmentIdeas = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();
  const [dataMap, setDataMap] = useState<
    Record<string, InvestingIdeaPageState>
  >({});
  const loadingRef = useRef<Set<string>>(new Set());
  const refreshingRef = useRef(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeGroup, setActiveGroup] = useState<
    "trend" | "community" | "top_choice"
  >("top_choice");
  const [currentPage, setCurrentPage] = useState(0);

  // Selected time window for trend tabs + bottom-sheet visibility.
  const [selectedInterval, setSelectedInterval] =
    useState<SuggestionInterval>("today");
  const [intervalSheetVisible, setIntervalSheetVisible] = useState(false);

  type SortKey = "symbol" | "price" | "change";
  type SortDir = "asc" | "desc";

  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSortPress = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const flatListRef = useRef<FlatList>(null);
  const params = useLocalSearchParams<{ tab?: string; msgType?: string }>();

  // ------------------------------------------------------------------
  // Tabs definition (same logic as SuggestionSection)
  // ------------------------------------------------------------------
  const tabs = useMemo(() => {
    return [
      {
        icon: (
          <MaterialCommunityIcons
            name="tag-heart-outline"
            size={28}
            color={theme.base.primary}
          />
        ),
        title: t("suggestion.topUnder50kTitle"),
        description: t("suggestion.topUnder50kDescription"),
        group: "top_choice" as const,
        msgType: "cheap_under_50k" as const,
      },
      {
        icon: <AntDesign name="rise" size={28} color={theme.base.success} />,
        title: t("suggestion.topGainersTitle"),
        description: t("suggestion.topGainersDescription"),
        group: "trend" as const,
        msgType: "top_gainers" as const,
      },
      {
        icon: <AntDesign name="fall" size={28} color={theme.base.error} />,
        title: t("suggestion.topDeclinersTitle"),
        description: t("suggestion.topDeclinersDescription"),
        group: "trend" as const,
        msgType: "top_decliners" as const,
      },
      {
        icon: <Entypo name="bar-graph" size={28} color={theme.base.primary} />,
        title: t("suggestion.topVolumeTitle"),
        description: t("suggestion.topVolumeDescription"),
        group: "trend" as const,
        msgType: "top_volume" as const,
      },
      {
        icon: <Feather name="search" size={28} color={theme.base.primary} />,
        title: t("suggestion.topSearchedTitle"),
        description: t("suggestion.topSearchedDescription"),
        group: "community" as const,
        msgType: "top_searched" as const,
      },
      {
        icon: (
          <MaterialCommunityIcons
            name="eye-plus-outline"
            size={28}
            color={theme.base.primary}
          />
        ),
        title: t("suggestion.topWatchlistTitle"),
        description: t("suggestion.topWatchlistDescription"),
        group: "community" as const,
        msgType: "top_watchlist" as const,
      },
    ];
  }, [t, theme.base.error, theme.base.primary, theme.base.success]);

  const trendTabs = tabs.filter((t) => t.group === "trend");
  const topChoiceTabs = tabs.filter((t) => t.group === "top_choice");
  const communityTabs = tabs.filter((t) => t.group === "community");

  // Global index offsets (matches SuggestionSection)
  const topChoiceStartIndex = 0;
  const trendStartIndex = topChoiceTabs.length; // = 1
  const communityStartIndex = trendStartIndex + trendTabs.length; // = 4

  // Tabs shown under current group
  const activeTabs =
    activeGroup === "trend"
      ? trendTabs
      : activeGroup === "top_choice"
        ? topChoiceTabs
        : communityTabs;

  // Dot index relative to the active group
  const activeStartIndex =
    activeGroup === "trend"
      ? trendStartIndex
      : activeGroup === "top_choice"
        ? topChoiceStartIndex
        : communityStartIndex;

  // ------------------------------------------------------------------
  // Lazy-load page 1 of a single category, cached by msgType. Each tab loads once.
  const loadTab = useCallback(
    (msgType: SuggestionMsgType, interval: SuggestionInterval) => {
      const key = cacheKeyFor(msgType, interval);
      setDataMap((prev) => {
        if (prev[key] !== undefined || loadingRef.current.has(key)) {
          return prev;
        }
        loadingRef.current.add(key);
        getInvestingIdea(
          msgType,
          PAGE_SIZE,
          isTrendMsgType(msgType) ? interval : undefined,
          0,
        )
          .then((res) => {
            if (!res?.status) return;
            const items = res.data;
            setDataMap((curr) => ({
              ...curr,
              [key]: {
                items,
                hasMore:
                  items.length === PAGE_SIZE && items.length < MAX_TOTAL_ITEMS,
                loadingMore: false,
              },
            }));
          })
          .finally(() => loadingRef.current.delete(key));
        return prev;
      });
    },
    [],
  );

  // Load the next page for a category (infinite scroll), appending to what's
  // already loaded. Scoped to the exact (msgType, interval) pair calling it,
  // so scrolling one tab never fetches data for another.
  const loadMoreTab = useCallback(
    (msgType: SuggestionMsgType, interval: SuggestionInterval) => {
      const key = cacheKeyFor(msgType, interval);
      setDataMap((prev) => {
        const current = prev[key];
        if (
          !current ||
          !current.hasMore ||
          current.loadingMore ||
          loadingRef.current.has(key)
        ) {
          return prev;
        }
        loadingRef.current.add(key);
        const offset = current.items.length;
        getInvestingIdea(
          msgType,
          PAGE_SIZE,
          isTrendMsgType(msgType) ? interval : undefined,
          offset,
        )
          .then((res) => {
            if (!res?.status) {
              setDataMap((curr) => {
                const existing = curr[key];
                if (!existing) return curr;
                return {
                  ...curr,
                  [key]: { ...existing, loadingMore: false },
                };
              });
              return;
            }
            const newItems = res.data;
            setDataMap((curr) => {
              const existing = curr[key];
              if (!existing) return curr;
              const merged = [...existing.items, ...newItems];
              return {
                ...curr,
                [key]: {
                  items: merged,
                  hasMore:
                    newItems.length === PAGE_SIZE &&
                    merged.length < MAX_TOTAL_ITEMS,
                  loadingMore: false,
                },
              };
            });
          })
          .finally(() => loadingRef.current.delete(key));
        return { ...prev, [key]: { ...current, loadingMore: true } };
      });
    },
    [],
  );

  // Load whichever page is currently visible (also covers initial mount and
  // interval changes for trend tabs).
  useEffect(() => {
    const tab = tabs[currentPage];
    if (tab) loadTab(tab.msgType, selectedInterval);
  }, [currentPage, selectedInterval, loadTab, tabs]);

  // ------------------------------------------------------------------
  // Handlers
  // ------------------------------------------------------------------
  const handleGroupPress = (group: "trend" | "community" | "top_choice") => {
    setActiveGroup(group);
    const targetIndex =
      group === "trend"
        ? trendStartIndex
        : group === "top_choice"
          ? topChoiceStartIndex
          : communityStartIndex;
    flatListRef.current?.scrollToIndex({ index: targetIndex, animated: true });
    setCurrentPage(targetIndex);
  };

  // Jump to the exact sub-tab passed via navigation params (from
  // SuggestionSection); falls back to the group's first sub-tab if the
  // msgType isn't found.
  useEffect(() => {
    if (
      params.tab !== "trend" &&
      params.tab !== "community" &&
      params.tab !== "top_choice"
    ) {
      return;
    }
    const matchedIndex = tabs.findIndex((t) => t.msgType === params.msgType);
    if (matchedIndex !== -1) {
      setActiveGroup(params.tab);
      flatListRef.current?.scrollToIndex({
        index: matchedIndex,
        animated: true,
      });
      setCurrentPage(matchedIndex);
    } else {
      handleGroupPress(params.tab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.tab, params.msgType, tabs]);

  const handleSubTabPress = (globalIndex: number) => {
    flatListRef.current?.scrollToIndex({ index: globalIndex, animated: true });
    setCurrentPage(globalIndex);
  };

  const handleScrollEnd = (e: any) => {
    const offsetX = e.nativeEvent.contentOffset.x;
    const page = Math.round(offsetX / SCREEN_WIDTH);
    setCurrentPage(page);

    if (page < trendStartIndex) {
      setActiveGroup("top_choice");
    } else if (page < communityStartIndex) {
      setActiveGroup("trend");
    } else {
      setActiveGroup("community");
    }
  };

  const handleRefresh = useCallback(async () => {
    if (refreshingRef.current) {
      return;
    }

    const activeTab = tabs[currentPage];
    if (!activeTab) {
      return;
    }

    const key = cacheKeyFor(activeTab.msgType, selectedInterval);
    refreshingRef.current = true;
    setIsRefreshing(true);

    try {
      const result = await getInvestingIdea(
        activeTab.msgType,
        PAGE_SIZE,
        isTrendMsgType(activeTab.msgType) ? selectedInterval : undefined,
        0,
      );

      if (result.status) {
        setDataMap((current) => ({
          ...current,
          [key]: {
            items: result.data,
            hasMore:
              result.data.length === PAGE_SIZE &&
              result.data.length < MAX_TOTAL_ITEMS,
            loadingMore: false,
          },
        }));
      }
    } finally {
      refreshingRef.current = false;
      setIsRefreshing(false);
    }
  }, [currentPage, selectedInterval, tabs]);

  // ------------------------------------------------------------------
  // Render a single full-screen stock row
  // ------------------------------------------------------------------
  const renderStockRow = (stock: SuggestionItem, index: number) => {
    const priceChangeColor = getStockChangeColor(
      stock.price_change,
      theme.base,
    );
    const perPriceChangeColor = getStockChangeColor(
      stock.per_price_change,
      theme.base,
    );

    return (
      <TouchableOpacity
        key={index.toString()}
        onPress={() =>
          router.push({ pathname: "/Detail", params: { data: stock.symbol } })
        }
        style={{
          flexDirection: "row",
          alignItems: "center",
          paddingHorizontal: 16,
          paddingVertical: 12,
          borderTopWidth: index === 0 ? 0 : 1,
          borderTopColor: theme.border.default,
          backgroundColor: theme.background.bg,
        }}
      >
        {/* Symbol column */}
        <View
          style={{
            flex: 6,
            flexDirection: "row",
            alignItems: "center",
            marginRight: 12,
          }}
        >
          <Text
            typography="labelLarge"
            color={theme.base.primary}
            style={{ width: 28 }}
          >
            {index + 1}
          </Text>
          <Image
            source={{
              uri:
                stock.logo ??
                "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png",
            }}
            style={{ width: 32, height: 32, borderRadius: 8, marginRight: 10 }}
          />
          <View style={{ flex: 1 }}>
            <Text
              typography="labelLarge"
              color={theme.text.primary}
              numberOfLines={1}
            >
              {stock.symbol}
            </Text>
            <Text
              typography="bodySmall"
              color={theme.text.primary + "70"}
              numberOfLines={1}
            >
              {stock.company_name}
            </Text>
          </View>
        </View>
        <View style={{ flex: 1.5, marginRight: 12 }}>
          <Text typography="labelLarge" color={theme.text.primary}>
            {stock.current_price.toLocaleString("vi-VN", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Text>
          <Text typography="bodySmall" color={priceChangeColor}>
            {formatPriceChange(stock.price_change)}
          </Text>
        </View>
        <View
          style={{
            backgroundColor: perPriceChangeColor + "20",
            borderRadius: 6,
            flex: 2.5,
            alignItems: "center",
            justifyContent: "center",
            paddingVertical: 6,
          }}
        >
          <Text typography="labelMedium" color={perPriceChangeColor}>
            {formatPercentageChange(stock.per_price_change)}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  // ------------------------------------------------------------------
  // Render one full-screen page
  // ------------------------------------------------------------------
  const renderPage = ({ item }: { item: (typeof tabs)[0] }) => {
    const pageState = dataMap[cacheKeyFor(item.msgType, selectedInterval)];

    if (pageState === undefined) {
      return <PageTableSkeleton />;
    }

    const intervalLabelKey =
      INTERVAL_OPTIONS.find((o) => o.value === selectedInterval)?.labelKey ??
      "suggestion.intervalToday";

    const sortedData = [...pageState.items].sort((a, b) => {
      if (!sortKey) return 0;
      let diff = 0;
      if (sortKey === "symbol") diff = a.symbol.localeCompare(b.symbol);
      else if (sortKey === "price") diff = a.current_price - b.current_price;
      else if (sortKey === "change")
        diff = a.per_price_change - b.per_price_change;
      return sortDir === "asc" ? diff : -diff;
    });

    // Infinite scroll: fetch the next page for this exact tab + interval
    // once the user nears the bottom of its own ScrollView.
    const handlePageScroll = (e: any) => {
      const { layoutMeasurement, contentOffset, contentSize } = e.nativeEvent;
      const distanceFromBottom =
        contentSize.height - (layoutMeasurement.height + contentOffset.y);
      if (distanceFromBottom < 200) {
        loadMoreTab(item.msgType, selectedInterval);
      }
    };

    return (
      <View style={{ width: SCREEN_WIDTH, flex: 1 }}>
        <ScrollView
          alwaysBounceVertical
          style={{ flex: 1 }}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 32, flexGrow: 1 }}
          onScroll={handlePageScroll}
          scrollEventThrottle={16}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={handleRefresh}
              colors={["transparent"]}
              progressBackgroundColor="transparent"
              tintColor="transparent"
            />
          }
        >
          {/* Table header */}
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              paddingHorizontal: 16,
              paddingTop: 12,
              backgroundColor: theme.background.bg,
            }}
          >
            {/* Symbol — sortable */}
            <TouchableOpacity
              onPress={() => handleSortPress("symbol")}
              style={{
                flex: 6,
                flexDirection: "row",
                alignItems: "center",
                marginRight: 12,
              }}
            >
              <Text
                typography="bodySmall"
                color={
                  sortKey === "symbol" ? theme.base.primary : theme.text.primary
                }
              >
                {t("suggestion.columnSymbol")}
              </Text>
              <View style={{ marginLeft: 4, alignItems: "center" }}>
                <Entypo
                  name="chevron-small-up"
                  size={14}
                  color={
                    sortKey === "symbol" && sortDir === "asc"
                      ? theme.base.primary
                      : theme.text.primary + "40"
                  }
                  style={{ marginBottom: -2 }}
                />
                <Entypo
                  name="chevron-small-down"
                  size={14}
                  color={
                    sortKey === "symbol" && sortDir === "desc"
                      ? theme.base.primary
                      : theme.text.primary + "40"
                  }
                  style={{ marginTop: -2 }}
                />
              </View>
            </TouchableOpacity>

            {/* Price — sortable */}
            <TouchableOpacity
              onPress={() => handleSortPress("price")}
              style={{
                flex: 1.5,
                flexDirection: "row",
                alignItems: "center",
                marginRight: 12,
              }}
            >
              <Text
                typography="bodySmall"
                color={
                  sortKey === "price" ? theme.base.primary : theme.text.primary
                }
              >
                {t("suggestion.columnPrice")}
              </Text>
              <View style={{ marginLeft: 4, alignItems: "center" }}>
                <Entypo
                  name="chevron-small-up"
                  size={14}
                  color={
                    sortKey === "price" && sortDir === "asc"
                      ? theme.base.primary
                      : theme.text.primary + "40"
                  }
                  style={{ marginBottom: -2 }}
                />
                <Entypo
                  name="chevron-small-down"
                  size={14}
                  color={
                    sortKey === "price" && sortDir === "desc"
                      ? theme.base.primary
                      : theme.text.primary + "40"
                  }
                  style={{ marginTop: -2 }}
                />
              </View>
            </TouchableOpacity>

            {/* % Change — sortable */}
            <View
              style={{
                flex: 2.5,
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <TouchableOpacity
                onPress={() => handleSortPress("change")}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                }}
              >
                <Text
                  typography="bodySmall"
                  color={
                    sortKey === "change"
                      ? theme.base.primary
                      : theme.text.primary
                  }
                >
                  %
                </Text>
                <View style={{ marginLeft: 4, alignItems: "center" }}>
                  <Entypo
                    name="chevron-small-up"
                    size={14}
                    color={
                      sortKey === "change" && sortDir === "asc"
                        ? theme.base.primary
                        : theme.text.primary + "40"
                    }
                    style={{ marginBottom: -2 }}
                  />
                  <Entypo
                    name="chevron-small-down"
                    size={14}
                    color={
                      sortKey === "change" && sortDir === "desc"
                        ? theme.base.primary
                        : theme.text.primary + "40"
                    }
                    style={{ marginTop: -2 }}
                  />
                </View>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={() =>
                  activeGroup === "trend" && setIntervalSheetVisible(true)
                }
                style={{ flexDirection: "row", alignItems: "center" }}
                activeOpacity={item.group === "trend" ? 0.7 : 1}
              >
                <Text typography="bodySmall" color={theme.text.primary}>
                  {item.group === "trend"
                    ? t(intervalLabelKey)
                    : t("suggestion.intervalToday")}
                </Text>
                <Text
                  typography="bodySmall"
                  color={theme.text.primary}
                  style={{ marginLeft: 3 }}
                >
                  ▼
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Rows */}
          {sortedData.map((stock: SuggestionItem, index: number) =>
            renderStockRow(stock, index),
          )}

          {/* Loading indicator while fetching the next page */}
          {pageState.loadingMore && (
            <View style={{ paddingVertical: 16, alignItems: "center" }}>
              <ActivityIndicator color={theme.base.primary} />
            </View>
          )}
        </ScrollView>
      </View>
    );
  };

  // ------------------------------------------------------------------
  // Loading state — show full skeleton until the first tab has loaded.
  // ------------------------------------------------------------------
  if (dataMap[cacheKeyFor(tabs[0].msgType, selectedInterval)] === undefined) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
        <LinearGradient
          colors={["#9D8CFF", "#7B5CFF", "#613DE4"]}
          useAngle
          angle={120}
          angleCenter={{ x: 0.5, y: 0.5 }}
          style={{ paddingBottom: 0 }}
        >
          <ScreenHeader title={t("suggestion.sectionTitle")} />

          {/* Group tab skeletons — matches real UI: wide cards */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{
              paddingHorizontal: 12,
              paddingTop: 12,
              gap: 8,
              flexDirection: "row",
            }}
          >
            {[0, 1, 2].map((i) => (
              <View
                key={i}
                style={{
                  width: 200,
                  paddingHorizontal: 14,
                  paddingVertical: 16,
                  borderRadius: 10,
                  backgroundColor: "rgba(255,255,255,0.15)",
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <View
                  style={{
                    width: 100,
                    height: 14,
                    borderRadius: 4,
                    backgroundColor: "rgba(255,255,255,0.3)",
                  }}
                />
                <View
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: 4,
                    backgroundColor: "rgba(255,255,255,0.3)",
                  }}
                />
              </View>
            ))}
          </ScrollView>

          {/* Description text skeleton */}
          <View
            style={{
              width: 240,
              height: 12,
              borderRadius: 4,
              backgroundColor: "rgba(255,255,255,0.25)",
              marginHorizontal: 12,
              marginTop: 8,
              marginBottom: 12,
            }}
          />

          {/* Sub-tab skeletons */}
          <View
            style={{
              flexDirection: "row",
              backgroundColor: theme.background.bg,
              borderTopLeftRadius: 12,
              borderTopRightRadius: 12,
            }}
          >
            {[90, 100, 85].map((w, i) => (
              <View
                key={i}
                style={{ paddingHorizontal: 16, paddingVertical: 12 }}
              >
                <View
                  style={{
                    width: w,
                    height: 14,
                    borderRadius: 4,
                    backgroundColor: theme.background.surface + "80",
                  }}
                />
              </View>
            ))}
          </View>
        </LinearGradient>

        <InvestmentIdeasSkeleton />
      </View>
    );
  }

  // ------------------------------------------------------------------
  // Full render
  // ------------------------------------------------------------------
  return (
    <View style={{ flex: 1, backgroundColor: theme.background.bg }}>
      {/* ── Gradient header ── */}
      <LinearGradient
        colors={["#9D8CFF", "#7B5CFF", "#613DE4"]}
        useAngle
        angle={120}
        angleCenter={{ x: 0.5, y: 0.5 }}
      >
        <ScreenHeader title={t("suggestion.sectionTitle")} />

        {/* Group tabs */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{
            paddingHorizontal: 12,
            paddingTop: 12,
            gap: 8,
            flexDirection: "row",
          }}
        >
          {(["top_choice", "trend", "community"] as const).map((tab) => {
            const isActive = activeGroup === tab;
            const label =
              tab === "trend"
                ? t("suggestion.tabTrend")
                : tab === "top_choice"
                  ? t("suggestion.tabTopChoice")
                  : t("suggestion.tabCommunity");

            return (
              <TouchableOpacity
                key={tab}
                onPress={() => handleGroupPress(tab)}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  width: 200,
                  gap: 6,
                  paddingHorizontal: 14,
                  paddingVertical: 16,
                  borderRadius: 10,
                  backgroundColor: isActive
                    ? theme.background.bg
                    : theme.background.bg + "66",
                  borderWidth: 1.5,
                  borderColor: isActive ? theme.base.primary : "transparent",
                }}
              >
                <Text
                  typography="bodyMedium"
                  color={theme.text.primary}
                  style={{ flex: 1 }}
                >
                  {label}
                </Text>

                {tab === "top_choice" ? (
                  <AntDesign
                    name="stock"
                    size={20}
                    color={isActive ? theme.base.primary : theme.text.primary}
                  />
                ) : tab === "trend" ? (
                  <Entypo
                    name="bar-graph"
                    size={20}
                    color={isActive ? theme.base.primary : theme.text.primary}
                  />
                ) : (
                  <Ionicons
                    name="people"
                    size={20}
                    color={isActive ? theme.base.primary : theme.text.primary}
                  />
                )}
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        <Text
          typography="bodySmall"
          color={theme.text.onPrimary}
          style={{ paddingHorizontal: 12, marginTop: 8 }}
        >
          {activeGroup === "trend"
            ? t("suggestion.screenDescTrend")
            : activeGroup === "top_choice"
              ? t("suggestion.screenDescTopchoice")
              : t("suggestion.screenDescCommunity")}
        </Text>

        {/* Sub-tabs (within the active group) */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{
            gap: 4,
            flexDirection: "row",
            width: "100%",
            backgroundColor: theme.background.bg,
            marginTop: 12,
            borderTopLeftRadius: 12,
            borderTopRightRadius: 12,
          }}
        >
          {activeTabs.map((tab, localIdx) => {
            const globalIdx = activeStartIndex + localIdx;
            const isActive = currentPage === globalIdx;
            return (
              <TouchableOpacity
                key={globalIdx}
                onPress={() => handleSubTabPress(globalIdx)}
                style={{
                  paddingHorizontal: 16,
                  paddingVertical: 12,
                  borderBottomWidth: 2,
                  borderBottomColor: isActive
                    ? theme.base.primary
                    : "transparent",
                }}
              >
                <Text
                  typography="titleSmall"
                  color={isActive ? theme.base.primary : theme.text.primary}
                >
                  {tab.title}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </LinearGradient>

      {/* ── Horizontal FlatList of full-screen pages ── */}
      <FlatList
        ref={flatListRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        data={tabs}
        initialScrollIndex={currentPage}
        keyExtractor={(_, index) => index.toString()}
        onMomentumScrollEnd={handleScrollEnd}
        getItemLayout={(_, index) => ({
          length: SCREEN_WIDTH,
          offset: SCREEN_WIDTH * index,
          index,
        })}
        renderItem={renderPage}
        style={{ flex: 1, paddingBottom: 24 }}
      />

      <IntervalBottomsheet
        visible={intervalSheetVisible}
        selectedInterval={selectedInterval}
        onSelect={setSelectedInterval}
        onClose={() => setIntervalSheetVisible(false)}
      />
    </View>
  );
};

export default InvestmentIdeas;
