import React, { useEffect } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import {
  CompanyProfile,
  getCompanyProfile,
} from "@/helpers/CompanyProfileHelpers";

interface IntroductionSectionProps {
  stockSymbol: string;
}

const IntroductionSection = ({ stockSymbol }: IntroductionSectionProps) => {
  const [companyProfileData, setCompanyProfileData] =
    React.useState<CompanyProfile | null>(null);

  useEffect(() => {
    getCompanyProfile(stockSymbol).then((res) => {
      if (res.status) {
        setCompanyProfileData(res.data);
      }
    });
  }, [stockSymbol]);

  return companyProfileData != null ? (
    <View style={{ marginTop: 12, marginHorizontal: 12 }}>
      <Text typography="titleLarge" style={{ marginBottom: 8 }}>
        Giới thiệu
      </Text>

      <Text typography="bodyMedium">{companyProfileData?.description}</Text>

      {/* ── Basic Info ── */}
      <View>
        <Text
          typography="titleLarge"
          style={{ marginBottom: 4, marginTop: 24 }}
        >
          Thông tin cơ bản
        </Text>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Mã</Text>
          <Text typography="bodyMedium">{companyProfileData?.symbol}</Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Tên ngành ICB</Text>
          <Text typography="bodyMedium">
            {companyProfileData?.industry_name}
          </Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Mã ngành ICB</Text>
          <Text typography="bodyMedium">{companyProfileData?.icb_code}</Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Năm thành lập</Text>
          <Text typography="bodyMedium">
            {companyProfileData?.founded_date}
          </Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Vốn điều lệ</Text>
          <Text typography="bodyMedium">
            {companyProfileData?.listed_volume} tỷ
          </Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Số lượng nhân viên</Text>
          <Text typography="bodyMedium">
            {companyProfileData?.employee_count}
          </Text>
        </View>
      </View>

      {/* ── Listing information ── */}
      <View>
        <Text
          typography="titleLarge"
          style={{ marginBottom: 4, marginTop: 24 }}
        >
          Thông tin niêm yết
        </Text>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Ngày niêm yết</Text>
          <Text typography="bodyMedium">
            {companyProfileData?.listing_date}
          </Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">Nơi niêm yết</Text>
          <Text typography="bodyMedium">{companyProfileData?.exchange}</Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">{`Giá chào sàn (1000 VND)`}</Text>
          <Text typography="bodyMedium">{companyProfileData?.ipo_price}</Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">KL đang niêm yết</Text>
          <Text typography="bodyMedium">
            {companyProfileData?.market_cap_billion} tỷ
          </Text>
        </View>

        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
          }}
        >
          <Text typography="titleMedium">SLCP lưu hành</Text>
          <Text typography="bodyMedium">
            {companyProfileData?.shares_outstanding}
          </Text>
        </View>
      </View>
    </View>
  ) : null;
};
export default IntroductionSection;
