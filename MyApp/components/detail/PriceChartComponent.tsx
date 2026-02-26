import React, { useState, useEffect} from "react";
import { fetchStockData, StockData } from "@/helpers/DetailHelpers";
import { ActivityIndicator, TouchableOpacity, View } from "react-native";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import PriceLineGraph from "../ui/PriceLineChart";
import PriceCandleChart from "../ui/PriceCandleChart";

interface Props {
    stockSymbol: string
}

const PriceChartComponent = ({stockSymbol} : Props) => {
    const { theme } = useTheme();
    const [chartType, setChartType] = useState<'Line' | 'Candlestick'>('Line');
    const [loading, setLoading] = useState<boolean>(false);
    const [option, setOption] = useState<"1D" | "1W" | "1M" | "1Y" | "5Y">("1D")
    const [data, setData] = useState<StockData[]>([]);

    useEffect(() => {
        setLoading(true);
        fetchStockData(stockSymbol, option ).then((stockRes) => {
          setLoading(false);
          if (stockRes?.status) {
            setData(stockRes.data);
          }
        });
    }, [stockSymbol, option]);

    return <View>
        
    <View>
        <View style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between'}}> 
            <Text typography="titleLarge">
                hihihihihihi
            </Text>

            <TouchableOpacity 
                onPress={() => {
                    if(chartType === 'Line') {
                        setChartType('Candlestick')
                    } else {
                        setChartType('Line')
                    }
                }}
            style={{height:30, width: 30, backgroundColor: 'red'}}/>
        </View>
        { 
        loading ?  <View style={{height: 300, justifyContent: 'center',
            alignItems: 'center',}}>
            <ActivityIndicator size="large" color={theme.base.primary} />
          </View> :
        chartType === 'Line' ? <PriceLineGraph data={data} option={option}/> : <PriceCandleChart data={data}/>}
    </View>
    
            
  



<View style={{flexDirection: 'row', alignItems: "center", justifyContent: "space-between"}}>
        <View style={{backgroundColor: option ==='1D' ? theme.base.primary : theme.background.surface, padding: 4, borderRadius: 2}}>
            <Text typography="titleMedium" color={option ==='1D' ? theme.text.onPrimary : theme.text.primary} onPress={() => setOption("1D")} >
                1D
            </Text>
        </View>
        <View style={{backgroundColor: option ==='1W' ? theme.base.primary : theme.background.surface, padding: 4, borderRadius: 2}}>
            <Text typography="titleMedium" color={option ==='1W' ? theme.text.onPrimary : theme.text.primary} onPress={() => setOption("1W")} >
                1W
            </Text>
        </View>
        <View style={{backgroundColor: option ==='1M' ? theme.base.primary : theme.background.surface, padding: 4, borderRadius: 2}}>
            <Text typography="titleMedium" color={option ==='1M' ? theme.text.onPrimary : theme.text.primary} onPress={() => setOption("1M")} >
                1M
            </Text>
        </View>
        <View style={{backgroundColor: option ==='1Y' ? theme.base.primary : theme.background.surface, padding: 4, borderRadius: 2}}>
            <Text typography="titleMedium" color={option ==='1Y' ? theme.text.onPrimary : theme.text.primary} onPress={() => setOption("1Y")} >
                1Y
            </Text>
        </View>
        <View style={{backgroundColor: option ==='5Y' ? theme.base.primary : theme.background.surface, padding: 4, borderRadius: 2}}>
            <Text typography="titleMedium" color={option ==='5Y' ? theme.text.onPrimary : theme.text.primary} onPress={() => setOption("5Y")} >
                5Y
            </Text>
        </View>
          </View>
    </View>
}

export default PriceChartComponent