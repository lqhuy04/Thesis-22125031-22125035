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
  ScrollView,
  TouchableOpacity,
  View,
} from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import {
  getInvestingIdea,
  SuggestionItem,
  SuggestionMsgType,
} from "@/helpers/MarketHelpers";
import LinearGradient from "react-native-linear-gradient";
import Entypo from "@expo/vector-icons/Entypo";
import AntDesign from "@expo/vector-icons/AntDesign";
import Feather from "@expo/vector-icons/Feather";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { router } from "expo-router";

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
  return (
    <Animated.View
      style={[
        {
          width: width as any,
          height,
          borderRadius,
          backgroundColor: "#FFFFFF40",
          opacity: animatedOpacity,
        },
        style,
      ]}
    />
  );
};

// Skeleton for just the card body (table) — used when switching to a tab
// whose data is still loading.
const SuggestionCardBodySkeleton = () => {
  const { theme } = useTheme();
  const rowOpacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(rowOpacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(rowOpacity, {
          toValue: 0.3,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    shimmer.start();
    return () => shimmer.stop();
  }, [rowOpacity]);

  return (
    <>
      {/* Table */}
      <View
        style={{
          marginHorizontal: 12,
          marginBottom: 12,
          borderRadius: 12,
          backgroundColor: theme.background.bg,
          overflow: "hidden",
        }}
      >
        {/* Table Header */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            paddingHorizontal: 12,
            paddingVertical: 8,
          }}
        >
          <SkeletonBox
            width={60}
            height={11}
            animatedOpacity={rowOpacity}
            style={{
              flex: 6.5,
              marginRight: 16,
              backgroundColor: theme.text.primary + "20",
            }}
          />
          <SkeletonBox
            width={40}
            height={11}
            animatedOpacity={rowOpacity}
            style={{
              flex: 2,
              marginRight: 16,
              backgroundColor: theme.text.primary + "20",
            }}
          />
          <SkeletonBox
            width={60}
            height={11}
            animatedOpacity={rowOpacity}
            style={{
              flex: 3.5,
              backgroundColor: theme.text.primary + "20",
            }}
          />
        </View>

        {/* Skeleton Rows */}
        {Array.from({ length: 5 }).map((_, index) => (
          <View
            key={index}
            style={{
              flexDirection: "row",
              alignItems: "center",
              paddingHorizontal: 12,
              paddingVertical: 10,
              borderTopWidth: 1,
              borderTopColor: theme.border.default,
            }}
          >
            {/* Logo + Symbol + Name */}
            <View
              style={{
                flex: 6.5,
                flexDirection: "row",
                alignItems: "center",
                gap: 8,
                marginRight: 16,
              }}
            >
              <SkeletonBox
                width={24}
                height={24}
                borderRadius={8}
                animatedOpacity={rowOpacity}
                style={{ backgroundColor: theme.text.primary + "20" }}
              />
              <View style={{ flex: 1, gap: 4 }}>
                <SkeletonBox
                  width={40}
                  height={12}
                  animatedOpacity={rowOpacity}
                  style={{ backgroundColor: theme.text.primary + "20" }}
                />
                <SkeletonBox
                  width={"80%" as any}
                  height={10}
                  animatedOpacity={rowOpacity}
                  style={{ backgroundColor: theme.text.primary + "20" }}
                />
              </View>
            </View>

            {/* Price */}
            <View style={{ flex: 2, marginRight: 16, gap: 4 }}>
              <SkeletonBox
                width={36}
                height={12}
                animatedOpacity={rowOpacity}
                style={{ backgroundColor: theme.text.primary + "20" }}
              />
              <SkeletonBox
                width={28}
                height={10}
                animatedOpacity={rowOpacity}
                style={{ backgroundColor: theme.text.primary + "20" }}
              />
            </View>

            {/* % Badge */}
            <View style={{ flex: 3.4, alignItems: "flex-end" }}>
              <SkeletonBox
                width={"100%" as any}
                height={28}
                borderRadius={4}
                animatedOpacity={rowOpacity}
                style={{ backgroundColor: theme.text.primary + "20" }}
              />
            </View>
          </View>
        ))}
      </View>

      {/* View more placeholder */}
      <View
        style={{
          alignItems: "center",
          paddingBottom: 16,
          flexDirection: "row",
          justifyContent: "center",
        }}
      >
        <SkeletonBox
          width={80}
          height={12}
          animatedOpacity={rowOpacity}
          style={{ backgroundColor: theme.text.primary + "20" }}
        />
      </View>
    </>
  );
};

const SuggestionSectionSkeleton = () => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;
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

  const rowOpacity = useRef(new Animated.Value(0.3)).current;
  useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(rowOpacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(rowOpacity, {
          toValue: 0.3,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    shimmer.start();
    return () => shimmer.stop();
  }, [rowOpacity]);

  return (
    <View style={{ marginTop: 24, marginHorizontal: 12 }}>
      <SkeletonBox
        width={160}
        height={20}
        animatedOpacity={animatedOpacity}
        style={{ backgroundColor: theme.text.primary + "30" }}
      />

      <LinearGradient
        colors={["#9D8CFF", "#7B5CFF", "#613DE4"]}
        useAngle
        angle={90}
        angleCenter={{ x: 0.5, y: 0.5 }}
        style={{ marginTop: 12, borderRadius: 12 }}
      >
        {/* Tab placeholders */}
        <View
          style={{
            flexDirection: "row",
            marginTop: 12,
            gap: 8,
            marginHorizontal: 12,
          }}
        >
          <SkeletonBox
            width={80}
            height={26}
            borderRadius={24}
            animatedOpacity={animatedOpacity}
          />
          <SkeletonBox
            width={60}
            height={26}
            borderRadius={24}
            animatedOpacity={animatedOpacity}
          />
          <SkeletonBox
            width={120}
            height={26}
            borderRadius={24}
            animatedOpacity={animatedOpacity}
          />
        </View>

        {/* Card placeholder */}
        <View
          style={{
            width: screenWidth - 48,
            margin: 12,
            borderRadius: 12,
            backgroundColor: theme.background.surface,
            overflow: "hidden",
          }}
        >
          {/* Card Header */}
          <View
            style={{
              flexDirection: "row",
              justifyContent: "space-between",
              alignItems: "center",
              margin: 12,
            }}
          >
            <View style={{ gap: 6 }}>
              <SkeletonBox
                width={130}
                height={16}
                animatedOpacity={rowOpacity}
                style={{ backgroundColor: theme.text.primary + "20" }}
              />
              <SkeletonBox
                width={180}
                height={12}
                animatedOpacity={rowOpacity}
                style={{ backgroundColor: theme.text.primary + "20" }}
              />
            </View>
            <SkeletonBox
              width={36}
              height={36}
              borderRadius={8}
              animatedOpacity={rowOpacity}
              style={{
                marginRight: 12,
                backgroundColor: theme.text.primary + "20",
              }}
            />
          </View>

          {/* Table */}
          <View
            style={{
              marginHorizontal: 12,
              marginBottom: 12,
              borderRadius: 12,
              backgroundColor: theme.background.bg,
              overflow: "hidden",
            }}
          >
            {/* Table Header */}
            <View
              style={{
                flexDirection: "row",
                alignItems: "center",
                paddingHorizontal: 12,
                paddingVertical: 8,
              }}
            >
              <SkeletonBox
                width={60}
                height={11}
                animatedOpacity={rowOpacity}
                style={{
                  flex: 6.5,
                  marginRight: 16,
                  backgroundColor: theme.text.primary + "20",
                }}
              />
              <SkeletonBox
                width={40}
                height={11}
                animatedOpacity={rowOpacity}
                style={{
                  flex: 2,
                  marginRight: 16,
                  backgroundColor: theme.text.primary + "20",
                }}
              />
              <SkeletonBox
                width={60}
                height={11}
                animatedOpacity={rowOpacity}
                style={{
                  flex: 3.5,
                  backgroundColor: theme.text.primary + "20",
                }}
              />
            </View>

            {/* Skeleton Rows */}
            {Array.from({ length: 5 }).map((_, index) => (
              <View
                key={index}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  paddingHorizontal: 12,
                  paddingVertical: 10,
                  borderTopWidth: 1,
                  borderTopColor: theme.border.default,
                }}
              >
                {/* Logo + Symbol + Name */}
                <View
                  style={{
                    flex: 6.5,
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 8,
                    marginRight: 16,
                  }}
                >
                  <SkeletonBox
                    width={24}
                    height={24}
                    borderRadius={8}
                    animatedOpacity={rowOpacity}
                    style={{ backgroundColor: theme.text.primary + "20" }}
                  />
                  <View style={{ flex: 1, gap: 4 }}>
                    <SkeletonBox
                      width={40}
                      height={12}
                      animatedOpacity={rowOpacity}
                      style={{ backgroundColor: theme.text.primary + "20" }}
                    />
                    <SkeletonBox
                      width={"80%" as any}
                      height={10}
                      animatedOpacity={rowOpacity}
                      style={{ backgroundColor: theme.text.primary + "20" }}
                    />
                  </View>
                </View>

                {/* Price */}
                <View style={{ flex: 2, marginRight: 16, gap: 4 }}>
                  <SkeletonBox
                    width={36}
                    height={12}
                    animatedOpacity={rowOpacity}
                    style={{ backgroundColor: theme.text.primary + "20" }}
                  />
                  <SkeletonBox
                    width={28}
                    height={10}
                    animatedOpacity={rowOpacity}
                    style={{ backgroundColor: theme.text.primary + "20" }}
                  />
                </View>

                {/* % Badge */}
                <View style={{ flex: 3.4, alignItems: "flex-end" }}>
                  <SkeletonBox
                    width={"100%" as any}
                    height={28}
                    borderRadius={4}
                    animatedOpacity={rowOpacity}
                    style={{ backgroundColor: theme.text.primary + "20" }}
                  />
                </View>
              </View>
            ))}
          </View>

          {/* View more placeholder */}
          <View
            style={{
              alignItems: "center",
              paddingBottom: 16,
              flexDirection: "row",
              justifyContent: "center",
            }}
          >
            <SkeletonBox
              width={80}
              height={12}
              animatedOpacity={rowOpacity}
              style={{ backgroundColor: theme.text.primary + "20" }}
            />
          </View>
        </View>

        {/* Page indicator placeholder */}
        <View
          style={{
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            paddingBottom: 12,
            gap: 6,
          }}
        >
          <SkeletonBox
            width={20}
            height={6}
            borderRadius={3}
            animatedOpacity={animatedOpacity}
          />
          <SkeletonBox
            width={6}
            height={6}
            borderRadius={3}
            animatedOpacity={animatedOpacity}
          />
          <SkeletonBox
            width={6}
            height={6}
            borderRadius={3}
            animatedOpacity={animatedOpacity}
          />
        </View>
      </LinearGradient>
    </View>
  );
};

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

const SuggestionSection = ({ registerRefresh }: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [dataMap, setDataMap] = useState<
    Partial<Record<SuggestionMsgType, SuggestionItem[]>>
  >({});
  const loadingRef = useRef<Set<SuggestionMsgType>>(new Set());
  const [activeTab, setActiveTab] = useState<
    "trend" | "community" | "top_choice"
  >("top_choice");
  const [currentPage, setCurrentPage] = useState(0);
  const flatListRef = useRef<FlatList>(null);
  const screenWidth = Dimensions.get("window").width;

  const tabs = useMemo(() => {
    return [
      {
        icon: (
          <MaterialCommunityIcons
            name="tag-heart-outline"
            size={36}
            color={theme.base.primary}
          />
        ),
        title: t("suggestion.topUnder50kTitle"),
        description: t("suggestion.topUnder50kDescription"),
        group: "top_choice" as const,
        msgType: "cheap_under_50k" as const,
      },
      {
        icon: <AntDesign name="rise" size={36} color={theme.base.success} />,
        title: t("suggestion.topGainersTitle"),
        description: t("suggestion.topGainersDescription"),
        group: "trend" as const,
        msgType: "top_gainers" as const,
      },
      {
        icon: <AntDesign name="fall" size={36} color={theme.base.error} />,
        title: t("suggestion.topDeclinersTitle"),
        description: t("suggestion.topDeclinersDescription"),
        group: "trend" as const,
        msgType: "top_decliners" as const,
      },
      {
        icon: <Entypo name="bar-graph" size={36} color={theme.base.primary} />,
        title: t("suggestion.topVolumeTitle"),
        description: t("suggestion.topVolumeDescription"),
        group: "trend" as const,
        msgType: "top_volume" as const,
      },
      {
        icon: <Feather name="search" size={36} color={theme.base.primary} />,
        title: t("suggestion.topSearchedTitle"),
        description: t("suggestion.topSearchedDescription"),
        group: "community" as const,
        msgType: "top_searched" as const,
      },
      {
        icon: (
          <MaterialCommunityIcons
            name="eye-plus-outline"
            size={36}
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

  const topChoiceStartIndex = 0;
  const trendStartIndex = topChoiceTabs.length; // = 1
  const communityStartIndex = trendStartIndex + trendTabs.length; // = 4

  // Lazy-load a single category, cached by msgType. Each tab loads once.
  const loadTab = useCallback((msgType: SuggestionMsgType) => {
    setDataMap((prev) => {
      if (prev[msgType] !== undefined || loadingRef.current.has(msgType)) {
        return prev;
      }
      loadingRef.current.add(msgType);
      getInvestingIdea(msgType, 5)
        .then((res) => {
          setDataMap((curr) => ({ ...curr, [msgType]: res?.data ?? [] }));
        })
        .finally(() => loadingRef.current.delete(msgType));
      return prev;
    });
  }, []);

  // Load whichever page is currently visible (also covers initial mount).
  useEffect(() => {
    const tab = tabs[currentPage];
    if (tab) loadTab(tab.msgType);
  }, [currentPage, loadTab, tabs]);

  // Pull-to-refresh — luôn fetch mới tab đang hiển thị và invalidate cache
  useEffect(() => {
    const refreshFn = async () => {
      const tab = tabs[currentPage];
      if (!tab) return;
      const msgType = tab.msgType;
      loadingRef.current.delete(msgType);
      // Xóa data cũ để hiện lại skeleton trong lúc fetch
      setDataMap((curr) => {
        const next = { ...curr };
        delete next[msgType];
        return next;
      });
      const res = await getInvestingIdea(msgType, 5);
      setDataMap((curr) => ({ ...curr, [msgType]: res?.data ?? [] }));
    };
    const unregister = registerRefresh?.(refreshFn);
    return () => unregister?.();
  }, [registerRefresh, currentPage, tabs]);

  const handleTabPress = (tab: "trend" | "community" | "top_choice") => {
    setActiveTab(tab);
    const targetIndex =
      tab === "trend"
        ? trendStartIndex
        : tab === "top_choice"
          ? topChoiceStartIndex
          : communityStartIndex;
    flatListRef.current?.scrollToIndex({ index: targetIndex, animated: true });
    setCurrentPage(targetIndex);
  };

  const handleScrollEnd = (e: any) => {
    const offsetX = e.nativeEvent.contentOffset.x;
    const cardWidth = screenWidth - 48 + 24;
    const page = Math.round(offsetX / cardWidth);
    setCurrentPage(page);

    if (page < trendStartIndex) {
      setActiveTab("top_choice");
    } else if (page < communityStartIndex) {
      setActiveTab("trend");
    } else {
      setActiveTab("community");
    }
  };

  // dots chỉ hiển thị theo group đang active
  const activeTabs =
    activeTab === "trend"
      ? trendTabs
      : activeTab === "top_choice"
        ? topChoiceTabs
        : communityTabs;

  const dotIndex =
    activeTab === "trend"
      ? currentPage - trendStartIndex
      : activeTab === "top_choice"
        ? currentPage - topChoiceStartIndex
        : currentPage - communityStartIndex;

  // Show the full skeleton only until the first (default) tab has loaded.
  // Latch to true once so a pull-to-refresh (which momentarily clears the
  // tab data) shows the per-card body skeleton, not the whole-section skeleton.
  const [initialLoaded, setInitialLoaded] = useState(false);
  useEffect(() => {
    if (!initialLoaded && dataMap[tabs[0].msgType] !== undefined) {
      setInitialLoaded(true);
    }
  }, [dataMap, tabs, initialLoaded]);

  return initialLoaded ? (
    <View style={{ marginHorizontal: 12 }}>
      <TouchableOpacity
        onPress={() => {
          router.push({
            pathname: "/InvestmentIdeas",
          });
        }}
        style={{
          flexDirection: "row",
          alignItems: "center",
          gap: 8,
        }}
      >
        <Text typography="titleLarge" color={theme.text.primary}>
          {t("suggestion.sectionTitle")}{" "}
        </Text>
        <View
          style={{
            height: 16,
            width: 16,
            borderRadius: 8,
            backgroundColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Entypo
            name="chevron-small-right"
            size={16}
            color={theme.text.primary}
          />
        </View>
      </TouchableOpacity>
      <LinearGradient
        colors={["#9D8CFF", "#7B5CFF", "#613DE4"]}
        useAngle
        angle={90}
        angleCenter={{ x: 0.5, y: 0.5 }}
        style={{ marginTop: 12, borderRadius: 12 }}
      >
        <ScrollView
          style={{
            marginTop: 12,
            gap: 8,
            marginLeft: 12,
          }}
          horizontal
          showsHorizontalScrollIndicator={false}
        >
          {(["top_choice", "trend", "community"] as const).map((tab) => {
            const isActive = activeTab === tab;
            const label =
              tab === "trend"
                ? t("suggestion.tabTrend")
                : tab === "top_choice"
                  ? t("suggestion.tabTopChoice")
                  : t("suggestion.tabCommunity");
            return (
              <TouchableOpacity
                key={tab}
                onPress={() => handleTabPress(tab)}
                style={{
                  paddingHorizontal: 12,
                  paddingVertical: 4,
                  borderRadius: 24,
                  backgroundColor: isActive
                    ? theme.base.primary
                    : theme.border.default,
                  marginRight: 8,
                }}
              >
                <Text
                  typography="bodyMedium"
                  color={isActive ? theme.text.onPrimary : theme.text.primary}
                >
                  {label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        <FlatList
          ref={flatListRef}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          data={tabs}
          keyExtractor={(_, index) => index.toString()}
          onMomentumScrollEnd={handleScrollEnd}
          getItemLayout={(_, index) => ({
            length: screenWidth - 48 + 24,
            offset: (screenWidth - 48 + 24) * index,
            index,
          })}
          renderItem={({ item }) => {
            const listData = dataMap[item.msgType as SuggestionMsgType];

            return (
              <View
                style={{
                  width: screenWidth - 48,
                  margin: 12,
                  borderRadius: 12,
                  backgroundColor: theme.background.surface,
                  overflow: "hidden",
                }}
              >
                {/* Card Header */}
                <View
                  style={{
                    flexDirection: "row",
                    justifyContent: "space-between",
                    alignItems: "center",
                    margin: 12,
                  }}
                >
                  <View>
                    <Text
                      typography="titleMedium"
                      color={theme.text.primary}
                      style={{ marginBottom: 4 }}
                    >
                      {item.title}
                    </Text>
                    <Text
                      typography="bodyMedium"
                      color={theme.text.primary + "88"}
                    >
                      {item.description}
                    </Text>
                  </View>
                  <View style={{ marginRight: 12 }}>{item.icon}</View>
                </View>

                {listData === undefined ? (
                  <SuggestionCardBodySkeleton />
                ) : (
                  <>
                    {/* Table */}
                    <View
                      style={{
                        marginHorizontal: 12,
                        marginBottom: 12,
                        borderRadius: 12,
                        backgroundColor: theme.background.bg,
                        overflow: "hidden",
                      }}
                    >
                      {/* Table Header */}
                      <View
                        style={{
                          flexDirection: "row",
                          alignItems: "center",
                          paddingHorizontal: 12,
                          paddingVertical: 8,
                        }}
                      >
                        <Text
                          typography="bodySmall"
                          color={theme.text.primary}
                          style={{ flex: 6.5, marginRight: 16 }}
                        >
                          {t("suggestion.columnSymbol")}
                        </Text>
                        <Text
                          typography="bodySmall"
                          color={theme.text.primary}
                          style={{
                            flex: 2,
                            textAlign: "left",
                            marginRight: 16,
                          }}
                        >
                          {t("suggestion.columnPrice")}
                        </Text>
                        <Text
                          typography="bodySmall"
                          color={theme.text.primary}
                          style={{ flex: 3.5, textAlign: "center" }}
                        >
                          {t("suggestion.columnChangeToday")}
                        </Text>
                      </View>

                      {/* Table Rows */}
                      {listData.map((stock: SuggestionItem, index: number) => {
                        const isPositive = stock.per_price_change >= 0;
                        const changeColor = isPositive ? "#22C55E" : "#EF4444";
                        const changeBg = isPositive ? "#DCFCE7" : "#FEE2E2";
                        const arrow = isPositive ? "▲" : "▼";

                        return (
                          <TouchableOpacity
                            onPress={() => {
                              router.push({
                                pathname: "/Detail",
                                params: { data: stock.symbol },
                              });
                            }}
                            key={index.toString()}
                            style={{
                              flexDirection: "row",
                              alignItems: "center",
                              paddingHorizontal: 12,
                              paddingVertical: 10,
                              borderTopWidth: 1,
                              borderTopColor: theme.border.default,
                            }}
                          >
                            {/* Logo + Symbol + Name */}
                            <View
                              style={{
                                flex: 6.5,
                                flexDirection: "row",
                                alignItems: "center",
                                gap: 12,
                                marginRight: 16,
                              }}
                            >
                              <Image
                                source={{
                                  uri:
                                    stock.logo ??
                                    "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png",
                                }}
                                style={{
                                  width: 32,
                                  height: 32,
                                  borderRadius: 8,
                                }}
                              />
                              <View style={{ flex: 2 }}>
                                <Text
                                  typography="labelLarge"
                                  color={theme.text.primary}
                                  numberOfLines={1}
                                >
                                  {stock.symbol}
                                </Text>
                                <Text
                                  typography="bodyMedium"
                                  color={theme.text.primary + "88"}
                                  numberOfLines={1}
                                >
                                  {stock.company_name}
                                </Text>
                              </View>
                            </View>

                            {/* Price */}
                            <View style={{ flex: 2, marginRight: 16 }}>
                              <Text
                                typography="labelLarge"
                                color={theme.text.primary}
                              >
                                {stock.current_price.toLocaleString("vi-VN")}
                              </Text>
                              <Text typography="bodySmall" color={changeColor}>
                                ({isPositive ? "+" : ""}
                                {stock.price_change.toLocaleString("vi-VN")})
                              </Text>
                            </View>

                            {/* % Change badge */}
                            <View style={{ flex: 3.5, alignItems: "flex-end" }}>
                              <View
                                style={{
                                  backgroundColor: changeBg,
                                  borderRadius: 4,
                                  width: "100%",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  paddingVertical: 6,
                                }}
                              >
                                <Text
                                  typography="labelLarge"
                                  color={changeColor}
                                >
                                  <Text
                                    typography="labelSmall"
                                    color={changeColor}
                                  >
                                    {arrow}
                                  </Text>
                                  {Math.abs(
                                    stock.per_price_change,
                                  ).toLocaleString("vi-VN")}
                                  %
                                </Text>
                              </View>
                            </View>
                          </TouchableOpacity>
                        );
                      })}
                    </View>

                    {/* Xem thêm */}
                    <TouchableOpacity
                      style={{
                        alignItems: "center",
                        paddingBottom: 16,
                        flexDirection: "row",
                        justifyContent: "center",
                      }}
                    >
                      <Text typography="labelLarge" color={theme.base.primary}>
                        {t("suggestion.viewMore")}
                      </Text>
                      <Entypo
                        name="chevron-right"
                        size={16}
                        color={theme.base.primary}
                      />
                    </TouchableOpacity>
                  </>
                )}
              </View>
            );
          }}
        />

        {/* Page indicator */}
        <View
          style={{
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            paddingBottom: 12,
            gap: 6,
          }}
        >
          {activeTabs.map((_, i) => {
            const isActive = i === dotIndex;
            return (
              <View
                key={i}
                style={{
                  width: isActive ? 20 : 6,
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: isActive
                    ? theme.text.onPrimary
                    : theme.border.default,
                }}
              />
            );
          })}
        </View>
      </LinearGradient>
    </View>
  ) : (
    <SuggestionSectionSkeleton />
  );
};

export default SuggestionSection;
