import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  TouchableOpacity,
  View,
  Image,
  FlatList,
  Animated,
  ActivityIndicator,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { getAllStocks, getIndustryMovement } from "@/helpers/MarketHelpers";
import { CurrentPriceData } from "@/helpers/DetailHelpers";
import { useLocalSearchParams } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";

// Sentinel value cho tab "Tất cả" (không phải tên ngành thật)
export const ALL_VALUE = "__all__";
const PAGE_SIZE = 20;

// --- Skeleton Item ---
const SkeletonItem = ({ theme }: { theme: any }) => {
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
        borderTopWidth: 1,
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
  const { t } = useLocalization();
  const { industry } = useLocalSearchParams<{ industry?: string }>();

  const categories = useMemo(
    () => [
      { label: t("home.industryAll"), value: ALL_VALUE },
      { label: t("home.industryRealEstate"), value: "Bất động sản" },
      { label: t("home.industryBanking"), value: "Ngân hàng" },
      { label: t("home.industryOilGas"), value: "Dầu khí" },
      { label: t("home.industryFood"), value: "Thực phẩm" },
      { label: t("home.industryEntertainment"), value: "Dịch vụ giải trí" },
      { label: t("home.industryIT"), value: "Công nghệ thông tin" },
      { label: t("home.industryConstruction"), value: "Xây dựng và Vật liệu" },
      { label: t("home.industryRetail"), value: "Bán lẻ" },
    ],
    [t],
  );

  // So sánh theo value (chuỗi tiếng Việt cố định), không phụ thuộc ngôn ngữ
  const initialIndex = useMemo(() => {
    if (!industry) return 0;
    const idx = categories.findIndex((c) => c.value === industry);
    return idx >= 0 ? idx : 0;
  }, [industry, categories]);

  const cache = useRef<Record<string, CurrentPriceData[]>>({});
  const categoryListRef = useRef<FlatList>(null);

  // Trạng thái phân trang riêng cho tab "Tất cả"
  const allPageRef = useRef<number>(1);
  const allTotalPagesRef = useRef<number>(1);

  const [data, setData] = useState<CurrentPriceData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [chosenIndex, setChosenIndex] = useState<number>(initialIndex);

  useEffect(() => {
    // FlatList chỉ chứa các industry (không có tab "Tất cả") → lệch index 1
    if (initialIndex > 1) {
      setTimeout(() => {
        categoryListRef.current?.scrollToIndex({
          index: initialIndex - 1,
          animated: false,
          viewPosition: 0.5,
        });
      }, 100);
    }
  }, [initialIndex]);

  useEffect(() => {
    const key = categories[chosenIndex].value;

    if (cache.current[key]) {
      setData(cache.current[key]);
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
          setData(result.data);
        }
        setLoading(false);
      });
      return;
    }

    getIndustryMovement(key).then((result) => {
      if (result?.status) {
        cache.current[key] = result.data;
        setData(result.data);
      }
      setLoading(false);
    });
  }, [categories, chosenIndex]);

  // Kéo xuống hết trang → load thêm page tiếp theo (chỉ cho tab "Tất cả")
  const handleLoadMore = () => {
    if (categories[chosenIndex].value !== ALL_VALUE) return;
    if (loading || loadingMore) return;
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
    setChosenIndex(index);
    // Chỉ scroll FlatList cho các tab industry (index >= 1); tab "Tất cả" cố định
    if (index > 0) {
      categoryListRef.current?.scrollToIndex({
        index: index - 1,
        animated: true,
        viewPosition: 0.5,
      });
    }
  };

  const renderTabButton = (
    item: { label: string; value: string },
    index: number,
  ) => (
    <TouchableOpacity
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
        <FlatList
          ref={categoryListRef}
          data={categories.slice(1)}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(_, index) => (index + 1).toString()}
          style={{ flex: 1 }}
          getItemLayout={(_, index) => ({
            length: 120,
            offset: 120 * index,
            index,
          })}
          renderItem={({ item, index }) => renderTabButton(item, index + 1)}
        />
      </View>

      {/* List */}
      {loading ? (
        <View
          style={{
            backgroundColor: theme.background.bg,
            borderRadius: 12,
            margin: 12,
            paddingHorizontal: 12,
            flex: 1,
            overflow: "hidden",
          }}
        >
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <SkeletonItem key={i} theme={theme} />
          ))}
        </View>
      ) : (
        <FlatList
          data={data}
          style={{
            backgroundColor: theme.background.bg,
            borderRadius: 12,
            margin: 12,
            paddingHorizontal: 12,
            flex: 1,
          }}
          keyExtractor={(_, index) => index.toString()}
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.5}
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
                  onPress={() => {}}
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
                      {currentPrice}
                    </Text>
                    <Text
                      typography="bodySmall"
                      color={
                        priceChange > 0
                          ? theme.base.success
                          : priceChange === 0
                            ? theme.base.warning
                            : theme.base.error
                      }
                      style={{ textAlign: "right" }}
                    >
                      {"("}
                      {priceChange > 0 ? "+" : ""}
                      {priceChange >= 0 ? priceChange : priceChange * -1}
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
                      backgroundColor:
                        perPriceChange > 0
                          ? theme.base.success + "36"
                          : perPriceChange === 0
                            ? theme.base.warning + "36"
                            : theme.base.error + "36",
                    }}
                  >
                    <Text
                      typography="labelMedium"
                      color={
                        perPriceChange > 0
                          ? theme.base.success
                          : perPriceChange === 0
                            ? theme.base.warning
                            : theme.base.error
                      }
                    >
                      <Text
                        typography="labelSmall"
                        color={
                          perPriceChange > 0
                            ? theme.base.success
                            : perPriceChange === 0
                              ? theme.base.warning
                              : theme.base.error
                        }
                      >
                        {perPriceChange > 0
                          ? "▲"
                          : perPriceChange === 0
                            ? ""
                            : "▼"}{" "}
                      </Text>
                      {perPriceChange >= 0
                        ? perPriceChange?.toFixed(2)
                        : (perPriceChange * -1).toFixed(2)}
                      %
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
