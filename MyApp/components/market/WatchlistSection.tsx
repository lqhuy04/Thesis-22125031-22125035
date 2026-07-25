import { FavoriteItem, getFavoritelist } from "@/helpers/ProfileHelpers";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useTheme } from "@/hooks/ThemeContext";
import {
  View,
  Image,
  TouchableOpacity,
  Animated,
  Dimensions,
} from "react-native";
import { Text } from "@/components/ui/Text";
import { router, useFocusEffect } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";
import Entypo from "@expo/vector-icons/Entypo";
import Ionicons from "@expo/vector-icons/Ionicons";
import { ALL_VALUE } from "@/app/IndustryMovement";
import { saveSearchHistory } from "@/helpers/SearchHelper";

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

const FavoriteSkeletonRow = ({
  animatedOpacity,
  isFirst,
}: {
  animatedOpacity: Animated.Value;
  isFirst: boolean;
}) => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;

  return (
    <View>
      {!isFirst && (
        <View
          style={{
            width: screenWidth - 48,
            height: 1,
            backgroundColor: theme.border.default,
            marginHorizontal: 12,
          }}
        />
      )}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginTop: 16,
          marginBottom: 16,
          marginHorizontal: 12,
        }}
      >
        {/* Logo */}
        <SkeletonBox
          width={40}
          height={40}
          borderRadius={2}
          animatedOpacity={animatedOpacity}
          style={{ marginRight: 10 }}
        />

        {/* Symbol + Company name */}
        <View style={{ flex: 1, marginRight: 12, gap: 6 }}>
          <SkeletonBox
            width={60}
            height={13}
            animatedOpacity={animatedOpacity}
          />
          <SkeletonBox
            width={130}
            height={11}
            animatedOpacity={animatedOpacity}
          />
        </View>

        {/* Price + Change */}
        <View style={{ alignItems: "flex-start", gap: 6, marginRight: 12 }}>
          <SkeletonBox
            width={48}
            height={13}
            animatedOpacity={animatedOpacity}
          />
          <SkeletonBox
            width={36}
            height={11}
            animatedOpacity={animatedOpacity}
          />
        </View>

        {/* % Badge */}
        <SkeletonBox
          width={64}
          height={32}
          borderRadius={4}
          animatedOpacity={animatedOpacity}
        />
      </View>
    </View>
  );
};

// ─── Main Screen ─────────────────────────────────────────────────────────────

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

const WatchlistSection = ({ registerRefresh }: Props) => {
  const { t } = useLocalization();
  const { theme } = useTheme();
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [loading, setLoading] = useState(false);

  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  const sortedFavorites = useMemo(() => {
    return [...favorites].sort((a, b) =>
      sortOrder === "desc"
        ? b.PerPriceChange - a.PerPriceChange
        : a.PerPriceChange - b.PerPriceChange,
    );
  }, [favorites, sortOrder]);

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

  const goToAllStocks = useCallback(() => {
    router.push({
      pathname: "/IndustryMovement",
      params: { industryId: ALL_VALUE },
    });
  }, []);

  const goToStock = useCallback(async (symbol: string) => {
    router.push({
      pathname: "/Detail",
      params: { data: symbol },
    });
    await saveSearchHistory(symbol);
  }, []);

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

  // Pull-to-refresh — fetch lại danh sách yêu thích
  useEffect(() => {
    const refreshFn = async () => {
      setLoading(true);
      await fetchFavorites().finally(() => setLoading(false));
    };
    const unregister = registerRefresh?.(refreshFn);
    return () => unregister?.();
  }, [registerRefresh, fetchFavorites]);

  const renderItem = ({
    item,
    index,
  }: {
    item: FavoriteItem;
    index: number;
  }) => {
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

    const absPerPriceChange = Math.abs(item.PerPriceChange).toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const arrow =
      item.PerPriceChange > 0 ? "▲" : item.PerPriceChange < 0 ? "▼" : "";

    const screenWidth = Dimensions.get("window").width;

    return (
      <View key={String(item.id)}>
        {index !== 0 && (
          <View
            style={{
              width: screenWidth - 48,
              height: 1,
              backgroundColor: theme.border.default,
              marginTop: 16,
              marginHorizontal: 12,
            }}
          />
        )}

        <TouchableOpacity
          onPress={() => goToStock(item.symbol)}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginTop: 16,
            marginHorizontal: 12,
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
              {item.CurrentPrice.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
            <Text typography="bodySmall" color={priceColor}>
              {`(${item.PriceChange > 0 ? "+" : ""}${item.PriceChange.toLocaleString("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`}
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
      </View>
    );
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.background.surface }}>
      {loading ? (
        <View style={{ marginHorizontal: 12 }}>
          {/* Header placeholder */}
          <SkeletonBox
            width={120}
            height={14}
            animatedOpacity={animatedOpacity}
            style={{ marginBottom: 12 }}
          />
          <View
            style={{
              borderRadius: 12,
              backgroundColor: theme.background.bg,
              paddingBottom: 12,
            }}
          >
            {/* Column header */}
            <View
              style={{
                flexDirection: "row",
                margin: 12,
                alignItems: "center",
              }}
            >
              <SkeletonBox
                width={56}
                height={12}
                animatedOpacity={animatedOpacity}
                style={{ flex: 1 }}
              />
              <SkeletonBox
                width={96}
                height={12}
                animatedOpacity={animatedOpacity}
              />
            </View>

            <View
              style={{
                width: "100%",
                height: 1,
                backgroundColor: theme.border.default,
              }}
            />

            {Array.from({ length: 5 }).map((_, i) => (
              <FavoriteSkeletonRow
                key={i}
                isFirst={i === 0}
                animatedOpacity={animatedOpacity}
              />
            ))}
          </View>
        </View>
      ) : (
        <View style={{ marginHorizontal: 12 }}>
          <Text
            typography="titleMedium"
            color={theme.text.primary}
            style={{ marginBottom: 12 }}
          >
            {t("profile.favoriteList")}
          </Text>

          {sortedFavorites.length === 0 ? (
            <View
              style={{
                borderRadius: 12,
                backgroundColor: theme.background.bg,
                padding: 16,
              }}
            >
              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <View
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 12,
                    backgroundColor: theme.base.primary + "14",
                    alignItems: "center",
                    justifyContent: "center",
                    marginRight: 12,
                  }}
                >
                  <Ionicons
                    name="file-tray-outline"
                    size={28}
                    color={theme.base.primary}
                  />
                </View>

                <View style={{ flex: 1, gap: 4 }}>
                  <Text typography="titleMedium" color={theme.text.primary}>
                    {t("profile.emptyFavoriteTitle")}
                  </Text>
                  <Text
                    typography="bodyMedium"
                    color={theme.text.primary + "80"}
                  >
                    {t("profile.emptyFavoriteDesc")}
                  </Text>
                </View>
              </View>

              <View style={{ alignItems: "flex-end", marginTop: 16 }}>
                <TouchableOpacity
                  onPress={goToAllStocks}
                  style={{
                    backgroundColor: theme.base.primary,
                    borderRadius: 20,
                    paddingVertical: 8,
                    paddingHorizontal: 16,
                  }}
                >
                  <Text typography="labelLarge" color={theme.text.onPrimary}>
                    {t("profile.viewAllStocks")}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <View
              style={{
                borderRadius: 12,
                backgroundColor: theme.background.bg,
                paddingBottom: 12,
              }}
            >
              <View
                style={{
                  flexDirection: "row",
                  margin: 12,
                  alignItems: "center",
                }}
              >
                <Text
                  typography="labelLarge"
                  color={theme.text.primary}
                  style={{ flex: 1 }}
                >
                  {t("home.tickerUpper")}
                </Text>

                <TouchableOpacity
                  onPress={() =>
                    setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"))
                  }
                  style={{ flexDirection: "row", alignItems: "center" }}
                >
                  <Text typography="labelLarge" color={theme.base.primary}>
                    {t("profile.indayChange")}
                  </Text>
                  <View style={{ marginLeft: 4, alignItems: "center" }}>
                    <Entypo
                      name="chevron-small-up"
                      size={16}
                      color={
                        sortOrder === "asc"
                          ? theme.base.primary
                          : theme.text.primary
                      }
                      style={{ marginBottom: -2 }}
                    />
                    <Entypo
                      name="chevron-small-down"
                      size={16}
                      color={
                        sortOrder === "desc"
                          ? theme.base.primary
                          : theme.text.primary
                      }
                      style={{ marginTop: -2 }}
                    />
                  </View>
                </TouchableOpacity>
              </View>

              <View
                style={{
                  width: "100%",
                  height: 1,
                  backgroundColor: theme.border.default,
                }}
              />

              {sortedFavorites.map((item, index) =>
                renderItem({ item, index }),
              )}
            </View>
          )}
        </View>
      )}
    </View>
  );
};

export default WatchlistSection;
