import React, { useEffect, useState } from 'react'
import { View } from 'react-native'
import { Text } from "../ui/Text";
import { useLocalization } from '@/hooks/LocalizationContext';
import { useTheme } from '@/hooks/ThemeContext';
import { fetchFundamentalAnalysisIndexes, FundamentalAnalysisIndexes } from '@/helpers/DetailHelpers';

interface FundamentalAnalysisMetricsSectionProps {
  stock_symbol: string;
}

const FundamentalAnalysisMetricsSection = ({stock_symbol}: FundamentalAnalysisMetricsSectionProps) => {
    const { t } = useLocalization();
    const { theme } = useTheme();
    const [metrics, setMetrics] = useState<FundamentalAnalysisIndexes | null>(null)

    useEffect(()=> {
        fetchFundamentalAnalysisIndexes(stock_symbol).then((data) => {
            if(data.status) {
                setMetrics(data.data)
            }
        })
    }, []);
    
  return <View style={{marginTop: 24}}>
    <Text typography="titleLarge" >
          {t("fundamentalAnalysis.fundamentalAnalysisMetricsSectionTitle")}
    </Text>

    <View style={{padding: 8, marginTop: 16, backgroundColor: theme.background.surface, borderRadius: 4}}>
        <View style={{flexDirection: 'row', justifyContent:'space-between', marginVertical: 4}}>
              <Text typography='titleMedium'>
              {t("fundamentalAnalysis.PE")}
              </Text>
              <Text typography='bodyMedium'>
              {metrics?.pe_ratio}
              </Text>
        </View>

        <View style={{flexDirection: 'row', justifyContent:'space-between', marginVertical: 4}}>
              <Text typography='titleMedium'>
              {t("fundamentalAnalysis.PB")}
              </Text>
              <Text typography='bodyMedium'>
              {metrics?.pb_ratio}
              </Text>
        </View>

        <View style={{flexDirection: 'row', justifyContent:'space-between', marginVertical: 4}}>
              <Text typography='titleMedium'>
              {t("fundamentalAnalysis.EPS")}
              </Text>
              <Text typography='bodyMedium'>
              {metrics?.eps}
              </Text>
        </View>

        <View style={{flexDirection: 'row', justifyContent:'space-between', marginVertical: 4}}>
              <Text typography='titleMedium'>
              {t("fundamentalAnalysis.marketCap")}
              </Text>
              <Text typography='bodyMedium'>
              {metrics?.market_cap_billion}
              </Text>
        </View>

        <View style={{flexDirection: 'row', justifyContent:'space-between', marginVertical: 4}}>
              <Text typography='titleMedium'>
              {t("fundamentalAnalysis.shareOutstanding")}
              </Text>
              <Text typography='bodyMedium'>
              {metrics?.shares_outstanding_million}
              </Text>
        </View>

        <View style={{flexDirection: 'row', justifyContent:'space-between', marginVertical: 4}}>
              <Text typography='titleMedium'>
              {t("fundamentalAnalysis.ROE")}
              </Text>
              <Text typography='bodyMedium'>
              {metrics?.roe}
              </Text>
        </View>
        
    </View>
  </View>
}

export default FundamentalAnalysisMetricsSection