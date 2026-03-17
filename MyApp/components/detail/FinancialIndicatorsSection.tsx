import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import {
  CashFlows,
  FinancialIndicators,
  getCashFlows,
  getFinancialIndicators,
} from "@/helpers/FundamentalAnalysisHelpers";
import { useTheme } from "@/hooks/ThemeContext";
import RevenueBarChart from "../ui/BarChart";

interface FinancialIndicatorsSectionProps {
  stockSymbol: string;
}

const FinancialIndicatorsSection = ({
  stockSymbol,
}: FinancialIndicatorsSectionProps) => {
  const { theme } = useTheme();
  const [financialIndicators, setFinancialIndicators] =
    useState<FinancialIndicators | null>(null);

  const [cashFlows, setCashFlows] = useState<CashFlows | null>(null);

  const [annualData, setAnnualData] = useState<FinancialIndicators[]>([]);

  useEffect(() => {
    getFinancialIndicators(stockSymbol).then((res) => {
      if (res.status) {
        setFinancialIndicators(res.data);
        setAnnualData(res.annualData);
      }
    });

    getCashFlows(stockSymbol).then((res) => {
      if (res.status) {
        setCashFlows(res.data);
      }
    });
  }, [stockSymbol]);

  return financialIndicators != null && cashFlows != null ? (
    <View style={{ marginHorizontal: 12 }}>
      <Text typography="headlineSmall">Định giá</Text>

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

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Vốn hoá thị trường</Text>
        <Text typography="titleMedium">
          {(financialIndicators?.market_cap / 1000000000).toFixed(2)} tỷ đồng
        </Text>
      </View>

      {/** -------------------------------------------- */}
      <Text typography="headlineSmall" style={{ marginTop: 24 }}>
        Khả năng sinh lời
      </Text>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginVertical: 4,
        }}
      >
        <Text typography="bodyLarge">
          Doanh thu:{" "}
          <Text typography="titleLarge">
            {(financialIndicators?.revenue / 1000000000).toFixed(2)} tỷ đồng
          </Text>
        </Text>

        <Text
          typography="titleLarge"
          color={
            financialIndicators?.revenue_yoy > 0
              ? theme.base.success
              : theme.base.error
          }
        >
          {financialIndicators?.revenue_yoy > 0 ? "+" : "-"}{" "}
          {(financialIndicators?.revenue_yoy * 100).toFixed(2)}%
        </Text>
      </View>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginVertical: 4,
        }}
      >
        <Text typography="bodyLarge">
          Lợi nhuận:{" "}
          <Text typography="titleLarge">
            {(financialIndicators?.net_income / 1000000000).toFixed(2)} tỷ đồng
          </Text>
        </Text>

        <Text
          typography="titleLarge"
          color={
            financialIndicators?.profit_yoy > 0
              ? theme.base.success
              : theme.base.error
          }
        >
          {financialIndicators?.profit_yoy > 0 ? "+" : "-"}{" "}
          {(financialIndicators?.profit_yoy * 100).toFixed(2)}%
        </Text>
      </View>

      <RevenueBarChart
        data={annualData.map((e) => {
          return {
            time: e?.year.toString(),
            revenue: e?.revenue / 1000000000,
            profit: e?.net_income / 1000000000,
          };
        })}
      />

      {/* <Text typography="titleMedium" style={{ marginTop: 12, marginBottom: 8 }}>
        {`Lợi nhuận (Tỷ đồng)`}
      </Text>
      <BarChart
        data={annualData.map((e) => {
          return {
            time: e?.year.toString(),
            value: e?.net_income / 1000000000,
          };
        })}
      /> */}

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
      <Text typography="headlineSmall" style={{ marginTop: 24 }}>
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

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Khả năng trả lãi</Text>
        <Text typography="titleMedium">
          {financialIndicators?.interest_coverage.toFixed(2)}
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
        <Text typography="bodyLarge">Thanh khoản tiền mặt</Text>
        <Text typography="titleMedium">
          {financialIndicators?.cash_ratio.toFixed(2)}
        </Text>
      </View>

      {/** -------------------------------------------- */}
      <Text typography="headlineSmall" style={{ marginTop: 24 }}>
        Dòng tiền
      </Text>

      <View
        style={{
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 12,
        }}
      >
        <Text typography="bodyLarge">Dòng tiền kinh doanh</Text>
        <Text typography="titleMedium">
          {(cashFlows?.cfo / 1000000000).toFixed(2)}
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
        <Text typography="bodyLarge">Dòng tiền đầu tư</Text>
        <Text typography="titleMedium">
          {(cashFlows?.cfi / 1000000000).toFixed(2)}
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
        <Text typography="bodyLarge">Dòng tiền tài chính</Text>
        <Text typography="titleMedium">
          {(cashFlows?.cff / 1000000000).toFixed(2)}
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
        <Text typography="bodyLarge">Dòng tiền tự do</Text>
        <Text typography="titleMedium">
          {((cashFlows?.cfo + cashFlows?.capex) / 1000000000).toFixed(2)}
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
        <Text typography="bodyLarge">Tiền cuối kỳ</Text>
        <Text typography="titleMedium">
          {(cashFlows?.cash_ending / 1000000000).toFixed(2)}
        </Text>
      </View>
    </View>
  ) : null;
};
export default FinancialIndicatorsSection;
