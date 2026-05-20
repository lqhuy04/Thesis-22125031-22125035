import React, { useState } from "react";
import {
  View,
  TouchableOpacity,
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

const validateEmail = (value: string, t: (k: string) => string) => {
  if (!value) return undefined;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) return t("auth.emailInvalid");
  return undefined;
};

const validatePassword = (value: string, t: (k: string) => string) => {
  if (!value) return undefined;
  if (value.length < 8) return t("changePass.validateMinLength");
  if (!/[0-9]/.test(value)) return t("changePass.validateNumber");
  if (!/[a-z]/.test(value)) return t("changePass.validateLower");
  if (!/[A-Z]/.test(value)) return t("changePass.validateUpper");
  if (!/[^a-zA-Z0-9]/.test(value)) return t("changePass.validateSpecial");
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
  const [errorModal, setErrorModal] = useState(false);

  const email = watch("email");
  const password = watch("password");
  const confirmPassword = watch("confirmPassword");

  const isFormValid =
    !!email &&
    !!password &&
    !!confirmPassword &&
    !validateEmail(email, t) &&
    !validatePassword(password, t) &&
    password === confirmPassword;

  const onSubmit = (formData: any) => {
    const emailErr = validateEmail(formData.email, t);
    const pwdError = validatePassword(formData.password, t);
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
          setErrorModal(true);
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Validate live khi user sửa lại
  const handleEmailChange = (value: string) => {
    setEmailError(validateEmail(value, t));
  };

  const handlePasswordChange = (value: string) => {
    setPasswordError(validatePassword(value, t));
    if (confirmPassword) {
      setConfirmError(
        value !== confirmPassword
          ? t("auth.confirmPasswordMismatch")
          : undefined,
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
      {/* Header */}
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signUp")}
      </Text>
      <Text
        typography="bodyLarge"
        color={theme.text.primary}
        style={{ opacity: 0.8, marginTop: 4 }}
      >
        {t("auth.signUpWelcome")}
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
        {loading ? (
          <ActivityIndicator color={theme.text.onPrimary} />
        ) : (
          <Text typography="titleLarge" color={theme.text.onPrimary}>
            {t("auth.signUp")}
          </Text>
        )}
      </TouchableOpacity>

      <SocialButtons />

      {/* Error Modal */}
      <Modal
        visible={errorModal}
        transparent
        animationType="fade"
        statusBarTranslucent
      >
        <View style={styles.overlay}>
          <View
            style={[styles.modalCard, { backgroundColor: theme.background.bg }]}
          >
            <Text
              typography="titleLarge"
              color={theme.text.primary}
              style={{ textAlign: "center" }}
            >
              {t("auth.signUpFailedTitle")}
            </Text>
            <Text
              typography="bodyMedium"
              color={theme.text.primary}
              style={{ opacity: 0.6, textAlign: "center", marginTop: 8 }}
            >
              {t("auth.signUpFailedBody")}
            </Text>
            <TouchableOpacity
              style={[
                styles.modalButton,
                { backgroundColor: theme.base.primary },
              ]}
              onPress={() => setErrorModal(false)}
              activeOpacity={0.8}
            >
              <Text typography="titleMedium" color={theme.text.onPrimary}>
                {t("auth.retry")}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
    gap: 12,
    marginTop: 8,
  },
  button: {
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
    marginTop: 4,
  },
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalCard: {
    width: "100%",
    borderRadius: 20,
    padding: 24,
    alignItems: "center",
    gap: 4,
  },
  modalButton: {
    marginTop: 16,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 40,
    alignItems: "center",
  },
});
