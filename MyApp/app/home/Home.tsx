import React, { useState } from "react";
import { FlatList, View, Text} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { SearchBar } from "@/components/ui/SearchBar";
import SearchResultItem from "@/components/ui/SearchResultItem";
import { SearchStockItem, searchStocks } from "@/helpers/SearchHelper";

const Home = () => {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [text, setText] = React.useState("");
  const [searchResults, setSearchResults] = useState<SearchStockItem[]>([]);

  const onSearch = () => {
    setLoading(true);
    searchStocks(text).then((results) => {
      setSearchResults(results);
      setLoading(false);
    });
  };
  return (
    <View
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
        paddingTop: 12,
      }}
    >
      <SearchBar value={text} onChange={setText} onSearchPress={onSearch} />

      {loading ? (
        <Text>Searching...</Text>
      ) : (
        <FlatList
          data={searchResults}
          keyExtractor={(item) => item.symbol}
          renderItem={({ item }) => <SearchResultItem item={item} />}
        />
      )}
    </View>
  );
};

export default Home;
