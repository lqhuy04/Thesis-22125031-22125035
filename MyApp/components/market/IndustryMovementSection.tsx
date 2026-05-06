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

const IndustryMovementSection = () => {
  const { theme } = useTheme();
  const screenWidth = Dimensions.get("window").width;
  const [data, setData] = useState<CurrentPriceData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [chosenIndex, setChosenIndex] = useState<number>(0);

  const categories = useMemo(() => {
    return [
      "Bất động sản",
      "Ngân hàng",
      "Dầu khí",
      "Thực phẩm",
      "Dịch vụ giải trí",
      "Công nghệ thông tin",
      "Xây dựng và Vật liệu",
      "Bán lẻ",
    ];
  }, []);

  useEffect(() => {
    setLoading(true);
    getIndustryMovement(categories[chosenIndex], 10).then((result) => {
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
          marginBottom: 8,
        }}
      >
        <Text typography="titleMedium">{"Diễn biến nhóm ngành"}</Text>
        <Text
          typography="titleMedium"
          color={theme.base.primary}
          onPress={() => {
            // router.push({
            //   pathname: "/AllNews",
            //   params: {
            //     data: JSON.stringify({
            //       title: categoryArticles[chosenIndex].category_name,
            //       category_id: categoryArticles[chosenIndex].category_id,
            //       type: "category",
            //     }),
            //   },
            // });
          }}
        >
          Xem tất cả
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
                    ? theme.base.primary + "12"
                    : theme.text.secondary + "80",
                borderWidth: 2,
                borderColor:
                  chosenIndex === index
                    ? theme.base.primary + "80"
                    : theme.text.secondary + "80",
                paddingVertical: 4,
                paddingHorizontal: 6,
                borderRadius: 16,
                marginRight: 8,
                marginBottom: 8,
              }}
              onPress={() => {
                setChosenIndex(index);
              }}
            >
              <Text
                typography="labelMedium"
                color={
                  chosenIndex === index
                    ? theme.base.primary
                    : theme.text.primary
                }
              >
                {" "}
                {item}{" "}
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
          height={300}
          title={categories[chosenIndex]}
          padding={1}
        />
      )}
    </View>
  );
};

export default IndustryMovementSection;
