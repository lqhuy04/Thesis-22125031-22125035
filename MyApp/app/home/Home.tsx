import React from "react";
import { FlatList, View } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { SearchBar } from "@/components/ui/SearchBar";
import { SearchStockItem } from "@/models";
import SearchResultItem from "@/components/ui/SearchResultItem";

const Home = () => {
  const { theme } = useTheme();

  const [text, setText] = React.useState("");

  const mockData: SearchStockItem[] = [
    {
      code: "AAPL",
      name: "Apple Inc.",
      difference: 1.25,
      currentPrice: 150.75,
      logoUrl: "",
    },
    {
      code: "GOOGL",
      name: "Alphabet Inc.",
      difference: -0.85,
      currentPrice: 2800.5,
      logoUrl: "",
    },
    {
      code: "AMZN",
      name: "Amazon.com, Inc.",

      difference: 0.45,
      currentPrice: 3400.2,
      logoUrl: "",
    },
  ];

  return (
    <View
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
        paddingTop: 12,
      }}
    >
      <SearchBar value={text} onChange={setText} />

      <FlatList
        data={mockData}
        keyExtractor={(item) => item.code}
        renderItem={({ item }) => <SearchResultItem item={item} />}
      />
    </View>
  );
};

export default Home;
