import React, { useCallback, useEffect, useRef, useState } from "react";
import { Animated, FlatList, TouchableOpacity, View } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { SearchBar } from "@/components/ui/SearchBar";
import SearchResultItem from "@/components/ui/SearchResultItem";
import { SearchStockItem, searchStocks } from "@/helpers/SearchHelper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { Text } from "@/components/ui/Text";
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
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [searchResults, setSearchResults] = useState<SearchStockItem[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const insets = useSafeAreaInsets();

  const onSearch = () => {
    setLoading(true);
    searchStocks(text).then((results) => {
      setSearchResults(results);
      setLoading(false);
    });
  };

  const handleSelectItem = useCallback(async (item: SearchStockItem) => {
    router.push({
      pathname: "/Detail",
      params: { data: item.symbol },
    });
  }, []);

  const handleFocus = () => setIsFocused(true);
  const handleBlur = () => setIsFocused(false);

  return (
    <View style={{ backgroundColor: theme.background.surface, flex: 1 }}>
      {/* Header */}
      <View
        style={{
          paddingRight: 12,
          paddingLeft: 12,
          backgroundColor: theme.background.bg,
          paddingTop: insets.top,
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
            onChange={(val) => {
              setText(val);
              if (val === "") setSearchResults([]);
            }}
            onSearchPress={onSearch}
            autoFocus={true}
            onFocus={handleFocus}
            onBlur={handleBlur}
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
