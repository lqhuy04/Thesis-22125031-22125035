import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  TouchableOpacity,
  View,
} from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import * as Progress from "react-native-progress";
import { SafeAreaView } from "react-native-safe-area-context";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import DropDown from "@/components/ui/Dropdown";
import { router } from "expo-router";
import { getRiskAppetite, saveRiskAppetite } from "@/helpers/ProfileHelpers";

const RiskAppetite = () => {
  const screenWidth = Dimensions.get("window").width;
  const { theme } = useTheme();
  const { t } = useLocalization();

  const [index, setIndex] = useState<number>(1);

  const [experience, setExperience] = useState<string>("");
  const [expectation, setExpectation] = useState<string>("");
  const [period, setPeriod] = useState<string>("");
  const [comfortZone, setComfortZone] = useState<string>("");
  const [capitalRatio, setCapitalRatio] = useState<string>("");

  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    getRiskAppetite().then((res) => {
      if (res.status && res.data) {
        setExperience(res.data.experience);
        setExpectation(res.data.expectation);
        setPeriod(res.data.period);
        setComfortZone(res.data.comfort_zone);
        setCapitalRatio(res.data.capital_ratio);
      }
      setLoading(false);
    });
  }, []);

  const surveyData = useMemo(() => {
    return [
      {
        key: 1,
        title: "Bạn đã có kinh nghiệm đầu tư chưa?",
        description:
          "Để chúng tôi chọn ngôn ngữ và công cụ hỗ trợ phù hợp nhất với trình độ của bạn.",
        label: "Kinh nghiệm đầu tư",
        placeholder: "Chọn kinh nghiệm",
        data: [
          { key: "1", value: "Chưa bao giờ" },
          { key: "2", value: "Đã có kinh nghiệm" },
          { key: "3", value: "Nhà đầu tư chuyên nghiệp" },
        ],
        selected: experience,
      },
      {
        key: 2,
        title: "Kỳ vọng lớn nhất của bạn là gì?",
        description:
          "Bạn muốn ưu tiên sự an toàn, nhận cổ tức đều đặn hay tối ưu hóa lợi nhuận đột phá?",
        label: "Kỳ vọng",
        placeholder: "Chọn kỳ vọng",
        data: [
          { key: "1", value: "Bảo toàn vốn" },
          { key: "2", value: "Kiếm thêm thu nhập thụ động" },
          { key: "3", value: "Tăng trưởng tài sản nhanh" },
        ],
        selected: expectation,
      },
      {
        key: 3,
        title: "Bạn định đầu tư trong bao lâu?",
        description:
          "Khoảng thời gian này giúp chúng tôi lọc ra những mã cổ phiếu phù hợp với kế hoạch tài chính của bạn.",
        label: "Thời gian",
        placeholder: "Chọn khoảng thời gian",
        data: [
          { key: "1", value: "Ngắn hạn (Dưới 1 năm)" },
          { key: "2", value: "Trung hạn (1-3 năm)" },
          { key: "3", value: "Dài hạn (trên 3-5 năm)" },
        ],
        selected: period,
      },
      {
        key: 4,
        title: "Kịch bản đầu tư nào khiến bạn thoải mái nhất?",
        description: `Hãy chọn sự kết hợp giữa "Lợi nhuận kỳ vọng" và "Mức lỗ tối đa" mà tâm lý của bạn có thể chấp nhận được trong khoảng thời gian trên.`,
        label: "Kịch bản mong muốn",
        placeholder: "Chọn kịch bản mong muốn",
        data: [
          { key: "1", value: "Lợi nhuận +5% | Rủi ro lỗ tối đa -1%" },
          { key: "2", value: "Lợi nhuận +15% | Rủi ro lỗ tối đa -10%" },
          { key: "3", value: "Lợi nhuận +30% | Rủi ro lỗ tối đa -25%" },
        ],
        selected: comfortZone,
      },
      {
        key: 5,
        title: "Số vốn này chiếm bao nhiêu phần thu nhập?",
        description: `Chúng tôi cần biết đây là khoản tích lũy nhỏ hay nguồn vốn chính để đưa ra chiến lược quản lý rủi ro an toàn.`,
        label: "Tỷ trọng vốn",
        placeholder: "Chọn tỷ trọng vốn",
        data: [
          { key: "1", value: "Dưới 10%" },
          { key: "2", value: "Khoảng 10 - 30%" },
          { key: "3", value: "Trên 30%" },
        ],
        selected: capitalRatio,
      },
    ];
  }, [capitalRatio, comfortZone, expectation, experience, period]);

  const Continue = useCallback(() => {
    if (index === 5) {
      saveRiskAppetite({
        experience: experience,
        expectation: expectation,
        period: period,
        comfort_zone: comfortZone,
        capital_ratio: capitalRatio,
      }).then((res) => {
        if (res.status) {
          router.back();
        } else {
          Alert.alert("Lỗi", "Đã có lỗi xảy ra, vui lòng thử lại sau.");
        }
      });
    } else {
      setIndex((prev) => prev + 1);
    }
  }, [capitalRatio, comfortZone, expectation, experience, index, period]);

  const Back = useCallback(() => {
    setIndex((prev) => (prev > 1 ? prev - 1 : prev));
  }, []);

  return loading ? (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <ActivityIndicator size="large" color={theme.base.primary} />
    </View>
  ) : (
    <SafeAreaView
      style={{
        backgroundColor: theme.background.bg,
        flex: 1,
        paddingTop: 12,
        paddingBottom: 40,
      }}
    >
      <View style={{ marginHorizontal: 12 }}>
        <ScreenHeader
          title="Khảo sát khẩu vị rủi ro"
          onPressBack={Back}
          hiddenBack={index === 1}
        />
      </View>

      <Progress.Bar
        progress={0.2 * index}
        height={2}
        width={screenWidth}
        borderRadius={0}
        borderWidth={0}
        unfilledColor={theme.border.default}
        color={theme.base.primary}
      />

      <View style={{ flex: 1, marginTop: 24, marginHorizontal: 16 }}>
        <Text typography="headlineSmall">{surveyData[index - 1].title}</Text>

        <Text typography="bodyMedium" style={{ marginTop: 4 }}>
          {surveyData[index - 1].description}
        </Text>

        <DropDown
          key={surveyData[index - 1].key}
          data={surveyData[index - 1].data}
          placeholder={surveyData[index - 1].placeholder}
          label={surveyData[index - 1].label}
          setSelected={(val) => {
            const currentData = surveyData[index - 1];
            const selectedValue =
              currentData.data.find((item) => item.key === val)?.value || "";
            switch (currentData.key) {
              case 1:
                setExperience(selectedValue);
                break;
              case 2:
                setExpectation(selectedValue);
                break;
              case 3:
                setPeriod(selectedValue);
                break;
              case 4:
                setComfortZone(selectedValue);
                break;
              case 5:
                setCapitalRatio(selectedValue);
                break;
            }
          }}
          value={surveyData[index - 1].selected}
          required
        />
      </View>

      <TouchableOpacity
        activeOpacity={1}
        onPress={
          surveyData[index - 1].selected.length === 0 ? undefined : Continue
        }
        style={{
          backgroundColor:
            surveyData[index - 1].selected.length === 0
              ? theme.background.surface
              : theme.base.primary,
          paddingVertical: 8,
          marginHorizontal: 12,
          borderRadius: 4,
          marginTop: 24,
          alignItems: "center",
        }}
      >
        <Text
          typography="titleLarge"
          color={
            surveyData[index - 1].selected.length === 0
              ? theme.text.secondary
              : "#F2F4F7"
          }
        >
          {index !== 5 ? t("ui.continue") : t("ui.start")}
        </Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
};

export default RiskAppetite;
