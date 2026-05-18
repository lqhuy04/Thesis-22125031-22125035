import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ScrollView,
  TouchableOpacity,
  View,
  Image,
  FlatList,
  Animated,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Text } from "@/components/ui/Text";
import { getIndustryMovement } from "@/helpers/MarketHelpers";
import { CurrentPriceData } from "@/helpers/DetailHelpers";

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
      {/* Logo placeholder */}
      <View
        style={{
          width: 40,
          height: 40,
          borderRadius: 2,
          backgroundColor: bg,
          marginRight: 8,
        }}
      />

      {/* Text placeholder */}
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

      {/* Price placeholder */}
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

      {/* Badge placeholder */}
      <View
        style={{
          width: 70,
          height: 34,
          borderRadius: 4,
          backgroundColor: bg,
        }}
      />
    </Animated.View>
  );
};

// --- Main Screen ---
const IndustryMovement = () => {
  const { theme } = useTheme();

  const categories = useMemo(
    () => [
      "Bất động sản",
      "Ngân hàng",
      "Dầu khí",
      "Thực phẩm",
      "Dịch vụ giải trí",
      "Công nghệ thông tin",
      "Xây dựng và Vật liệu",
      "Bán lẻ",
    ],
    [],
  );

  // Cache: Record<categoryName, CurrentPriceData[]>
  const cache = useRef<Record<string, CurrentPriceData[]>>({});

  const [data, setData] = useState<CurrentPriceData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [chosenIndex, setChosenIndex] = useState<number>(0);

  useEffect(() => {
    const key = categories[chosenIndex];

    // Cache hit: render immediately, no fetch
    if (cache.current[key]) {
      setData(cache.current[key]);
      return;
    }

    // Cache miss: fetch then store
    setLoading(true);
    setData([]); // clear stale data while loading

    getIndustryMovement(key).then((result) => {
      if (result?.status) {
        cache.current[key] = result.data; // store in cache
        setData(result.data);
      }
      setLoading(false);
    });
  }, [categories, chosenIndex]);

  const SKELETON_COUNT = 8;

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title="Diễn biến nhóm ngành" />

      {/* Category tabs */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{
          flexDirection: "row",
          backgroundColor: theme.background.primarySurface,
          paddingHorizontal: 12,
          paddingVertical: 8,
          maxHeight: 48,
        }}
      >
        {categories.map((item, index) => (
          <TouchableOpacity
            key={index.toString()}
            style={{
              backgroundColor:
                chosenIndex === index
                  ? theme.background.bg
                  : theme.background.surface,
              borderWidth: 2,
              borderColor:
                chosenIndex === index
                  ? theme.base.primary
                  : theme.background.surface,
              paddingVertical: 4,
              paddingHorizontal: 6,
              borderRadius: 16,
              marginRight: 8,
            }}
            onPress={() => setChosenIndex(index)}
          >
            <Text
              typography="labelLarge"
              color={
                chosenIndex === index ? theme.base.primary : theme.text.primary
              }
            >
              {" "}
              {item}{" "}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* List */}
      {loading ? (
        // Skeleton loading state
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
          renderItem={({ item, index }) => {
            const currentPrice = item.CurrentPrice;
            const priceChange = item.PriceChange;
            const perPriceChange = item.PerPriceChange;

            return (
              <TouchableOpacity
                onPress={() => {}}
                style={{
                  paddingHorizontal: 16,
                  paddingVertical: 16,
                  backgroundColor: theme.background.bg,
                  borderRadius: 12,
                  flexDirection: "row",
                  alignItems: "center",
                  borderTopWidth: index === 0 ? 0 : 1,
                  borderTopColor: theme.border.default,
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
            );
          }}
        />
      )}
    </View>
  );
};

export default IndustryMovement;
