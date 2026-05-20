import { FavoriteItem, getFavoritelist } from "@/helpers/ProfileHelpers";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useTheme } from "@/hooks/ThemeContext";
import {
  View,
  Image,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  Animated,
} from "react-native";
import { Text } from "@/components/ui/Text";
import { router, useFocusEffect } from "expo-router";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { useLocalization } from "@/hooks/LocalizationContext";

// ─── Skeleton ────────────────────────────────────────────────────────────────

const SkeletonBox = ({
  width,
  height,
  borderRadius = 4,
  style,
  animatedOpacity,
}: {
  width: number | string;
  height: number;
  borderRadius?: number;
  style?: object;
  animatedOpacity: Animated.Value;
}) => {
  const { theme } = useTheme();

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius,
          backgroundColor: theme.border.default,
          opacity: animatedOpacity,
        },
        style,
      ]}
    />
  );
};

const FavoriteSkeletonItem = ({
  animatedOpacity,
}: {
  animatedOpacity: Animated.Value;
}) => {
  const { theme } = useTheme();

  return (
    <View
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        marginHorizontal: 12,
        marginBottom: 12,
        borderRadius: 12,
        flexDirection: "row",
        alignItems: "center",
      }}
    >
      {/* Avatar */}
      <SkeletonBox
        width={48}
        height={48}
        borderRadius={4}
        animatedOpacity={animatedOpacity}
        style={{ marginRight: 8 }}
      />

      {/* Text block */}
      <View style={{ flex: 1, marginRight: 12, gap: 6 }}>
        <SkeletonBox width={80} height={14} animatedOpacity={animatedOpacity} />
        <SkeletonBox
          width={140}
          height={12}
          animatedOpacity={animatedOpacity}
        />
      </View>

      {/* Price block */}
      <View style={{ alignItems: "flex-end", gap: 6, marginRight: 12 }}>
        <SkeletonBox width={60} height={14} animatedOpacity={animatedOpacity} />
        <SkeletonBox width={48} height={12} animatedOpacity={animatedOpacity} />
      </View>

      {/* Badge */}
      <SkeletonBox
        width={64}
        height={36}
        borderRadius={4}
        animatedOpacity={animatedOpacity}
      />
    </View>
  );
};

// ─── Main Screen ─────────────────────────────────────────────────────────────

const Favorite = () => {
  const { theme } = useTheme();
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Shimmer animation
  const animatedOpacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(animatedOpacity, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(animatedOpacity, {
          toValue: 0.3,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    );
    shimmer.start();
    return () => shimmer.stop();
  }, [animatedOpacity]);

  const fetchFavorites = useCallback(async () => {
    const res = await getFavoritelist();
    if (res?.status) {
      setFavorites(res.data);
    }
  }, []);

  // Thay useEffect fetch lần đầu bằng useFocusEffect
  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      fetchFavorites().finally(() => setLoading(false));
    }, [fetchFavorites]),
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchFavorites();
    setRefreshing(false);
  }, [fetchFavorites]);

  const renderItem = ({ item }: { item: FavoriteItem }) => {
    const priceColor =
      item.PriceChange > 0
        ? theme.base.success
        : item.PriceChange < 0
          ? theme.base.error
          : theme.base.warning;

    const perPriceColor =
      item.PerPriceChange > 0
        ? theme.base.success
        : item.PerPriceChange < 0
          ? theme.base.error
          : theme.base.warning;

    const absPerPriceChange = Math.abs(item.PerPriceChange).toFixed(2);
    const arrow =
      item.PerPriceChange > 0 ? "▲" : item.PerPriceChange < 0 ? "▼" : "";

    return (
      <TouchableOpacity
        onPress={() => {
          router.push({ pathname: "/Detail", params: { data: item.symbol } });
        }}
        style={{
          padding: 12,
          backgroundColor: theme.background.bg,
          marginHorizontal: 12,
          marginBottom: 12,
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
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              marginBottom: 2,
            }}
          >
            <Text typography="titleMedium" color={theme.text.primary}>
              {item.symbol}
            </Text>
          </View>

          <Text
            typography="bodyMedium"
            color={theme.text.primary + "80"}
            numberOfLines={1}
          >
            {item.company_name}
          </Text>
        </View>

        <View style={{ alignItems: "flex-start" }}>
          <Text typography="labelLarge" color={theme.text.primary}>
            {item.CurrentPrice}
          </Text>
          <Text typography="bodySmall" color={priceColor}>
            {`(${item.PriceChange > 0 ? "+" : ""}${item.PriceChange})`}
          </Text>
        </View>

        <View
          style={{
            paddingVertical: 6,
            paddingHorizontal: 12,
            borderRadius: 4,
            marginLeft: 12,
            backgroundColor: perPriceColor + "24",
          }}
        >
          <Text typography="bodyMedium" color={perPriceColor}>
            <Text typography="labelSmall" color={perPriceColor}>
              {`${arrow} `}
            </Text>
            {`${absPerPriceChange}%`}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  const { t } = useLocalization();

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      <ScreenHeader title={t("profile.favoriteList")} />

      {loading ? (
        <View style={{ paddingTop: 12 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <FavoriteSkeletonItem key={i} animatedOpacity={animatedOpacity} />
          ))}
        </View>
      ) : (
        <FlatList
          data={favorites}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={{ paddingTop: 12 }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={theme.base.primary}
              colors={[theme.base.primary]}
            />
          }
        />
      )}
    </View>
  );
};

export default Favorite;
