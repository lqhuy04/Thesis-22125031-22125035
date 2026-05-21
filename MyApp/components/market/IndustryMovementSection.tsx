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
      { label: t("home.industryRealEstate"), value: "Bất động sản" },
      { label: t("home.industryBanking"), value: "Ngân hàng" },
      { label: t("home.industryOilGas"), value: "Dầu khí" },
      { label: t("home.industryFood"), value: "Thực phẩm" },
      { label: t("home.industryEntertainment"), value: "Dịch vụ giải trí" },
      { label: t("home.industryIT"), value: "Công nghệ thông tin" },
      { label: t("home.industryConstruction"), value: "Xây dựng và Vật liệu" },
      { label: t("home.industryRetail"), value: "Bán lẻ" },
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
        padding: 12,
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
          typography="titleLarge"
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
                industry: categories[chosenIndex].value,
              },
            });
          }}
          style={{
            height: 20,
            width: 20,
            borderRadius: 10,
            backgroundColor: theme.border.default,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Entypo
            name="chevron-small-right"
            size={20}
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
                backgroundColor:
                  chosenIndex === index
                    ? theme.base.primary + "20"
                    : theme.border.default + "80",
                paddingVertical: 2,
                paddingHorizontal: 12,
                borderRadius: 16,
                marginRight: 8,
                borderWidth: 2,
                borderColor:
                  chosenIndex === index
                    ? theme.base.primary + "60"
                    : theme.border.default + "00",
              }}
              onPress={() => {
                setChosenIndex(index);
              }}
            >
              <Text
                typography="bodyMedium"
                color={
                  chosenIndex === index
                    ? theme.base.primary
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
