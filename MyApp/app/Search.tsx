import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  FlatList,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { SearchBar } from "@/components/ui/SearchBar";
import SearchResultItem from "@/components/ui/SearchResultItem";
import {
  addToSearchHistory,
  clearSearchHistory,
  getSearchHistory,
  removeFromSearchHistory,
  SearchStockItem,
  searchStocks,
} from "@/helpers/SearchHelper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { router } from "expo-router";

const CHEVRON_WIDTH = 32;

const Search = () => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [searchResults, setSearchResults] = useState<SearchStockItem[]>([]);
  const [history, setHistory] = useState<SearchStockItem[]>([]);
  const [isFocused, setIsFocused] = useState(false);
  const slideAnim = useRef(new Animated.Value(CHEVRON_WIDTH)).current;
  const insets = useSafeAreaInsets();

  useEffect(() => {
    getSearchHistory().then(setHistory);
  }, []);

  const onSearch = () => {
    setLoading(true);
    searchStocks(text).then((results) => {
      setSearchResults(results);
      setLoading(false);
    });
  };

  const handleSelectItem = useCallback(async (item: SearchStockItem) => {
    await addToSearchHistory(item);
    setHistory(await getSearchHistory());
    router.push({
      pathname: "/Detail",
      params: { data: item.symbol },
    });
  }, []);

  const handleRemoveHistory = useCallback(async (symbol: string) => {
    await removeFromSearchHistory(symbol);
    setHistory(await getSearchHistory());
  }, []);

  const handleClearHistory = useCallback(async () => {
    await clearSearchHistory();
    setHistory([]);
  }, []);

  const handleFocus = () => {
    setIsFocused(true);
    Animated.timing(slideAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const handleBlur = () => {
    setIsFocused(false);
    Animated.timing(slideAnim, {
      toValue: CHEVRON_WIDTH,
      duration: 200,
      useNativeDriver: false,
    }).start();
  };

  const showHistory = isFocused && searchResults.length === 0 && !text;

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
        <Animated.View style={{ width: slideAnim, overflow: "hidden" }}>
          <TouchableOpacity onPress={() => router.dismiss()}>
            <MaterialIcons
              name="chevron-left"
              size={24}
              color={theme.text.primary}
            />
          </TouchableOpacity>
        </Animated.View>

        <View style={{ flex: 1 }}>
          <SearchBar
            value={text}
            onChange={(val) => {
              setText(val);
              if (val === "") {
                setSearchResults([]);
              }
            }}
            onSearchPress={onSearch}
            autoFocus={true}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />
        </View>
      </View>

      {/* Lịch sử tìm kiếm */}
      {showHistory && history.length > 0 && (
        <View style={{ marginTop: 8 }}>
          <View
            style={{
              flexDirection: "row",
              justifyContent: "space-between",
              alignItems: "center",
              paddingHorizontal: 16,
              paddingVertical: 8,
            }}
          >
            <Text
              style={{ color: theme.text.primary + "88", fontWeight: "600" }}
            >
              Tìm kiếm gần đây
            </Text>
            <TouchableOpacity onPress={handleClearHistory}>
              <Text
                style={{
                  color: theme.base.primary,
                  fontSize: 13,
                  fontWeight: "500",
                }}
              >
                Xoá tất cả
              </Text>
            </TouchableOpacity>
          </View>

          <FlatList
            keyboardShouldPersistTaps="handled"
            data={history}
            keyExtractor={(item) => item.symbol}
            renderItem={({ item }) => (
              <TouchableOpacity
                onPress={() => handleSelectItem(item)}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  paddingHorizontal: 16,
                  paddingVertical: 10,
                }}
              >
                <View
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <MaterialIcons
                    name="history"
                    size={18}
                    color={theme.text.primary + "88"}
                  />
                  <View>
                    <Text
                      style={{ color: theme.text.primary, fontWeight: "600" }}
                    >
                      {item.symbol}
                    </Text>
                    <Text
                      style={{ color: theme.text.primary + "88", fontSize: 12 }}
                    >
                      {item.company_name}
                    </Text>
                  </View>
                </View>
                <TouchableOpacity
                  onPress={() => handleRemoveHistory(item.symbol)}
                >
                  <MaterialIcons
                    name="close"
                    size={18}
                    color={theme.text.primary + "88"}
                  />
                </TouchableOpacity>
              </TouchableOpacity>
            )}
          />
        </View>
      )}

      {/* Kết quả tìm kiếm */}
      {loading ? (
        <View
          style={{ flex: 1, justifyContent: "center", alignItems: "center" }}
        >
          <ActivityIndicator size="large" color={theme.base.primary} />
        </View>
      ) : (
        !showHistory && (
          <FlatList
            data={searchResults}
            keyExtractor={(item) => item.symbol}
            renderItem={({ item }) => (
              <SearchResultItem
                item={item}
                onPress={() => handleSelectItem(item)}
              />
            )}
            style={{ marginTop: 8, marginBottom: 24 }}
          />
        )
      )}
    </View>
  );
};

export default Search;
