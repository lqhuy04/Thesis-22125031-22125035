import React, { useState } from "react";
import {
  ActivityIndicator,
  Modal,
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import { useForm } from "react-hook-form";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import { Text } from "@/components/ui/Text";
import ScreenHeader from "@/components/ui/ScreenHeader";
import { Input } from "@/components/ui/Input";
import SimpleLineIcons from "@expo/vector-icons/SimpleLineIcons";
import { router } from "expo-router";
import { sendOTPForgotPass } from "@/helpers/AuthenticationHelper";

const isEmailValid = (value: string): boolean => {
  if (!value) return true;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(value);
};

const ForgotPasswordEmail = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const { control, handleSubmit, watch } = useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState<string | undefined>();

  const email = watch("email");
  const isFormValid = !!email && isEmailValid(email);

  const handleEmailChange = (value: string) => {
    if (value && !isEmailValid(value)) {
      setEmailError(t("auth.emailFormatError"));
    } else {
      setEmailError(undefined);
    }
  };

  const onSubmit = async (data: any) => {
    if (!data.email) return setError(t("forgotPasswordFlow.emailRequiredError"));
    if (!isEmailValid(data.email)) return setEmailError(t("auth.emailFormatError"));

    setError("");
    setLoading(true);

    const response = await sendOTPForgotPass({ email: data.email });

    setLoading(false);

    if (!response.status)
      return setError(t("forgotPasswordFlow.emailNotFoundError"));

    router.push({
      pathname: "/OTP",
      params: { email: data.email, flow: "forgotPassword" },
    });
  };

  return (
    <View style={[styles.safe, { backgroundColor: theme.background.surface }]}>
      <ScreenHeader title={t("forgotPasswordFlow.screenTitle")} />

      <View style={styles.content}>
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

        {/* Icon + mô tả */}
        <View style={styles.header}>
          <View
            style={[
              styles.iconWrap,
              {
                backgroundColor: theme.base.primary + "12",
                borderColor: theme.base.primary + "30",
              },
            ]}
          >
            <SimpleLineIcons
              name="envelope"
              size={28}
              color={theme.base.primary}
            />
          </View>
          <Text
            typography="titleLarge"
            color={theme.text.primary}
            style={{ textAlign: "center" }}
          >
            {t("forgotPasswordFlow.emailVerificationTitle")}
          </Text>
          <Text
            typography="bodyMedium"
            color={theme.text.primary}
            style={{ opacity: 0.5, textAlign: "center", marginTop: 4 }}
          >
            {t("forgotPasswordFlow.emailVerificationDesc")}
          </Text>
        </View>

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
            label="Email"
            placeholder="username@gmail.com"
            required
            errorMessage={emailError}
            onChangeText={handleEmailChange}
          />
        </View>

        {/* Error */}
        {!!error && (
          <View
            style={[
              styles.banner,
              {
                backgroundColor: theme.base.error + "15",
                borderColor: theme.base.error + "40",
              },
            ]}
          >
            <SimpleLineIcons
              name="exclamation"
              size={13}
              color={theme.base.error}
            />
            <Text
              typography="labelLarge"
              color={theme.base.error}
              style={{ flex: 1 }}
            >
              {error}
            </Text>
          </View>
        )}

        {/* Button */}
        <TouchableOpacity
          style={[
            styles.button,
            {
              backgroundColor: isFormValid
                ? theme.base.primary
                : theme.border.default,
            },
          ]}
          onPress={handleSubmit(onSubmit)}
          disabled={loading || !isFormValid}
          activeOpacity={0.8}
        >
          <Text typography="titleLarge" color={theme.text.onPrimary}>
            {t("forgotPasswordFlow.sendOtpButton")}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default ForgotPasswordEmail;

const styles = StyleSheet.create({
  safe: { flex: 1 },
  content: { flex: 1, paddingHorizontal: 24, paddingTop: 32, gap: 16 },
  header: { alignItems: "center", gap: 8 },
  iconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  card: {
    borderRadius: 16,
    borderWidth: 0.5,
    padding: 16,
  },
  banner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
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
