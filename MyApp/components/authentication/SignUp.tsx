import React, { useState } from "react";
import { View, TextInput, TouchableOpacity } from "react-native";
import { useForm, Controller } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";

const SignUpComponent = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const { control, handleSubmit } = useForm();
  const [data, setData] = useState("");

  const onSubmit = (formData: any) => {
    setData(JSON.stringify(formData, null, 2));
  };

  return (
    <View>
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signUp")}
      </Text>

      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, value } }) => (
          <View>
            <Text
              typography="bodySmall"
              color={theme.text.primary}
              style={{ marginTop: 24 }}
            >
              {t("auth.email")}
              <Text typography="bodySmall" color={theme.base.error}>
                *
              </Text>
            </Text>
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
        name="phoneNumber"
        render={({ field: { onChange, value } }) => (
          <View>
            <Text
              typography="bodySmall"
              color={theme.text.primary}
              style={{ marginTop: 24 }}
            >
              {t("auth.phoneNumber")}
              <Text typography="bodySmall" color={theme.base.error}>
                *
              </Text>
            </Text>
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
              placeholder={t("auth.phoneNumberPlaceholder")}
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
              <Text typography="bodySmall" color={theme.base.error}>
                *
              </Text>
            </Text>
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
              placeholder={t("auth.passwordPlaceholder")}
              placeholderTextColor={theme.text.secondary}
              value={value}
              onChangeText={onChange}
            />
          </View>
        )}
      />

      <Controller
        control={control}
        name="confirmPassword"
        render={({ field: { onChange, value } }) => (
          <View>
            <Text
              typography="bodySmall"
              color={theme.text.primary}
              style={{ marginTop: 24 }}
            >
              {t("auth.confirmPassword")}
              <Text typography="bodySmall" color={theme.base.error}>
                *
              </Text>
            </Text>
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
              placeholder={t("auth.confirmPasswordPlaceholder")}
              placeholderTextColor={theme.text.secondary}
              value={value}
              onChangeText={onChange}
            />
          </View>
        )}
      />

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
          {t("auth.signUp")}
        </Text>
      </TouchableOpacity>

      <Text>{data}</Text>
    </View>
  );
};

export default SignUpComponent;
