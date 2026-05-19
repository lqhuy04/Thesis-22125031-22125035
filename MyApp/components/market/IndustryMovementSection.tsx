import React, { useEffect, useMemo, useState } from "react";
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

const IndustryMovementSection = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const screenWidth = Dimensions.get("window").width;
  const [data, setData] = useState<CurrentPriceData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [chosenIndex, setChosenIndex] = useState<number>(0);

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
    setLoading(true);
    getIndustryMovement(categories[chosenIndex].value, 10).then((result) => {
      if (result?.status) {
        setData(result?.data);
      }
      setLoading(false);
    });
  }, [categories, chosenIndex]);

  return (
    <View style={{ marginTop: 24, marginHorizontal: 12 }}>
      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 12,
        }}
      >
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("home.industryMovement")}
        </Text>
        <Text
          typography="titleMedium"
          color={theme.base.primary}
          onPress={() => {
            router.push({
              pathname: "/IndustryMovement",
              params: {
                industry: categories[chosenIndex].label,
              },
            });
          }}
        >
          {t("home.viewAll")}
        </Text>
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
                    ? theme.base.primary
                    : theme.background.primarySurface,
                paddingVertical: 6,
                paddingHorizontal: 12,
                borderRadius: 16,
                marginRight: 8,
                marginBottom: 12,
              }}
              onPress={() => {
                setChosenIndex(index);
              }}
            >
              <Text
                typography="labelLarge"
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
            height: 300,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <ActivityIndicator size="small" color={theme.base.primary} />
        </View>
      ) : (
        <TreeMap
          data={data}
          width={screenWidth - 24}
          height={360}
          title={categories[chosenIndex].label}
          padding={1}
        />
      )}
    </View>
  );
};

export default IndustryMovementSection;
