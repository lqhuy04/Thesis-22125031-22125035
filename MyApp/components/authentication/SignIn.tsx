import React from "react";
import { View, TouchableOpacity, Alert, StyleSheet } from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { signIn } from "@/helpers/AuthenticationHelper";
import { router } from "expo-router";
import { Input } from "../ui/Input";
import SocialButtons from "./SocialButtons";

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
        router.replace("/Tabs");
      } else {
        Alert.alert("Sign In Failed", "Invalid username or password.");
      }
    });
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signIn")}
      </Text>
      <Text typography="bodyMedium" style={{ opacity: 0.5, marginTop: 4 }}>
        Chào mừng bạn trở lại 👋
      </Text>

      {/* Card */}
      <View
        style={[
          styles.card,
          {
            backgroundColor: theme.background.bg,
            borderColor: theme.border.default,
          },
        ]}
      >
        <Input
          control={control}
          name="username"
          label={t("auth.username")}
          placeholder="username@gmail.com"
          required
        />
        <Input
          control={control}
          name="password"
          label={t("auth.password")}
          placeholder={t("auth.passwordPlaceholder")}
          required
          secure
        />

        {/* Forgot password */}
        <TouchableOpacity
          onPress={() => {
            router.push("./InputEmail");
          }}
          style={{ alignSelf: "flex-end", marginTop: 4 }}
        >
          <Text typography="labelLarge" color={theme.base.primary}>
            {t("auth.forgotPassword")}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Submit */}
      <TouchableOpacity
        onPress={handleSubmit(onSubmit)}
        style={[styles.button, { backgroundColor: theme.base.primary }]}
        activeOpacity={0.8}
      >
        <Text typography="titleLarge" color={theme.text.onPrimary}>
          {t("auth.signIn")}
        </Text>
      </TouchableOpacity>

      <SocialButtons />
    </View>
  );
};

export default SignInComponent;

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  card: {
    borderRadius: 16,
    borderWidth: 0.5,
    padding: 16,
    gap: 4,
    marginTop: 8,
  },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 4,
  },
});
