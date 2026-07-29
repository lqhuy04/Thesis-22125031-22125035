import React, { useCallback, useEffect, useState } from "react";
import {
  Dimensions,
  FlatList,
  TouchableOpacity,
  View,
  Animated,
} from "react-native";
import { Text } from "../ui/Text";
import { getMarketIndices, MarketIndex } from "@/helpers/MarketHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { router } from "expo-router";

const { width } = Dimensions.get("window");
const CARD_WIDTH = width * 0.72;
const CARD_GAP = 12;

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

// Skeleton shimmer
const SkeletonTitle = () => {
  const { theme } = useTheme();
  const shimmer = React.useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: 900,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, [shimmer]);

  const opacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [0.4, 0.85],
  });

  return (
    <Animated.View
      style={{
        width: "45%",
        height: 20,
        borderRadius: 4,
        backgroundColor: theme.border.default,
        opacity,
      }}
    />
  );
};

const SkeletonCard = () => {
  const { theme } = useTheme();
  const shimmer = React.useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: 900,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, [shimmer]);

  const opacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: [0.4, 0.85],
  });

  const Box = ({
    w,
    h,
    mt = 0,
  }: {
    w: number | `${number}%`;
    h: number;
    mt?: number;
  }) => (
    <Animated.View
      style={{
        width: w,
        height: h,
        marginTop: mt,
        borderRadius: 4,
        backgroundColor: theme.border.default,
        opacity,
      }}
    />
  );

  return (
    <View
      style={{
        width: CARD_WIDTH,
        marginRight: CARD_GAP,
        marginTop: 12,
        borderRadius: 12,
        backgroundColor: theme.background.bg,
        padding: 12,
        paddingBottom: 6,
      }}
    >
      {/* IndexName */}
      <Box w="50%" h={14} />

      {/* IndexValue + Change badge + RatioChange */}
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginTop: 4,
          gap: 8,
        }}
      >
        <Box w="35%" h={24} />
        <Box w="20%" h={20} />
        <Box w="20%" h={14} />
      </View>

      {/* TotalVol | TotalVal */}
      <Box w="80%" h={12} mt={8} />

      {/* Progress bar */}
      <Box w="100%" h={4} mt={10} />

      {/* Advances / NoChanges / Declines */}
      <View
        style={{
          flexDirection: "row",
          justifyContent: "space-between",
          marginTop: 8,
        }}
      >
        <Box w="25%" h={12} />
        <Box w="25%" h={12} />
        <Box w="25%" h={12} />
      </View>
    </View>
  );
};

const MarketIndicesSection = ({ registerRefresh }: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getMarketIndices();
      if (result.status) {
        setIndices(result.data);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const unregister = registerRefresh?.(fetchData);
    return () => unregister?.();
  }, [fetchData, registerRefresh]);

  return (
    <View style={{ marginLeft: 12 }}>
      {loading ? (
        // Hiện 2 skeleton card lúc loading
        <>
          <SkeletonTitle />
          <View style={{ flexDirection: "row", marginTop: 0 }}>
            <SkeletonCard />
            <SkeletonCard />
          </View>
        </>
      ) : (
        <>
          <Text typography="titleLarge" color={theme.text.primary}>
            {t("home.marketToday")}
          </Text>
          <FlatList
            data={indices}
            keyExtractor={(item) => item.IndexId}
            horizontal
            showsHorizontalScrollIndicator={false}
            snapToInterval={CARD_WIDTH + CARD_GAP}
            snapToAlignment="start"
            decelerationRate="fast"
            contentContainerStyle={{ paddingRight: width - CARD_WIDTH }}
            renderItem={({ item }) => {
              const adv = Number(item.Advances) || 0;
              const noChg = Number(item.NoChanges) || 0;
              const dec = Number(item.Declines) || 0;
              const total = adv + noChg + dec;
              const allZero = total === 0;
              const mutedColor = theme.text.primary + "88";

              return (
                <TouchableOpacity
                  onPress={() =>
                    router.push({
                      pathname: "/IndexDetail" as any,
                      params: { data: JSON.stringify(item) },
                    })
                  }
                  style={{
                    width: CARD_WIDTH,
                    marginRight: CARD_GAP,
                    marginTop: 12,
                    borderRadius: 12,
                    backgroundColor: theme.background.bg,
                    padding: 12,
                    paddingBottom: 6,
                  }}
                >
                  <Text typography="bodyMedium" color={theme.text.primary}>
                    {item.IndexName}
                  </Text>

                  <View
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      marginTop: 4,
                    }}
                  >
                    <Text typography="titleLarge" color={theme.text.primary}>
                      {item.IndexValue.toLocaleString("vi-VN")}
                    </Text>
                    <View
                      style={{
                        borderRadius: 4,
                        paddingVertical: 2,
                        paddingHorizontal: 6,
                        backgroundColor:
                          Number(item.Change) > 0
                            ? theme.base.success + "33"
                            : theme.base.error + "33",
                        marginLeft: 8,
                      }}
                    >
                      <Text
                        typography="labelLarge"
                        color={
                          item.Change < 0
                            ? theme.base.error
                            : item.Change > 0
                              ? theme.base.success
                              : theme.base.warning
                        }
                      >
                        <Text
                          typography="labelSmall"
                          color={
                            item.Change < 0
                              ? theme.base.error
                              : item.Change > 0
                                ? theme.base.success
                                : theme.base.warning
                          }
                        >
                          {item.Change > 0
                            ? "▲"
                            : item.Change === 0
                              ? ""
                              : "▼"}{" "}
                        </Text>
                        {(item.Change >= 0
                          ? item.Change
                          : item.Change * -1
                        ).toLocaleString("vi-VN")}
                      </Text>
                    </View>
                    <Text
                      typography="labelMedium"
                      color={
                        item.RatioChange < 0
                          ? theme.base.error
                          : item.RatioChange > 0
                            ? theme.base.success
                            : theme.base.warning
                      }
                      style={{ marginLeft: 8 }}
                    >
                      <Text
                        typography="labelSmall"
                        color={
                          item.Change < 0
                            ? theme.base.error
                            : item.Change > 0
                              ? theme.base.success
                              : theme.base.warning
                        }
                      >
                        {item.Change > 0
                          ? "▲"
                          : item.Change === 0
                            ? ""
                            : "▼"}{" "}
                      </Text>
                      {(item.RatioChange >= 0
                        ? item.RatioChange
                        : item.RatioChange * -1
                      ).toLocaleString("vi-VN")}
                      %
                    </Text>
                  </View>

                  <Text
                    typography="bodySmall"
                    color={theme.text.primary + "80"}
                    style={{ marginVertical: 8 }}
                  >
                    {(Number(item.TotalVol) / 1000000).toLocaleString("vi-VN", {
                      maximumFractionDigits: 0,
                    })}{" "}
                    {t("home.millionShares")}
                    {"   "}|{"   "}
                    {(Number(item.TotalVal) / 1000000000).toLocaleString(
                      "vi-VN",
                      {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      },
                    )}{" "}
                    {t("home.billion")}
                  </Text>

                  {(() => {
                    const advPct = allZero ? 33.33 : (adv / total) * 100;
                    const noChgPct = allZero ? 33.33 : (noChg / total) * 100;
                    const decPct = allZero ? 33.34 : (dec / total) * 100;

                    return (
                      <View
                        style={{
                          flexDirection: "row",
                          height: 4,
                          borderRadius: 2,
                          overflow: "hidden",
                          marginTop: 8,
                          marginBottom: 2,
                        }}
                      >
                        <View
                          style={{
                            flex: advPct,
                            backgroundColor: allZero
                              ? mutedColor
                              : theme.base.success,
                          }}
                        />
                        <View
                          style={{
                            flex: noChgPct,
                            backgroundColor: allZero
                              ? mutedColor
                              : theme.base.warning,
                          }}
                        />
                        <View
                          style={{
                            flex: decPct,
                            backgroundColor: allZero
                              ? mutedColor
                              : theme.base.error,
                          }}
                        />
                      </View>
                    );
                  })()}

                  <View
                    style={{
                      flexDirection: "row",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginVertical: 4,
                    }}
                  >
                    <Text
                      typography="bodySmall"
                      color={allZero ? mutedColor : theme.base.success}
                    >
                      {item.Advances} {t("home.ticker")} {"▲"}
                    </Text>

                    <View
                      style={{ flexDirection: "row", alignItems: "center" }}
                    >
                      <Text
                        typography="bodySmall"
                        color={allZero ? mutedColor : theme.base.warning}
                      >
                        {item.NoChanges} {t("home.ticker")}
                      </Text>
                      <View
                        style={{
                          width: 6,
                          height: 2,
                          backgroundColor: allZero
                            ? mutedColor
                            : theme.base.warning,
                          marginLeft: 8,
                        }}
                      />
                    </View>

                    <Text
                      typography="bodySmall"
                      color={allZero ? mutedColor : theme.base.error}
                    >
                      {item.Declines} {t("home.ticker")} {"▼"}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            }}
          />
        </>
      )}
    </View>
  );
};

export default MarketIndicesSection;
