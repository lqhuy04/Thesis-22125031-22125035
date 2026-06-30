import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Animated, FlatList, TouchableOpacity, View } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { SearchBar } from "@/components/ui/SearchBar";
import SearchResultItem from "@/components/ui/SearchResultItem";
import {
  getSearchHistory,
  saveSearchHistory,
  SearchHistoryItem,
  SearchStockItem,
  searchStocks,
} from "@/helpers/SearchHelper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router, useFocusEffect } from "expo-router";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";

function chunkArray<T>(arr: T[], size: number = 3): (T | any)[][] {
  const result: (T | any)[][] = [];

  for (let i = 0; i < arr.length; i += size) {
    const chunk: (T | any)[] = arr.slice(i, i + size);

    while (chunk.length < size) {
      chunk.push({});
    }

    result.push(chunk);
  }

  return result;
}

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

const SearchResultSkeleton = ({
  opacity,
}: {
  opacity: Animated.AnimatedInterpolation<number>;
}) => {
  const { theme } = useTheme();

  return (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        paddingVertical: 12,
        gap: 12,
      }}
    >
      {/* Logo */}
      <Animated.View
        style={{
          width: 40,
          height: 40,
          borderRadius: 20,
          backgroundColor: theme.border.default,
          opacity,
        }}
      />

      {/* Symbol + tên công ty */}
      <View style={{ flex: 1, gap: 8 }}>
        <Animated.View
          style={{
            height: 14,
            width: "30%",
            borderRadius: 4,
            backgroundColor: theme.border.default,
            opacity,
          }}
        />
        <Animated.View
          style={{
            height: 11,
            width: "70%",
            borderRadius: 4,
            backgroundColor: theme.border.default,
            opacity,
          }}
        />
      </View>

      {/* Giá + badge % */}
      <View style={{ alignItems: "flex-end", gap: 6 }}>
        <Animated.View
          style={{
            height: 14,
            width: 40,
            borderRadius: 4,
            backgroundColor: theme.border.default,
            opacity,
          }}
        />
        <Animated.View
          style={{
            height: 22,
            width: 64,
            borderRadius: 4,
            backgroundColor: theme.border.default,
            opacity,
          }}
        />
      </View>
    </View>
  );
};

const SearchHistorySkeleton = () => {
  const { theme } = useTheme();
  const opacity = useShimmer();

  return (
    <View>
      <View
        style={{
          flexWrap: "wrap",
          flexDirection: "row",
          marginHorizontal: 12,
          gap: 8,
          marginTop: 12,
        }}
      >
        {Array.from({ length: 3 }).map((_, i) => (
          <Animated.View
            key={i}
            style={{
              flex: 1,
              minWidth: 0,
              height: 52,
              borderRadius: 8,
              backgroundColor: theme.background.bg,
              opacity,
            }}
          />
        ))}
      </View>
      <View
        style={{
          flexWrap: "wrap",
          flexDirection: "row",
          marginHorizontal: 12,
          gap: 8,
          marginTop: 12,
        }}
      >
        {Array.from({ length: 3 }).map((_, i) => (
          <Animated.View
            key={i}
            style={{
              flex: 1,
              minWidth: 0,
              height: 52,
              borderRadius: 8,
              backgroundColor: theme.background.bg,
              opacity,
            }}
          />
        ))}
      </View>
    </View>
  );
};

const SearchResultSkeletonList = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const opacity = useShimmer();

  return (
    <View>
      <Text
        typography="titleMedium"
        color={theme.text.primary}
        style={{ marginLeft: 12, marginTop: 12 }}
      >
        {t("market.searchResult")}
      </Text>

      <View
        style={{
          marginTop: 12,
          marginBottom: 24,
          borderRadius: 12,
          backgroundColor: theme.background.bg,
          paddingHorizontal: 16,
          marginHorizontal: 12,
        }}
      >
        {Array.from({ length: 10 }).map((_, i) => (
          <View key={i}>
            {i !== 0 && (
              <View
                style={{ height: 1, backgroundColor: theme.border.default }}
              />
            )}
            <SearchResultSkeleton opacity={opacity} />
          </View>
        ))}
      </View>
    </View>
  );
};

const Search = () => {
  const { t } = useLocalization();
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [text, setText] = useState("");
  const [searchResults, setSearchResults] = useState<SearchStockItem[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);

  // Khoá điều hướng để tránh push nhiều trang Detail khi bấm nhanh nhiều lần
  const isNavigatingRef = useRef(false);

  const showHistory = useMemo(() => {
    return searchResults.length === 0 && !text;
  }, [searchResults.length, text]);

  useFocusEffect(
    useCallback(() => {
      // Mở khoá điều hướng mỗi khi màn hình được focus lại (vd: quay về từ Detail)
      isNavigatingRef.current = false;
      setHistoryLoading(true);
      getSearchHistory().then((history) => {
        setSearchHistory(history);
        setHistoryLoading(false);
      });
    }, []),
  );

  const distributedHistories = chunkArray(searchHistory, 3);

  const onSearch = useCallback((keyword: string) => {
    const query = keyword.trim();
    if (query === "") {
      setSearchResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    searchStocks(query).then((results) => {
      setSearchResults(results);
      setLoading(false);
    });
  }, []);

  // Vừa gõ vừa search: debounce 400ms sau lần gõ cuối mới gọi API
  useEffect(() => {
    if (text.trim() === "") {
      setSearchResults([]);
      setLoading(false);
      return;
    }

    const handler = setTimeout(() => {
      onSearch(text);
    }, 400);

    return () => clearTimeout(handler);
  }, [text, onSearch]);

  const goToStock = useCallback(
    async (symbol: string) => {
      // Chỉ cho phép điều hướng một lần; bấm trùng sẽ bị bỏ qua
      if (isNavigatingRef.current) return;
      isNavigatingRef.current = true;

      await saveSearchHistory(symbol);
      router.push({
        pathname: "/Detail",
        params: { data: symbol },
      });
    },
    [],
  );

  const handleSelectItem = useCallback(
    (item: SearchStockItem) => goToStock(item.symbol),
    [goToStock],
  );

  return (
    <View style={{ backgroundColor: theme.background.surface, flex: 1 }}>
      {/* Header */}
      <View
        style={{
          paddingRight: 12,
          paddingLeft: 12,
          backgroundColor: theme.background.bg,
          paddingTop: insets.top + 12,
          paddingBottom: 12,
          flexDirection: "row",
          alignItems: "center",
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.08,
          shadowRadius: 4,
          elevation: 4,
        }}
      >
        <View style={{ flex: 1 }}>
          <SearchBar
            value={text}
            onChange={setText}
            onSearchPress={() => onSearch(text)}
            autoFocus={true}
          />
        </View>

        <TouchableOpacity
          onPress={() => router.dismiss()}
          style={{ marginLeft: 20, marginRight: 8 }}
        >
          <Text typography="titleMedium" color={theme.text.primary}>
            {t("common.cancel")}
          </Text>
        </TouchableOpacity>
      </View>

      {showHistory &&
        (historyLoading ? (
          <>
            <Text
              typography="titleMedium"
              color={theme.text.primary}
              style={{ marginLeft: 12, marginTop: 12 }}
            >
              {t("common.searchHistory")}
            </Text>
            <SearchHistorySkeleton />
          </>
        ) : (
          <View>
            <Text
              typography="titleMedium"
              color={theme.text.primary}
              style={{ marginLeft: 12, marginTop: 12 }}
            >
              {t("common.searchHistory")}
            </Text>

            <View>
              {distributedHistories.map((item, index) => (
                <View
                  key={index.toString()}
                  style={{
                    flexWrap: "wrap",
                    flexDirection: "row",
                    marginHorizontal: 12,
                    marginTop: 12,
                    gap: 8,
                  }}
                >
                  {item.map((subItem, subIndex) =>
                    subItem?.symbol != null ? (
                      <TouchableOpacity
                        onPress={() => goToStock(subItem?.symbol)}
                        key={subIndex.toString() + index.toString()}
                        style={{
                          backgroundColor: theme.background.bg,
                          padding: 10,
                          borderRadius: 8,
                          flex: 1,
                        }}
                      >
                        <Text
                          color={theme.text.primary}
                          typography="titleSmall"
                          style={{ marginBottom: 4 }}
                        >
                          {subItem?.symbol}
                        </Text>

                        <Text
                          color={
                            subItem?.per_price_change > 0
                              ? theme.base.success
                              : subItem?.per_price_change < 0
                                ? theme.base.error
                                : theme.base.warning
                          }
                          typography="bodySmall"
                        >
                          {subItem?.current_price?.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}{" "}
                          {subItem?.per_price_change >= 0 ? "+" : ""}
                          {subItem?.per_price_change?.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%
                        </Text>
                      </TouchableOpacity>
                    ) : (
                      <TouchableOpacity
                        key={subIndex.toString() + index.toString()}
                        style={{
                          padding: 10,
                          borderRadius: 8,
                          flex: 1,
                        }}
                      ></TouchableOpacity>
                    ),
                  )}
                </View>
              ))}
            </View>
          </View>
        ))}

      {loading ? (
        <SearchResultSkeletonList />
      ) : searchResults.length !== 0 ? (
        <View>
          <Text
            typography="titleMedium"
            color={theme.text.primary}
            style={{ marginLeft: 12, marginTop: 12 }}
          >
            {t("market.searchResult")}
          </Text>

          <FlatList
            data={searchResults}
            keyExtractor={(item) => item.symbol}
            renderItem={({ item, index }) => (
              <View>
                {index !== 0 && (
                  <View
                    style={{
                      height: 1,
                      backgroundColor: theme.border.default,
                      width: "100%",
                    }}
                  />
                )}
                <SearchResultItem
                  item={item}
                  onPress={() => handleSelectItem(item)}
                />
              </View>
            )}
            style={{
              marginTop: 12,
              marginBottom: 24,
              borderRadius: 12,
              backgroundColor: theme.background.bg,
              paddingHorizontal: 16,
              marginHorizontal: 12,
            }}
          />
        </View>
      ) : null}
    </View>
  );
};

export default Search;
