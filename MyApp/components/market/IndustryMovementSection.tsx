import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  View,
  Dimensions,
  ActivityIndicator,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { TreeMap } from "../ui/TreeMap";
import { CurrentPriceData } from "@/helpers/DetailHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { getIndustryMovement } from "@/helpers/MarketHelpers";
import { Text } from "../ui/Text";
import { router } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";
import Entypo from "@expo/vector-icons/Entypo";

const IndustryMovementSection = () => {
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
      { label: t("home.industryFinancials"), value: "8000" },
      { label: t("home.industryIndustrials"), value: "2000" },
      { label: t("home.industryConsumerGoods"), value: "3000" },
      { label: t("home.industryTechnology"), value: "9000" },
      { label: t("home.industryConsumerServices"), value: "5000" },
      { label: t("home.industryOilGas"), value: "0001" },
      { label: t("home.industryBasicMaterials"), value: "1000" },
      { label: t("home.industryTelecom"), value: "6000" },
      { label: t("home.industryUtilities"), value: "7000" },
      { label: t("home.industryHealthcare"), value: "4000" },
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

  return (
    <View
      style={{
        marginTop: 24,
        marginHorizontal: 12,
        backgroundColor: theme.background.bg,
        paddingVertical: 12,
        paddingLeft: 12,
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
        <View
          style={{
            height: 360,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <ActivityIndicator size="small" color={theme.base.primary} />
        </View>
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
