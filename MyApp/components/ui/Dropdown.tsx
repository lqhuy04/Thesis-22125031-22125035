import React, { useEffect } from "react";
import { SelectList } from 'react-native-dropdown-select-list'
import { fontFamily } from "@/constants/fonts";
import { useTheme } from "@/hooks/ThemeContext";
import { View } from "react-native";
import { Text } from "@/components/ui/Text";

interface Props {
    data: {
        key: any;
        value: any;
    }[],
    placeholder: string,
    label: string,
    setSelected: (val: string) => void,
    value: string,
    required?: boolean,
} 

const DropDown = ({data, placeholder, label, setSelected, value, required}: Props) => {
    const { theme } = useTheme();

    return <View>
        <Text
            typography="bodySmall"
            color={theme.text.primary}
            style={{ marginTop: 24, marginBottom: 4 }}
          >
            {label}
            {required && (
              <Text typography="bodySmall" color={theme.base.error}>
                *
              </Text>
            )}
        </Text>
        
        <SelectList
            defaultOption={data.find(e => e?.key === value)}
            setSelected={setSelected} 
            data={data}  
            search={false}
            boxStyles={
            {borderWidth: 1,
                borderColor: theme.border.default,
                borderRadius: 5,
                paddingTop: 12,
                paddingBottom: 10,
                paddingHorizontal: 16,
                marginTop: 4,
            }}
            dropdownStyles={
                {borderWidth: 1,
                    borderColor: theme.border.default,
                    borderRadius: 5,
                    marginTop: 16,
                }
            }
            inputStyles={
                {fontSize: 16,
                    lineHeight: 20,
                    letterSpacing: 0.15,
                    fontFamily: fontFamily.medium}
            }
            dropdownTextStyles={
                {fontSize: 16,
                    lineHeight: 24,
                    letterSpacing: 0.5,
                    fontFamily: fontFamily.regular,}
            }
            placeholder={placeholder}
        />
    </View> 

}

export default DropDown