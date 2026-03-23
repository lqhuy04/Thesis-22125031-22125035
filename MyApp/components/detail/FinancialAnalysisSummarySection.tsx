import { getFinancialAnalysisSummary } from "@/helpers/FundamentalAnalysisHelpers";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import Markdown from "react-native-markdown-display";

interface Props {
  stockSymbol: string;
}

const FinancialAnalysisSummarySection = ({ stockSymbol }: Props) => {
  const [summary, setSummary] = useState<string | null>(null);

  useEffect(() => {
    getFinancialAnalysisSummary(stockSymbol).then((res) => {
      if (res.status) {
        setSummary(res.data);
      }
    });
  }, [stockSymbol]);

  return (
    <View>
      {summary ? (
        <View style={{ marginVertical: 12, marginHorizontal: 12 }}>
          <Markdown>{summary}</Markdown>
        </View>
      ) : null}
    </View>
  );
};

export default FinancialAnalysisSummarySection;
