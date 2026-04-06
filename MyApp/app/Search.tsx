import React, { useState } from "react";
import { ActivityIndicator, FlatList, View } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { SearchBar } from "@/components/ui/SearchBar";
import SearchResultItem from "@/components/ui/SearchResultItem";
import { SearchStockItem, searchStocks } from "@/helpers/SearchHelper";
import { SafeAreaView } from "react-native-safe-area-context";

const Search = () => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [searchResults, setSearchResults] = useState<SearchStockItem[]>([]);

  const onSearch = () => {
    setLoading(true);
    searchStocks(text).then((results) => {
      setSearchResults(results);
      setLoading(false);
    });
  };

  return (
    <SafeAreaView
      style={{
        paddingHorizontal: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
      }}
    >
      <SearchBar value={text} onChange={setText} onSearchPress={onSearch} />

      {loading ? (
        <View
          style={{
            flex: 1,
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <ActivityIndicator size="large" color={theme.base.primary} />
        </View>
      ) : (
        <FlatList
          data={searchResults}
          keyExtractor={(item) => item.symbol}
          renderItem={({ item }) => <SearchResultItem item={item} />}
        />
      )}
    </SafeAreaView>
  );
};

export default Search;
