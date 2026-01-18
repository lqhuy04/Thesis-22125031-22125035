import React from "react";
import { View, TouchableOpacity, Alert } from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { signUp } from "@/helpers/AuthenticationHelper";
import { Input } from "../ui/Input";
import { router } from "expo-router";

const SignUpComponent = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const { control, handleSubmit } = useForm();

  const onSubmit = (formData: any) => {
    signUp({
      email: formData?.email,
      phoneNumber: formData?.phoneNumber,
      password: formData?.password,
    }).then((response) => {
      if (response.status) {
        router.push("../home/Home");
      } else {
        Alert.alert(
          "Sign Up Failed",
          "Invalid email, phone number, or password.",
        );
      }
    });
  };

  return (
    <View>
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signUp")}
      </Text>

      <Input
        control={control}
        name="email"
        label={t("auth.email")}
        placeholder="username@gmail.com"
        required={true}
      />

      <Input
        control={control}
        name="phoneNumber"
        label={t("auth.phoneNumber")}
        placeholder={t("auth.phoneNumberPlaceholder")}
      />

      <Input
        control={control}
        name="password"
        label={t("auth.password")}
        placeholder={t("auth.passwordPlaceholder")}
        required={true}
        secure={true}
      />

      <Input
        control={control}
        name="confirmPassword"
        label={t("auth.confirmPassword")}
        placeholder={t("auth.confirmPasswordPlaceholder")}
        required={true}
        secure={true}
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
    </View>
  );
};

export default SignUpComponent;
