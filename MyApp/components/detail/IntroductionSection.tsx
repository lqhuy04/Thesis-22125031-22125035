import React, { useEffect, useState } from "react";
import { Image, View } from "react-native";
import { Text } from "../ui/Text";
import {
  CompanyProfile,
  getCompanyProfile,
  getCompanySubsidiaries,
  SubsidiaryCompany,
} from "@/helpers/CompanyProfileHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import { Images } from "@/constants/Images";

interface IntroductionSectionProps {
  stockSymbol: string;
}

const IntroductionSection = ({ stockSymbol }: IntroductionSectionProps) => {
  const { theme } = useTheme();
  const [companyProfileData, setCompanyProfileData] =
    useState<CompanyProfile | null>(null);

  const [subsidiaries, setSubsidiaries] = useState<SubsidiaryCompany[]>([]);
  const [associates, setAssociates] = useState<SubsidiaryCompany[]>([]);

  useEffect(() => {
    getCompanyProfile(stockSymbol).then((res) => {
      if (res.status) {
        setCompanyProfileData(res.data);
      }
    });

    getCompanySubsidiaries(stockSymbol).then((res) => {
      if (res.status) {
        setSubsidiaries(res.data.subsidiaries);
        setAssociates(res.data.associates);
      }
    });
  }, [stockSymbol]);

  return companyProfileData != null ? (
    <View style={{ marginTop: 12, marginHorizontal: 12 }}>
      
      <Text typography="bodyMedium">{companyProfileData?.description}</Text>
      <View style={{height: 12}}/>
      <Text typography="bodyMedium">• Địa chỉ: {companyProfileData?.address}</Text>
      <Text typography="bodyMedium">• Email: {companyProfileData?.email}</Text>
      <Text typography="bodyMedium">• Điện thoại: {companyProfileData?.phone}</Text>
      <Text typography="bodyMedium">• Website: {companyProfileData?.website}</Text>
      <Text typography="bodyMedium">• Fax: {companyProfileData?.fax}</Text>

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

      {/* ── Subsidiaries ── */}
      <Text typography="titleLarge" style={{ marginBottom: 8, marginTop: 24 }}>
        Công ty con
      </Text>

      {subsidiaries.length > 0
        ? subsidiaries.map((sub) => (
            <View
              key={sub.symbol}
              style={{
                borderRadius: 4,
                padding: 8,
                backgroundColor: theme.background.surface,
                marginTop: 8,
                flexDirection: "row",
                alignItems: "flex-start",
              }}
            >
              <Image
                source={Images.ic_subsidiary}
                style={{ width: 36, height: 36, marginRight: 16 }}
              />

              <View style={{ flex: 1 }}>
                <Text typography="titleMedium">{sub.company_name}</Text>
                <Text typography="bodyMedium" style={{ marginTop: 4 }}>
                  Vốn điều lệ: {sub.charter_capital_billion} tỷ
                </Text>
                <Text typography="bodyMedium" style={{ marginTop: 4 }}>
                  Tỉ lệ nắm giữ: {sub.ownership_pct}%
                </Text>
              </View>
            </View>
          ))
        : null}

      {/* ── Associates ── */}
      <Text typography="titleLarge" style={{ marginBottom: 8, marginTop: 24 }}>
        Công ty liên kết
      </Text>

      {associates.length > 0
        ? associates.map((sub) => (
            <View
              key={sub.symbol}
              style={{
                borderRadius: 4,
                padding: 8,
                backgroundColor: theme.background.surface,
                marginTop: 8,
                flexDirection: "row",
                alignItems: "flex-start",
              }}
            >
              <Image
                source={Images.ic_subsidiary}
                style={{ width: 36, height: 36, marginRight: 16 }}
              />

              <View style={{ flex: 1 }}>
                <Text typography="titleMedium">{sub.company_name}</Text>
                <Text typography="bodyMedium" style={{ marginTop: 4 }}>
                  Vốn điều lệ: {sub.charter_capital_billion} tỷ
                </Text>
                <Text typography="bodyMedium" style={{ marginTop: 4 }}>
                  Tỉ lệ nắm giữ: {sub.ownership_pct}%
                </Text>
              </View>
            </View>
          ))
        : null}
    </View>
  ) : null;
};
export default IntroductionSection;
