import NewsSection from "@/components/detail/NewsSection";
import DetailHeader from "@/components/ui/DetailHeader";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { SearchStockItem } from "@/helpers/SearchHelper";
import { useLocalization } from "@/hooks/LocalizationContext";
import { useTheme } from "@/hooks/ThemeContext";
import React from "react";
import { ScrollView } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";

interface Props {
  stockItem: SearchStockItem;
}

const Detail = ({ stockItem }: Props) => {
  const { t } = useLocalization();
  const { theme } = useTheme();

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: theme.background.bg, padding: 12 }}
    >
      <ScreenHeader title={t("detail.screenTitle")} />

      <ScrollView style={{ flex: 1 }}>
        <DetailHeader item={stockItem} />

        <NewsSection stockSymbol={stockItem.symbol} />
      </ScrollView>
    </SafeAreaView>
  );
};

export default Detail;
