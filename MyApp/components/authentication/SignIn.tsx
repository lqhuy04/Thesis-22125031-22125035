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
import {
  resendVerificationEmail,
  signIn,
} from "@/helpers/AuthenticationHelper";
import { resolvePostAuthTarget } from "@/helpers/ProfileHelpers";
import { router } from "expo-router";
import { Input } from "../ui/Input";
import SocialButtons from "./SocialButtons";

const SignInComponent = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const { control, handleSubmit } = useForm();
  const [loading, setLoading] = useState(false);
  const [errorModal, setErrorModal] = useState(false);
  const [unverifiedModal, setUnverifiedModal] = useState(false);
  const [submittedUsername, setSubmittedUsername] = useState("");

  const onSubmit = (formData: any) => {
    const email = formData?.username?.trim() ?? "";
    const password = formData?.password?.trim() ?? "";

    // Reset modals trước mỗi lần submit
    setErrorModal(false);
    setUnverifiedModal(false);

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !password || !emailRegex.test(email)) {
      setErrorModal(true);
      return;
    }

    setLoading(true);
    setSubmittedUsername(email);
    signIn({ email, password })
      .then(async (response) => {
        if (response.status) {
          const nextRoute = await resolvePostAuthTarget();
          if (nextRoute === "/Tabs") {
            router.replace("/Tabs");
          } else {
            router.replace({
              pathname: "/RiskAppetite",
              params: { onboarding: "1" },
            });
          }
        } else {
          if (response.errorCode === 403001) {
            setUnverifiedModal(true);
          } else {
            setErrorModal(true);
          }
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <View style={styles.container}>
      {/* Unverified Account Modal */}
      <Modal
        visible={unverifiedModal}
        transparent
        animationType="fade"
        statusBarTranslucent
      >
        <View style={styles.overlay}>
          <View
            style={[styles.modalCard, { backgroundColor: theme.background.bg }]}
          >
            <Text typography="titleLarge" style={{ textAlign: "center" }}>
              {t("auth.unverifiedTitle")}
            </Text>
            <Text
              typography="bodyMedium"
              style={{ opacity: 0.6, textAlign: "center", marginTop: 8 }}
            >
              {t("auth.unverifiedBody")}
            </Text>
            <TouchableOpacity
              style={[
                styles.modalButton,
                { backgroundColor: theme.base.primary },
              ]}
              onPress={() => {
                resendVerificationEmail({ email: submittedUsername }).then(
                  () => {
                    setUnverifiedModal(false);
                    router.push({
                      pathname: "/OTP",
                      params: { email: submittedUsername, flow: "signUp" },
                    });
                  },
                );
              }}
              activeOpacity={0.8}
            >
              <Text typography="titleMedium" color={theme.text.onPrimary}>
                {t("auth.goToVerify")}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

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
              {t("auth.signInFailedTitle")}
            </Text>
            <Text
              typography="bodyMedium"
              color={theme.text.primary}
              style={{ opacity: 0.6, textAlign: "center", marginTop: 8 }}
            >
              {t("auth.signInFailedBody")}
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

      {/* Header */}
      <Text typography="headlineSmall" color={theme.text.primary}>
        {t("auth.signIn")}
      </Text>
      <Text
        typography="bodyLarge"
        color={theme.text.primary}
        style={{ opacity: 0.8, marginTop: 4 }}
      >
        {t("auth.welcome")}
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
          onPress={() => router.push("./InputEmail")}
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
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color={theme.text.onPrimary} />
        ) : (
          <Text typography="titleLarge" color={theme.text.onPrimary}>
            {t("auth.signIn")}
          </Text>
        )}
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
    paddingHorizontal: 32,
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
