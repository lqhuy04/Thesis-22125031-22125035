import React, { useState } from "react";
import {
  View,
  TouchableOpacity,
  Alert,
  StyleSheet,
  ActivityIndicator,
  Modal,
} from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { Text } from "@/components/ui/Text";
import { useLocalization } from "@/hooks/LocalizationContext";
import { signUp } from "@/helpers/AuthenticationHelper";
import { Input } from "../ui/Input";
import SocialButtons from "./SocialButtons";
import { router } from "expo-router";

interface SignUpComponentProps {
  onSuccess: () => void;
}

const validateEmail = (value: string): string | undefined => {
  if (!value) return undefined;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) return "Email không đúng định dạng.";
  return undefined;
};

const validatePassword = (value: string): string | undefined => {
  if (!value) return undefined;
  if (value.length < 8) return "Mật khẩu phải có ít nhất 8 ký tự.";
  if (!/[0-9]/.test(value)) return "Mật khẩu phải chứa ít nhất 1 chữ số.";
  if (!/[a-z]/.test(value)) return "Mật khẩu phải chứa ít nhất 1 chữ thường.";
  if (!/[A-Z]/.test(value)) return "Mật khẩu phải chứa ít nhất 1 chữ in hoa.";
  if (!/[^a-zA-Z0-9]/.test(value))
    return "Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt.";
  return undefined;
};

const SignUpComponent = ({ onSuccess }: SignUpComponentProps) => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const { control, handleSubmit, watch } = useForm();
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState<string | undefined>();
  const [passwordError, setPasswordError] = useState<string | undefined>();
  const [confirmError, setConfirmError] = useState<string | undefined>();

  const email = watch("email");
  const password = watch("password");
  const confirmPassword = watch("confirmPassword");

  const isFormValid =
    !!email &&
    !!password &&
    !!confirmPassword &&
    !validateEmail(email) &&
    !validatePassword(password) &&
    password === confirmPassword;

  const onSubmit = (formData: any) => {
    const emailErr = validateEmail(formData.email);
    const pwdError = validatePassword(formData.password);
    const confirmErr =
      formData.confirmPassword !== formData.password
        ? "Mật khẩu xác nhận không khớp."
        : undefined;

    setEmailError(emailErr);
    setPasswordError(pwdError);
    setConfirmError(confirmErr);

    if (emailErr || pwdError || confirmErr) return;

    setLoading(true);
    signUp({
      email: formData?.email,
      password: formData?.password,
    })
      .then((response) => {
        if (response.status) {
          router.push({
            pathname: "/OTP",
            params: { email: formData?.email, flow: "signUp" },
          });
          onSuccess();
        } else {
          Alert.alert(
            "Sign Up Failed",
            "Invalid email, phone number, or password.",
          );
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Validate live khi user sửa lại
  const handleEmailChange = (value: string) => {
    setEmailError(validateEmail(value));
  };

  const handlePasswordChange = (value: string) => {
    setPasswordError(validatePassword(value));
    if (confirmPassword) {
      setConfirmError(
        value !== confirmPassword ? "Mật khẩu xác nhận không khớp." : undefined,
      );
    }
  };

  const handleConfirmChange = (value: string) => {
    setConfirmError(
      value !== password ? "Mật khẩu xác nhận không khớp." : undefined,
    );
  };

  return (
    <View style={styles.container}>
      {/* Loading Modal */}
      <Modal
        visible={loading}
        transparent
        animationType="fade"
        statusBarTranslucent
      >
        <View style={styles.overlay}>
          <ActivityIndicator size="large" color={theme.base.primary} />
        </View>
      </Modal>

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
          errorMessage={emailError}
          onChangeText={handleEmailChange}
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
          errorMessage={passwordError}
          onChangeText={handlePasswordChange}
        />
        <Input
          control={control}
          name="confirmPassword"
          label={t("auth.confirmPassword")}
          placeholder={t("auth.confirmPasswordPlaceholder")}
          required
          secure
          errorMessage={confirmError}
          onChangeText={handleConfirmChange}
        />
      </View>

      {/* Submit */}
      <TouchableOpacity
        onPress={handleSubmit(onSubmit)}
        style={[
          styles.button,
          {
            backgroundColor: isFormValid
              ? theme.base.primary
              : theme.border.default,
          },
        ]}
        activeOpacity={0.8}
        disabled={!isFormValid}
      >
        <Text typography="titleLarge" color={theme.text.onPrimary}>
          {t("auth.signUp")}
        </Text>
      </TouchableOpacity>

      <SocialButtons />
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
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
  },
});
