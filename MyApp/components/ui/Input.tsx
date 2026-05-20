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
  errorMessage?: string;
  onChangeText?: (value: string) => void;
};

export const Input = ({
  control,
  name,
  label,
  placeholder,
  required = false,
  secure = false,
  errorMessage,
  onChangeText,
}: InputProps) => {
  const { theme } = useTheme();
  const [hidden, setHidden] = useState(secure);

  return (
    <Controller
      control={control}
      name={name}
      render={({ field: { onChange, value } }) => (
        <View style={{ gap: 6 }}>
          {/* Label */}
          <Text
            typography="labelLarge"
            style={{ opacity: 0.55, marginLeft: 2 }}
            color={theme.text.primary}
          >
            {label}
            {required && (
              <Text typography="labelLarge" color={theme.base.error}>
                {" "}
                *
              </Text>
            )}
          </Text>

          {/* Input row */}
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              borderWidth: 1,
              borderColor: errorMessage
                ? theme.base.error
                : theme.border.default,
              borderRadius: 10,
              backgroundColor: theme.background.bg,
              paddingHorizontal: 12,
            }}
          >
            <TextInput
              style={{
                flex: 1,
                fontSize: 15,
                paddingVertical: 11,
                color: theme.text.primary,
              }}
              placeholder={placeholder}
              placeholderTextColor={theme.text.primary + "44"}
              value={value}
              onChangeText={(text) => {
                onChange(text);
                onChangeText?.(text);
              }}
              secureTextEntry={hidden}
              autoCapitalize="none"
            />

            {secure && (
              <TouchableOpacity
                onPress={() => setHidden((h) => !h)}
                style={{ padding: 6 }}
              >
                <Ionicons
                  name={hidden ? "eye-off" : "eye"}
                  size={16}
                  color={theme.text.primary + "66"}
                />
              </TouchableOpacity>
            )}
          </View>

          {/* Error message */}
          {!!errorMessage && (
            <Text
              typography="labelMedium"
              color={theme.base.error}
              style={{ marginLeft: 2 }}
            >
              {errorMessage}
            </Text>
          )}
        </View>
      )}
    />
  );
};
