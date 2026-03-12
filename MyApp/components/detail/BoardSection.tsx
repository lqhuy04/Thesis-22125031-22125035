import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Text } from "../ui/Text";
import {
    CompanyLeader,
  getCompanyLeaders,
} from "@/helpers/CompanyProfileHelpers";

interface BoardSectionProps {
  stockSymbol: string;
}

const BoardSection = ({ stockSymbol }: BoardSectionProps) => {
  const [leaders, setLeaders] = useState<CompanyLeader[]>([])

  useEffect(() => {
        getCompanyLeaders(stockSymbol).then((res) => {
            if (res.status) {
                setLeaders(res.data);
              }
        })
  }, [stockSymbol]);

  return  ( leaders.length > 0
?    <View style={{ marginTop: 12, marginHorizontal: 12 }}>
        {leaders.map((e, index) => {
            return <View key={index.toString()} style={{marginVertical: 8}}>
                <Text typography="titleMedium" style={{ marginBottom: 4 }}>
                    {e.full_name}
                </Text>
                <Text typography="bodyMedium" >
                    {e.position}
                </Text>
            </View>
        })}
      
      
    </View> : null
  );
};
export default BoardSection;
