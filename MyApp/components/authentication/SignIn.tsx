import React from "react";
import { View, TouchableOpacity, Alert } from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { signIn } from "@/helpers/AuthenticationHelper";
import { router } from "expo-router";
import { Input } from "../ui/Input";

const SignInComponent = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();

  const { control, handleSubmit } = useForm();

  const onSubmit = (formData: any) => {
    signIn({
      username: formData?.username,
      password: formData?.password,
    }).then((response) => {
      if (response.status) {
        router.push("/Home");
      } else {
        Alert.alert("Sign In Failed", "Invalid username or password.");
      }
    });
  };

  return (
    <View>
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signIn")}
      </Text>

      <Input
        control={control}
        name="username"
        label={t("auth.username")}
        placeholder="username@gmail.com"
        required={true}
      />

      <Input
        control={control}
        name="password"
        label={t("auth.password")}
        placeholder={t("auth.passwordPlaceholder")}
        required={true}
        secure={true}
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
    </View>
  );
};

export default SignInComponent;
