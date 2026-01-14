import React, { useState } from "react";
import { View, TextInput, TouchableOpacity } from "react-native";
import { Controller, Control } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { Ionicons } from "@expo/vector-icons";

type InputProps = {
  control: Control<any>;
  name: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  secure?: boolean;
};

export const Input = ({
  control,
  name,
  label,
  placeholder,
  required = false,
  secure = false,
}: InputProps) => {
  const { theme } = useTheme();

  const [hidden, setHidden] = useState(secure);

  return (
    <Controller
      control={control}
      name={name}
      render={({ field: { onChange, value } }) => (
        <View>
          <Text
            typography="bodySmall"
            color={theme.text.primary}
            style={{ marginTop: 24 }}
          >
            {label}
            {required && (
              <Text typography="bodySmall" color={theme.base.error}>
                *
              </Text>
            )}
          </Text>

          <View>
            <TextInput
              style={{
                borderWidth: 1,
                borderColor: theme.border.default,
                borderRadius: 5,
                paddingVertical: 10,
                paddingHorizontal: 16,
                marginTop: 4,
                color: theme.text.primary,
              }}
              placeholder={placeholder}
              placeholderTextColor={theme.text.secondary}
              value={value}
              onChangeText={onChange}
              secureTextEntry={hidden}
              autoCapitalize="none"
            />

            {secure && (
              <TouchableOpacity
                onPress={() => setHidden(!hidden)}
                style={{ position: "absolute", right: 12, top: 14 }}
              >
                <Ionicons
                  name={hidden ? "eye-off-outline" : "eye-outline"}
                  size={20}
                  color={theme.text.primary}
                />
              </TouchableOpacity>
            )}
          </View>
        </View>
      )}
    />
  );
};
