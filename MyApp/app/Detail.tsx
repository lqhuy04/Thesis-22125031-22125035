import StockCandleChart from "@/components/ui/CandleChart";
import { useLocalSearchParams } from "expo-router";
import React from "react";
import { Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

const Detail = () => {
  const { data } = useLocalSearchParams() || {};
  const item = data ? JSON.parse(data as string) : null;

  return (
    <SafeAreaView>
      <StockCandleChart />
      <Text>Detail Screen</Text>
    </SafeAreaView>
  );
};

export default Detail;
