import ScreenHeader from "@/components/ui/ScreenHeader";
import PriceChartComponent from "@/components/detail/PriceChartComponent";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams } from "expo-router";
import { MarketIndex } from "@/helpers/MarketHelpers";
import { Dimensions } from "react-native";
import { TreeMap } from "@/components/ui/TreeMap";

const IndexDetail = () => {
  const { theme } = useTheme();
  const { data } = useLocalSearchParams() || {};
  const indexItem: MarketIndex = data ? JSON.parse(data as string) : null;
  const screenWidth = Dimensions.get("window").width;

  const treeMapData = [
    {
      stock_id: "baf9b5f8-df86-49bd-83ae-ca3b744a5248",
      symbol: "VIC",
      company_name: "Tập đoàn Vingroup - Công ty Cổ phần",
      exchange: "HOSE",
      PriceChange: 3.1,
      PerPriceChange: 1.6,
      CeilingPrice: 201.0,
      FloorPrice: 174.8,
      RefPrice: 187.9,
      CurrentPrice: 191.0,
      TotalMatchVol: 5425000.0,
      TotalMatchVal: 1004722700000.0,
    },
    {
      stock_id: "3f887af4-212f-4a41-ab02-fb406404ad81",
      symbol: "VHM",
      company_name: "Công ty Cổ phần Vinhomes",
      exchange: "HOSE",
      PriceChange: 9.4,
      PerPriceChange: 6.9,
      CeilingPrice: 145.1,
      FloorPrice: 126.3,
      RefPrice: 135.7,
      CurrentPrice: 145.1,
      TotalMatchVol: 6841800.0,
      TotalMatchVal: 961348480000.0,
    },
    {
      stock_id: "358581c9-1a12-4e09-b149-83eef68efd77",
      symbol: "VPI",
      company_name: "Công ty Cổ phần Đầu tư Văn Phú - Invest",
      exchange: "HOSE",
      PriceChange: -0.7,
      PerPriceChange: -1.1,
      CeilingPrice: 65.8,
      FloorPrice: 57.2,
      RefPrice: 61.5,
      CurrentPrice: 60.8,
      TotalMatchVol: 5706700.0,
      TotalMatchVal: 348372940000.0,
    },
    {
      stock_id: "5a1bf188-9e81-4e7f-b6f3-5414ead84bca",
      symbol: "VRE",
      company_name: "Công ty Cổ phần Vincom Retail",
      exchange: "HOSE",
      PriceChange: 0.85,
      PerPriceChange: 3.0,
      CeilingPrice: 30.6,
      FloorPrice: 26.6,
      RefPrice: 28.6,
      CurrentPrice: 29.45,
      TotalMatchVol: 6682700.0,
      TotalMatchVal: 194335115000.0,
    },
    {
      stock_id: "19277333-3538-4943-993e-3233d5324915",
      symbol: "NVL",
      company_name: "Công ty Cổ phần Tập đoàn Đầu tư Địa ốc No Va",
      exchange: "HOSE",
      PriceChange: 0.1,
      PerPriceChange: 0.6,
      CeilingPrice: 18.2,
      FloorPrice: 15.9,
      RefPrice: 17.05,
      CurrentPrice: 17.15,
      TotalMatchVol: 11247700.0,
      TotalMatchVal: 191718830000.0,
    },
    {
      stock_id: "2fb6c687-a218-49eb-8c73-d8c0572b691d",
      symbol: "KBC",
      company_name: "Tổng Công ty Phát triển Đô Thị Kinh Bắc – Công ty Cổ phần",
      exchange: "HOSE",
      PriceChange: -0.05,
      PerPriceChange: -0.1,
      CeilingPrice: 37.5,
      FloorPrice: 32.6,
      RefPrice: 35.05,
      CurrentPrice: 35.0,
      TotalMatchVol: 4271200.0,
      TotalMatchVal: 149345305000.0,
    },
    {
      stock_id: "55d71816-c25e-4893-af66-4cf3fea7656a",
      symbol: "DXG",
      company_name: "Công ty Cổ phần Tập đoàn Đất Xanh",
      exchange: "HOSE",
      PriceChange: 0.1,
      PerPriceChange: 0.7,
      CeilingPrice: 15.9,
      FloorPrice: 13.9,
      RefPrice: 14.9,
      CurrentPrice: 15.0,
      TotalMatchVol: 8153900.0,
      TotalMatchVal: 122082980000.0,
    },
    {
      stock_id: "ed84f677-a56f-49ea-a1f0-b823f1e9c2b8",
      symbol: "PDR",
      company_name: "Công ty Cổ phần Phát triển Bất động sản Phát Đạt",
      exchange: "HOSE",
      PriceChange: 0.0,
      PerPriceChange: 0.0,
      CeilingPrice: 17.25,
      FloorPrice: 15.05,
      RefPrice: 16.15,
      CurrentPrice: 16.15,
      TotalMatchVol: 5076700.0,
      TotalMatchVal: 81969550000.0,
    },
    {
      stock_id: "efb1d710-2b4b-4208-8e91-43ad2ddb933f",
      symbol: "TCH",
      company_name: "Công ty Cổ phần Đầu tư Dịch vụ Tài chính Hoàng Huy",
      exchange: "HOSE",
      PriceChange: 0.0,
      PerPriceChange: 0.0,
      CeilingPrice: 18.25,
      FloorPrice: 15.95,
      RefPrice: 17.1,
      CurrentPrice: 17.1,
      TotalMatchVol: 5979500.0,
      TotalMatchVal: 102208330000.0,
    },
    {
      stock_id: "5554cf08-bac7-433a-bc3a-5705fcf9fc1f",
      symbol: "DIG",
      company_name: "Tổng Công ty Cổ phần Đầu tư Phát triển Xây dựng",
      exchange: "HOSE",
      PriceChange: 0.0,
      PerPriceChange: 0.0,
      CeilingPrice: 15.35,
      FloorPrice: 13.35,
      RefPrice: 14.35,
      CurrentPrice: 14.35,
      TotalMatchVol: 5230400.0,
      TotalMatchVal: 75428815000.0,
    },
  ];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background.bg }}>
      <ScreenHeader title={indexItem?.IndexName ?? "Chi tiết chỉ số"} />
      <ScrollView>
        {indexItem && (
          <PriceChartComponent
            symbol={indexItem?.IndexId}
            isMarketIndex={true}
          />
        )}

        <TreeMap
          data={treeMapData}
          width={screenWidth}
          height={300}
          title="Doanh thu theo danh mục"
          padding={2}
        />
      </ScrollView>
    </SafeAreaView>
  );
};

export default IndexDetail;
