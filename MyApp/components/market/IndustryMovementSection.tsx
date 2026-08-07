import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  View,
  Dimensions,
  Animated,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import Svg, { Rect } from "react-native-svg";
import { TreeMap } from "../ui/TreeMap";
import { CurrentPriceData } from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { getIndustryMovement } from "@/helpers/MarketHelpers";
import { Text } from "../ui/Text";
import { router } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";
import Entypo from "@expo/vector-icons/Entypo";

const SKELETON_RECTS = [
  { x: 0, y: 0, w: 0.47, h: 0.6 },
  { x: 0, y: 0.6, w: 0.47, h: 0.4 },
  { x: 0.47, y: 0, w: 0.3, h: 0.35 },
  { x: 0.77, y: 0, w: 0.23, h: 0.35 },
  { x: 0.47, y: 0.35, w: 0.18, h: 0.35 },
  { x: 0.65, y: 0.35, w: 0.19, h: 0.35 },
  { x: 0.84, y: 0.35, w: 0.16, h: 0.35 },
  { x: 0.47, y: 0.7, w: 0.28, h: 0.3 },
  { x: 0.75, y: 0.7, w: 0.14, h: 0.16 },
  { x: 0.75, y: 0.86, w: 0.14, h: 0.14 },
  { x: 0.89, y: 0.7, w: 0.11, h: 0.3 },
];

const TreeMapSkeleton: React.FC<{ width: number; height: number }> = ({
  width,
  height,
}) => {
  const { theme } = useTheme();
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, {
          toValue: 1,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(anim, {
          toValue: 0,
          duration: 700,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  }, [anim]);

  const opacity = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.25, 0.55],
  });

  const chartH = height - 24;
  const pad = 2;

  return (
    <Animated.View style={{ opacity, marginTop: 8 }}>
      <Svg width={width} height={chartH}>
        {SKELETON_RECTS.map((r, i) => (
          <Rect
            key={i}
            x={r.x * width + pad}
            y={r.y * chartH + pad}
            width={Math.max(0, r.w * width - pad * 2)}
            height={Math.max(0, r.h * chartH - pad * 2)}
            fill={theme.border.default}
            rx={4}
          />
        ))}
      </Svg>
    </Animated.View>
  );
};

type Props = {
  registerRefresh?: (fn: () => Promise<void>) => () => void;
};

const IndustryMovementSection = ({ registerRefresh }: Props) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const screenWidth = Dimensions.get("window").width;
  const [data, setData] = useState<CurrentPriceData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [chosenIndex, setChosenIndex] = useState<number>(0);

  const cache = useRef<Record<string, CurrentPriceData[]>>({});
  const abortRef = useRef<AbortController | null>(null);

  const categories = useMemo(
    () => [
      { label: t("home.industryBanks"), value: "8300" },
      { label: t("home.industryRealEstate"), value: "8600" },
      { label: t("home.industryFoodBeverage"), value: "3500" },
      { label: t("home.industryIndustrialGoods"), value: "2700" },
      { label: t("home.industryUtilities"), value: "7500" },
      { label: t("home.industryFinancialServices"), value: "8700" },
      { label: t("home.industryBasicResources"), value: "1700" },
      { label: t("home.industryTravelLeisure"), value: "5700" },
      { label: t("home.industryMedia"), value: "5500" },
      { label: t("home.industryConstruction"), value: "2300" },
      { label: t("home.industryChemicals"), value: "1300" },
      { label: t("home.industryTechnology"), value: "9500" },
      { label: t("home.industryRetail"), value: "5300" },
      { label: t("home.industryOilGas"), value: "0500" },
      { label: t("home.industryInsurance"), value: "8500" },
      { label: t("home.industryPersonalHousehold"), value: "3700" },
      { label: t("home.industryHealthcare"), value: "4500" },
      { label: t("home.industryAutomobiles"), value: "3300" },
      { label: t("home.industryTelecom"), value: "6500" },
      { label: t("home.industryInvestment"), value: "8900" },
    ],
    [t],
  );

  useEffect(() => {
    const key = categories[chosenIndex].value;

    if (cache.current[key]) {
      setData(cache.current[key]);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setData([]);

    getIndustryMovement(key, 10).then((result) => {
      if (controller.signal.aborted) return;

      if (result?.status) {
        cache.current[key] = result.data;
        setData(result.data);
      }
      setLoading(false);
    });

    return () => {
      controller.abort();
    };
  }, [categories, chosenIndex]);

  // Pull-to-refresh keeps the current treemap visible while fetching fresh data.
  useEffect(() => {
    const refreshFn = async () => {
      const key = categories[chosenIndex].value;

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const result = await getIndustryMovement(key, 10);
      if (controller.signal.aborted) return;

      if (result?.status) {
        cache.current[key] = result.data;
        setData(result.data);
      }
      setLoading(false);
    };
    const unregister = registerRefresh?.(refreshFn);
    return () => unregister?.();
  }, [registerRefresh, categories, chosenIndex]);

  return (
    <View
      style={{
        marginTop: 24,
        marginHorizontal: 12,
        backgroundColor: theme.background.bg,
        paddingTop: 12,
        paddingBottom: 16,
        paddingHorizontal: 12,
        borderRadius: 12,
      }}
    >
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <Text
          typography="titleMedium"
          color={theme.text.primary}
          style={{ marginRight: 8 }}
        >
          {t("home.industryMovement")}
        </Text>

        <TouchableOpacity
          onPress={() => {
            router.push({
              pathname: "/IndustryMovement",
              params: {
                industryId: categories[chosenIndex].value,
              },
            });
          }}
          style={{
            height: 16,
            width: 16,
            borderRadius: 8,
            backgroundColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Entypo
            name="chevron-small-right"
            size={16}
            color={theme.text.primary}
          />
        </TouchableOpacity>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{
          flexDirection: "row",
          marginBottom: 0,
        }}
      >
        {categories.map((item, index) => {
          return (
            <TouchableOpacity
              key={index.toString()}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 4,
                borderRadius: 24,
                backgroundColor:
                  chosenIndex === index
                    ? theme.base.primary
                    : theme.border.default,
                marginRight: 8,
              }}
              onPress={() => {
                setChosenIndex(index);
              }}
            >
              <Text
                typography="bodyMedium"
                color={
                  chosenIndex === index
                    ? theme.text.onPrimary
                    : theme.text.primary
                }
              >
                {" "}
                {item.label}{" "}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {loading ? (
        <TreeMapSkeleton width={screenWidth - 48} height={360} />
      ) : (
        <TreeMap
          data={data}
          width={screenWidth - 48}
          height={360}
          title={categories[chosenIndex].label}
          padding={1}
        />
      )}
    </View>
  );
};

export default IndustryMovementSection;
