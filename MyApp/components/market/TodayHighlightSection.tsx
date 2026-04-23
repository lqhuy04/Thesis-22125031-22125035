import React, { useEffect, useRef, useState } from "react";
import {
  Dimensions,
  FlatList,
  NativeScrollEvent,
  NativeSyntheticEvent,
  View,
} from "react-native";
import { Text } from "../ui/Text";
import { getTodayHighlights, TodayHighlight } from "@/helpers/MarketHelpers";
import TodayHighlightCard from "../ui/TodayHighlightCard";
import { useTheme } from "@/hooks/ThemeContext";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const ITEM_WIDTH = SCREEN_WIDTH - 24;
const ITEM_MARGIN = 12;
const SNAP_INTERVAL = ITEM_WIDTH + ITEM_MARGIN;

const TodayHighlightSection = () => {
  const [data, setData] = useState<TodayHighlight[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);
  const { theme } = useTheme();

  useEffect(() => {
    getTodayHighlights().then((result) => {
      if (result.status) {
        setData(result.data);
      }
    });
  }, []);

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    const index = Math.round(offsetX / SNAP_INTERVAL);
    setActiveIndex(index);
  };

  return (
    <View style={{ marginTop: 12 }}>
      <Text typography="titleLarge">{"Tiêu điểm hôm nay"}</Text>

      <FlatList
        ref={flatListRef}
        horizontal
        showsHorizontalScrollIndicator={false}
        data={data}
        keyExtractor={(item) => item.stock_id}
        renderItem={({ item }) => <TodayHighlightCard item={item} />}
        style={{ marginTop: 12 }}
        // Carousel config
        snapToInterval={SNAP_INTERVAL}
        snapToAlignment="start"
        decelerationRate="fast"
        onScroll={onScroll}
        scrollEventThrottle={16}
        contentContainerStyle={{ paddingRight: ITEM_MARGIN }}
      />

      {/* Pagination Dots */}
      {data.length > 1 && (
        <View
          style={{
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            marginTop: 10,
            gap: 6,
          }}
        >
          {data.map((_, index) => (
            <View
              key={index}
              style={{
                width: activeIndex === index ? 16 : 6,
                height: 6,
                borderRadius: 3,
                backgroundColor:
                  activeIndex === index
                    ? theme.base.primary
                    : theme.base.primary + "40",
              }}
            />
          ))}
        </View>
      )}
    </View>
  );
};

export default TodayHighlightSection;
