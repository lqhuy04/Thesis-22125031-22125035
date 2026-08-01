import React, { useState } from "react";
import {
  ActivityIndicator,
  StyleSheet,
  TouchableOpacity,
  View,
  Modal,
} from "react-native";
import FontAwesome from "@expo/vector-icons/FontAwesome";
import {
  GoogleSignin,
  statusCodes,
} from "@react-native-google-signin/google-signin";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { socialLogin } from "@/helpers/AuthenticationHelper";
import { resolvePostAuthTarget } from "@/helpers/ProfileHelpers";
import { router } from "expo-router";
import { useLocalization } from "@/hooks/LocalizationContext";

GoogleSignin.configure({
  webClientId:
    "372062103134-ucu0jacbo5g104ofijuqf1jobnspstu1.apps.googleusercontent.com",
  iosClientId:
    "372062103134-tt5avvnivu4f50cmau3p8l72rj6i24og.apps.googleusercontent.com",
});

const SocialButtons = () => {
  const { theme } = useTheme();
  const { t } = useLocalization();
  const [loadingProvider, setLoadingProvider] = useState<"google" | null>(null);
  const [errorModal, setErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const showError = (message: string) => {
    setErrorMessage(message);
    setErrorModal(true);
  };

  const onPressGoogle = async () => {
    try {
      setLoadingProvider("google");
      await GoogleSignin.hasPlayServices();
      const result: any = await GoogleSignin.signIn();
      const idToken = result?.data?.idToken ?? result?.idToken;
      if (idToken) {
        await handleSocialLogin("google", idToken);
      } else {
        showError(t("auth.noIdToken"));
        setLoadingProvider(null);
      }
    } catch (e: any) {
      console.error("Google Sign-In Error:", e);
      if (e?.code !== statusCodes.SIGN_IN_CANCELLED) {
        showError(t("auth.tryAgain"));
      }
      setLoadingProvider(null);
    }
  };

  const handleSocialLogin = async (provider: "google", token: string) => {
    setLoadingProvider(provider);
    try {
      const res = await socialLogin({ token });
      if (res.status) {
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
        showError(t("auth.tryAgain"));
      }
    } finally {
      setLoadingProvider(null);
    }
  };

  const isLoading = loadingProvider !== null;

  return (
    <View style={{ gap: 10, marginTop: 8 }}>
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
              {t("auth.signInFailed")}
            </Text>
            <Text
              typography="bodyMedium"
              color={theme.text.primary}
              style={{ opacity: 0.6, textAlign: "center", marginTop: 8 }}
            >
              {errorMessage}
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

      {/* Divider */}
      <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
        <View
          style={{
            flex: 1,
            height: 0.5,
            backgroundColor: theme.border.default,
          }}
        />
        <Text
          typography="labelLarge"
          color={theme.text.primary}
          style={{ opacity: 0.4 }}
        >
          {t("auth.or")}
        </Text>
        <View
          style={{
            flex: 1,
            height: 0.5,
            backgroundColor: theme.border.default,
          }}
        />
      </View>

      {/* Google */}
      <TouchableOpacity
        activeOpacity={0.8}
        onPress={onPressGoogle}
        disabled={isLoading}
        style={[
          styles.socialBtn,
          {
            backgroundColor: theme.background.bg,
            borderColor: theme.border.default,
          },
          isLoading && { opacity: 0.6 },
        ]}
      >
        {loadingProvider === "google" ? (
          <ActivityIndicator size="small" color="#EA4335" />
        ) : (
          <FontAwesome name="google" size={18} color="#EA4335" />
        )}
        <Text typography="titleMedium" color={theme.text.primary}>
          {t("auth.signInWithGoogle")}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  socialBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    borderWidth: 0.5,
    borderRadius: 12,
    paddingVertical: 12,
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

export default SocialButtons;
