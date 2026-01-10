import React, { useState } from "react";
import { View, TextInput, StyleSheet, TouchableOpacity } from "react-native";
import { useForm, Controller } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";

const Authentication = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const { control, handleSubmit } = useForm();
  const [data, setData] = useState("");

  const onSubmit = (formData: any) => {
    setData(JSON.stringify(formData, null, 2));
  };

  return (
    <View
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
        justifyContent: "center",
      }}
    >
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signIn")}
      </Text>

      <Controller
        control={control}
        name="username"
        render={({ field: { onChange, value } }) => (
          <View>
            <Text
              typography="bodySmall"
              color={theme.text.primary}
              style={{ marginTop: 24 }}
            >
              {t("auth.username")}
            </Text>
            <TextInput
              style={{
                borderWidth: 1,
                borderColor: theme.border.default,
                borderRadius: 5,
                paddingVertical: 10,
                paddingHorizontal: 16,
                marginTop: 4,
              }}
              placeholder="username@gmail.com"
              placeholderTextColor={theme.text.secondary}
              value={value}
              onChangeText={onChange}
            />
          </View>
        )}
      />

      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, value } }) => (
          <View>
            <Text
              typography="bodySmall"
              color={theme.text.primary}
              style={{ marginTop: 24 }}
            >
              {t("auth.password")}
            </Text>
            <TextInput
              style={{
                borderWidth: 1,
                borderColor: theme.border.default,
                borderRadius: 5,
                paddingVertical: 10,
                paddingHorizontal: 16,
                marginTop: 4,
              }}
              placeholder={t("auth.passwordPlaceholder")}
              placeholderTextColor={theme.text.secondary}
              value={value}
              onChangeText={onChange}
            />
          </View>
        )}
      />

      <Text
        typography="bodySmall"
        color={theme.base.primary}
        style={{ marginTop: 4 }}
      >
        {t("auth.forgotPassword")}
      </Text>

      <TouchableOpacity
        onPress={handleSubmit(onSubmit)}
        style={{
          backgroundColor: theme.base.primary,
          paddingVertical: 8,
          borderRadius: 4,
          marginTop: 24,
          alignItems: "center",
        }}
      >
        <Text typography="titleLarge" color="#F2F4F7">
          {t("auth.signIn")}
        </Text>
      </TouchableOpacity>

      <Text style={styles.output}>{data}</Text>
    </View>
  );
};

export default Authentication;

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    justifyContent: "center",
    padding: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    padding: 10,
    marginBottom: 12,
    borderRadius: 5,
  },
  textArea: {
    height: 80,
  },
  output: {
    marginTop: 20,
  },
});
