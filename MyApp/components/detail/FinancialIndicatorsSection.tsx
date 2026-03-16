import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import {
  FinancialIndicators,
  getFinancialIndicators,
} from "@/helpers/FundamentalAnalysisHelpers";
import BarChart from "../ui/BarChart";

interface FinancialIndicatorsSectionProps {
  stockSymbol: string;
}

const FinancialIndicatorsSection = ({
  stockSymbol,
}: FinancialIndicatorsSectionProps) => {
  const [financialIndicators, setFinancialIndicators] =
    useState<FinancialIndicators | null>(null);

  const [annualData, setAnnualData] = useState<FinancialIndicators[]>([]);

  useEffect(() => {
    getFinancialIndicators(stockSymbol).then((res) => {
      if (res.status) {
        setFinancialIndicators(res.data);
        setAnnualData(res.annualData);
      }
    });
  }, [stockSymbol]);

  return financialIndicators != null ? (
    <View style={{ marginHorizontal: 12 }}>
      <Text typography="titleLarge">Định giá</Text>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">P/E</Text>
        <Text typography="titleMedium">
          {financialIndicators?.pe_ratio.toFixed(2)}
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">P/B</Text>
        <Text typography="titleMedium">
          {financialIndicators?.pb_ratio.toFixed(2)}
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">EPS</Text>
        <Text typography="titleMedium">
          {financialIndicators?.eps.toFixed(2)}
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">BVPS</Text>
        <Text typography="titleMedium">
          {financialIndicators?.bvps.toFixed(2)}
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">EV/EBITDA</Text>
        <Text typography="titleMedium">
          {financialIndicators?.ev_ebitda.toFixed(2)}
        </Text>
      </View>

      {/** -------------------------------------------- */}
      <Text typography="titleLarge" style={{ marginTop: 24 }}>
        Khả năng sinh lời
      </Text>

      <Text typography="titleMedium" style={{ marginTop: 12, marginBottom: 8 }}>
        {`Doanh thu (Tỷ đồng)`}
      </Text>
      <BarChart
        data={annualData.map((e) => {
          return {
            time: e?.year.toString(),
            value: e?.revenue / 1000000000,
          };
        })}
      />

      <Text typography="titleMedium" style={{ marginTop: 12, marginBottom: 8 }}>
        {`Lợi nhuận (Tỷ đồng)`}
      </Text>
      <BarChart
        data={annualData.map((e) => {
          return {
            time: e?.year.toString(),
            value: e?.net_income / 1000000000,
          };
        })}
      />

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">ROE</Text>
        <Text typography="titleMedium">
          {(financialIndicators?.roe * 100).toFixed(2)}%
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">ROA</Text>
        <Text typography="titleMedium">
          {(financialIndicators?.roa * 100).toFixed(2)}%
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">ROIC</Text>
        <Text typography="titleMedium">
          {(financialIndicators?.roic * 100).toFixed(2)}%
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Biên lợi nhuận ròng</Text>
        <Text typography="titleMedium">
          {(financialIndicators?.net_margin * 100).toFixed(2)}%
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Biên lợi nhuận gộp</Text>
        <Text typography="titleMedium">
          {(financialIndicators?.gross_margin * 100).toFixed(2)}%
        </Text>
      </View>

      {/** -------------------------------------------- */}
      <Text typography="titleLarge" style={{ marginTop: 24 }}>
        Sức mạnh tài chính
      </Text>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Tổng nợ/VCSH</Text>
        <Text typography="titleMedium">
          {financialIndicators?.debt_to_equity.toFixed(2)}
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Tổng nợ/Tổng TS</Text>
        <Text typography="titleMedium">
          {(
            financialIndicators?.debt_to_equity /
            financialIndicators?.financial_leverage
          ).toFixed(2)}
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Thanh toán nhanh</Text>
        <Text typography="titleMedium">
          {financialIndicators?.quick_ratio.toFixed(2)}
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Thanh toán hiện hành</Text>
        <Text typography="titleMedium">
          {financialIndicators?.current_ratio.toFixed(2)}
        </Text>
      </View>
    </View>
  ) : null;
};
export default FinancialIndicatorsSection;
