import React from "react";
import { View, TouchableOpacity, Alert, StyleSheet } from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { signUp } from "@/helpers/AuthenticationHelper";
import { Input } from "../ui/Input";

interface SignUpComponentProps {
  onSuccess: () => void;
}

const SignUpComponent = ({ onSuccess }: SignUpComponentProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const { control, handleSubmit } = useForm();

  const onSubmit = (formData: any) => {
    signUp({
      email: formData?.email,
      password: formData?.password,
    }).then((response) => {
      if (response.status) {
        onSuccess();
      } else {
        Alert.alert(
          "Sign Up Failed",
          "Invalid email, phone number, or password.",
        );
      }
    });
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signUp")}
      </Text>
      <Text typography="bodyMedium" style={{ opacity: 0.5, marginTop: 4 }}>
        Tạo tài khoản để bắt đầu 🚀
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
          name="email"
          label={t("auth.email")}
          placeholder="username@gmail.com"
          required
        />

        <View
          style={[styles.divider, { backgroundColor: theme.border.default }]}
        />

        <Input
          control={control}
          name="password"
          label={t("auth.password")}
          placeholder={t("auth.passwordPlaceholder")}
          required
          secure
        />
        <Input
          control={control}
          name="confirmPassword"
          label={t("auth.confirmPassword")}
          placeholder={t("auth.confirmPasswordPlaceholder")}
          required
          secure
        />
      </View>

      {/* Submit */}
      <TouchableOpacity
        onPress={handleSubmit(onSubmit)}
        style={[styles.button, { backgroundColor: theme.base.primary }]}
        activeOpacity={0.8}
      >
        <Text typography="titleLarge" color={theme.text.onPrimary}>
          {t("auth.signUp")}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default SignUpComponent;

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
  divider: {
    height: 0.5,
    opacity: 0.6,
    marginVertical: 4,
  },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 4,
  },
});
