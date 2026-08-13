import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  TouchableOpacity,
  View,
  Image,
  FlatList,
  ScrollView,
  Animated,
  ActivityIndicator,
  LayoutChangeEvent,
  RefreshControl,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { getAllStocks, getIndustryMovement } from "@/helpers/MarketHelpers";
import { CurrentPriceData } from "@/helpers/DetailHelpers";
import { router, useLocalSearchParams } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  formatPercentageChange,
  formatPriceChange,
  getStockChangeColor,
} from "@/helpers/stockChange";

// Sentinel value cho tab "Tất cả" (không phải industry id thật)
export const ALL_VALUE = "__all__";
const PAGE_SIZE = 20;

// --- Skeleton Item ---
const SkeletonItem = ({ theme, index }: { theme: any; index: number }) => {
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacity]);

  const bg = theme.border.default;

  return (
    <Animated.View
      style={{
        opacity,
        paddingHorizontal: 16,
        paddingVertical: 16,
        flexDirection: "row",
        alignItems: "center",
        borderTopWidth: index === 0 ? 0 : 1,
        borderTopColor: theme.border.default,
      }}
    >
      <View
        style={{
          width: 40,
          height: 40,
          borderRadius: 2,
          backgroundColor: bg,
          marginRight: 8,
        }}
      />
      <View style={{ flex: 1, marginRight: 12, gap: 6 }}>
        <View
          style={{
            width: 48,
            height: 14,
            borderRadius: 4,
            backgroundColor: bg,
          }}
        />
        <View
          style={{
            width: 120,
            height: 11,
            borderRadius: 4,
            backgroundColor: bg,
          }}
        />
      </View>
      <View style={{ alignItems: "flex-end", marginRight: 12, gap: 6 }}>
        <View
          style={{
            width: 52,
            height: 14,
            borderRadius: 4,
            backgroundColor: bg,
          }}
        />
        <View
          style={{
            width: 36,
            height: 11,
            borderRadius: 4,
            backgroundColor: bg,
          }}
        />
      </View>
      <View
        style={{ width: 70, height: 34, borderRadius: 4, backgroundColor: bg }}
      />
    </Animated.View>
  );
};

// --- Main Screen ---
const IndustryMovement = () => {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const { t } = useLocalization();
  const { industryId } = useLocalSearchParams<{ industryId?: string }>();

  const categories = useMemo(
    () => [
      { label: t("home.industryAll"), value: ALL_VALUE },
      { label: t("home.industryOilGas"), value: "0500" },
      { label: t("home.industryChemicals"), value: "1300" },
      { label: t("home.industryBasicResources"), value: "1700" },
      { label: t("home.industryConstruction"), value: "2300" },
      { label: t("home.industryIndustrialGoods"), value: "2700" },
      { label: t("home.industryAutomobiles"), value: "3300" },
      { label: t("home.industryFoodBeverage"), value: "3500" },
      { label: t("home.industryPersonalHousehold"), value: "3700" },
      { label: t("home.industryHealthcare"), value: "4500" },
      { label: t("home.industryRetail"), value: "5300" },
      { label: t("home.industryMedia"), value: "5500" },
      { label: t("home.industryTravelLeisure"), value: "5700" },
      { label: t("home.industryTelecom"), value: "6500" },
      { label: t("home.industryUtilities"), value: "7500" },
      { label: t("home.industryBanks"), value: "8300" },
      { label: t("home.industryInsurance"), value: "8500" },
      { label: t("home.industryRealEstate"), value: "8600" },
      { label: t("home.industryFinancialServices"), value: "8700" },
      { label: t("home.industryInvestment"), value: "8900" },
      { label: t("home.industryTechnology"), value: "9500" },
    ],
    [t],
  );

  // So sánh theo industry id (cố định), không phụ thuộc ngôn ngữ
  const initialIndex = useMemo(() => {
    if (!industryId) return 0;
    const idx = categories.findIndex((c) => c.value === industryId);
    return idx >= 0 ? idx : 0;
  }, [industryId, categories]);

  const cache = useRef<Record<string, CurrentPriceData[]>>({});
  const activeCategoryKeyRef = useRef(
    categories[initialIndex]?.value ?? ALL_VALUE,
  );
  const refreshingRef = useRef(false);
  const categoryListRef = useRef<ScrollView>(null);
  const categoryLayoutsRef = useRef<
    Record<number, { x: number; width: number }>
  >({});
  const categoryViewportWidthRef = useRef(0);
  const initialCategoryScrolledRef = useRef(false);

  // Trạng thái phân trang riêng cho tab "Tất cả"
  const allPageRef = useRef<number>(1);
  const allTotalPagesRef = useRef<number>(1);

  const [data, setData] = useState<CurrentPriceData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState(false);
  const [chosenIndex, setChosenIndex] = useState<number>(initialIndex);

  const scrollToCategory = useCallback((index: number, animated: boolean) => {
    if (index <= 0) return true;

    const layout = categoryLayoutsRef.current[index];
    const viewportWidth = categoryViewportWidthRef.current;

    if (!layout || viewportWidth === 0) return false;

    categoryListRef.current?.scrollTo({
      x: Math.max(0, layout.x - (viewportWidth - layout.width) / 2),
      y: 0,
      animated,
    });
    return true;
  }, []);

  useEffect(() => {
    setChosenIndex(initialIndex);
    initialCategoryScrolledRef.current = false;

    const frame = requestAnimationFrame(() => {
      initialCategoryScrolledRef.current = scrollToCategory(
        initialIndex,
        false,
      );
    });

    return () => cancelAnimationFrame(frame);
  }, [initialIndex, scrollToCategory]);

  useEffect(() => {
    const key = categories[chosenIndex].value;
    activeCategoryKeyRef.current = key;

    if (cache.current[key]) {
      setData(cache.current[key]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setData([]);

    if (key === ALL_VALUE) {
      allPageRef.current = 1;
      allTotalPagesRef.current = 1;

      getAllStocks(1, PAGE_SIZE).then((result) => {
        if (result.status) {
          cache.current[key] = result.data;
          allPageRef.current = result.page;
          allTotalPagesRef.current = result.totalPages;
          if (activeCategoryKeyRef.current === key) {
            setData(result.data);
          }
        }
        if (activeCategoryKeyRef.current === key) {
          setLoading(false);
        }
      });
      return;
    }

    getIndustryMovement(key).then((result) => {
      if (result?.status) {
        cache.current[key] = result.data;
        if (activeCategoryKeyRef.current === key) {
          setData(result.data);
        }
      }
      if (activeCategoryKeyRef.current === key) {
        setLoading(false);
      }
    });
  }, [categories, chosenIndex]);

  const handleRefresh = useCallback(async () => {
    if (refreshingRef.current) return;

    const key = categories[chosenIndex].value;
    refreshingRef.current = true;
    setRefreshing(true);

    try {
      if (key === ALL_VALUE) {
        const result = await getAllStocks(1, PAGE_SIZE);
        if (result.status) {
          cache.current[key] = result.data;
          allPageRef.current = result.page;
          allTotalPagesRef.current = result.totalPages;
          if (activeCategoryKeyRef.current === key) {
            setData(result.data);
          }
        }
        return;
      }

      const result = await getIndustryMovement(key);
      if (result.status) {
        cache.current[key] = result.data;
        if (activeCategoryKeyRef.current === key) {
          setData(result.data);
        }
      }
    } finally {
      refreshingRef.current = false;
      setRefreshing(false);
    }
  }, [categories, chosenIndex]);

  // Kéo xuống hết trang → load thêm page tiếp theo (chỉ cho tab "Tất cả")
  const handleLoadMore = () => {
    if (categories[chosenIndex].value !== ALL_VALUE) return;
    if (loading || loadingMore || refreshingRef.current) return;
    if (allPageRef.current >= allTotalPagesRef.current) return;

    const nextPage = allPageRef.current + 1;
    setLoadingMore(true);

    getAllStocks(nextPage, PAGE_SIZE).then((result) => {
      if (result.status && result.data.length > 0) {
        allPageRef.current = result.page;
        allTotalPagesRef.current = result.totalPages;
        setData((prev) => {
          const merged = [...prev, ...result.data];
          cache.current[ALL_VALUE] = merged;
          return merged;
        });
      }
      setLoadingMore(false);
    });
  };

  const handleTabPress = (index: number) => {
    activeCategoryKeyRef.current = categories[index].value;
    setChosenIndex(index);
    scrollToCategory(index, true);
  };

  const renderTabButton = (
    item: { label: string; value: string },
    index: number,
    onLayout?: (event: LayoutChangeEvent) => void,
  ) => (
    <TouchableOpacity
      key={item.value}
      onLayout={onLayout}
      style={{
        backgroundColor:
          chosenIndex === index ? theme.base.primary : theme.border.default,
        paddingHorizontal: 12,
        height: 32,
        borderRadius: 16,
        marginRight: 12,
        alignItems: "center",
        justifyContent: "center",
      }}
      onPress={() => handleTabPress(index)}
    >
      <Text
        typography="labelLarge"
        color={
          chosenIndex === index ? theme.text.onPrimary : theme.text.primary
        }
      >
        {" "}
        {item.label}{" "}
      </Text>
    </TouchableOpacity>
  );

  const SKELETON_COUNT = 8;

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={categories[chosenIndex].label} />

      {/* Category tabs */}
      <View
        style={{
          backgroundColor: theme.background.bg,
          flexDirection: "row",
          alignItems: "center",
          maxHeight: 48,
          paddingLeft: 12,
          paddingVertical: 8,
        }}
      >
        {/* Tab "Tất cả" cố định */}
        {renderTabButton(categories[0], 0)}

        {/* Divider dọc */}
        <View
          style={{
            width: 1,
            height: 24,
            backgroundColor: theme.border.default,
            marginRight: 12,
          }}
        />

        {/* Các tab industry có thể scroll */}
        <ScrollView
          ref={categoryListRef}
          horizontal
          showsHorizontalScrollIndicator={false}
          style={{ flex: 1 }}
          contentContainerStyle={{ paddingRight: 12 }}
          onLayout={(event) => {
            categoryViewportWidthRef.current = event.nativeEvent.layout.width;

            if (!initialCategoryScrolledRef.current) {
              initialCategoryScrolledRef.current = scrollToCategory(
                initialIndex,
                false,
              );
            }
          }}
        >
          {categories.slice(1).map((item, index) => {
            const categoryIndex = index + 1;

            return renderTabButton(item, categoryIndex, (event) => {
              const { x, width } = event.nativeEvent.layout;
              categoryLayoutsRef.current[categoryIndex] = { x, width };

              if (
                categoryIndex === initialIndex &&
                !initialCategoryScrolledRef.current
              ) {
                initialCategoryScrolledRef.current = scrollToCategory(
                  initialIndex,
                  false,
                );
              }
            });
          })}
        </ScrollView>
      </View>

      {/* List */}
      {loading ? (
        <View
          style={{
            backgroundColor: theme.background.bg,
            borderRadius: 12,
            margin: 12,
            paddingHorizontal: 12,
            flexGrow: 0,
            flexShrink: 1,
            overflow: "hidden",
            marginBottom: insets.bottom + 12,
          }}
        >
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <SkeletonItem key={i} theme={theme} index={i} />
          ))}
        </View>
      ) : (
        <FlatList
          data={data}
          alwaysBounceVertical
          overScrollMode="always"
          style={{
            backgroundColor: theme.background.bg,
            borderRadius: 12,
            margin: 12,
            paddingHorizontal: 12,
            flexGrow: 0,
            flexShrink: 1,
            marginBottom: insets.bottom + 12,
          }}
          keyExtractor={(_, index) => index.toString()}
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.5}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              colors={[theme.base.primary]}
              tintColor={theme.base.primary}
              progressBackgroundColor={theme.background.bg}
            />
          }
          ListFooterComponent={
            loadingMore ? (
              <View style={{ paddingVertical: 16 }}>
                <ActivityIndicator color={theme.base.primary} />
              </View>
            ) : null
          }
          showsVerticalScrollIndicator={false}
          renderItem={({ item, index }) => {
            const currentPrice = item.CurrentPrice;
            const priceChange = item.PriceChange;
            const perPriceChange = item.PerPriceChange;
            const priceChangeColor = getStockChangeColor(
              priceChange,
              theme.base,
            );
            const perPriceChangeColor = getStockChangeColor(
              perPriceChange,
              theme.base,
            );

            return (
              <>
                {index !== 0 ? (
                  <View
                    style={{
                      width: "100%",
                      height: 1,
                      backgroundColor: theme.border.default,
                    }}
                  />
                ) : null}
                <TouchableOpacity
                  onPress={() =>
                    router.push({
                      pathname: "/Detail",
                      params: { data: item.symbol },
                    })
                  }
                  style={{
                    paddingVertical: 16,
                    backgroundColor: theme.background.bg,
                    borderRadius: 12,
                    flexDirection: "row",
                    alignItems: "center",
                  }}
                >
                  <Image
                    source={{
                      uri:
                        item.logo ||
                        "https://ddazflrupjwuxlxlszbk.supabase.co/storage/v1/object/public/icons/office.png",
                    }}
                    style={{
                      marginRight: 8,
                      width: 40,
                      height: 40,
                      borderRadius: 2,
                    }}
                  />

                  <View style={{ flex: 1, marginRight: 12 }}>
                    <Text typography="labelLarge" color={theme.text.primary}>
                      {item.symbol}
                    </Text>
                    <Text
                      typography="bodySmall"
                      color={theme.text.primary}
                      numberOfLines={1}
                    >
                      {item.company_name}
                    </Text>
                  </View>

                  <View style={{ alignItems: "flex-start", marginRight: 4 }}>
                    <Text typography="labelLarge" color={theme.text.primary}>
                      {currentPrice.toLocaleString("vi-VN", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </Text>
                    <Text
                      typography="bodySmall"
                      color={priceChangeColor}
                      style={{ textAlign: "right" }}
                    >
                      {"("}
                      {formatPriceChange(priceChange)}
                      {")"}
                    </Text>
                  </View>

                  <View
                    style={{
                      marginLeft: 8,
                      borderRadius: 4,
                      width: 70,
                      paddingVertical: 6,
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: perPriceChangeColor + "36",
                    }}
                  >
                    <Text
                      typography="labelMedium"
                      color={perPriceChangeColor}
                    >
                      {formatPercentageChange(perPriceChange)}
                    </Text>
                  </View>
                </TouchableOpacity>
              </>
            );
          }}
        />
      )}
    </View>
  );
};

export default IndustryMovement;
