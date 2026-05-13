import React, { useState } from "react";
import {
  Alert,
  ActivityIndicator,
  StyleSheet,
  TouchableOpacity,
  View,
} from "react-native";
import FontAwesome from "@expo/vector-icons/FontAwesome";
import {
  GoogleSignin,
  statusCodes,
} from "@react-native-google-signin/google-signin";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { socialLogin } from "@/helpers/AuthenticationHelper";
import { router } from "expo-router";

GoogleSignin.configure({
  webClientId:
    "372062103134-ucu0jacbo5g104ofijuqf1jobnspstu1.apps.googleusercontent.com",
  iosClientId:
    "372062103134-tt5avvnivu4f50cmau3p8l72rj6i24og.apps.googleusercontent.com",
});

const SocialButtons = () => {
  const { theme } = useTheme();
  const [loadingProvider, setLoadingProvider] = useState<"google" | null>(null);

  const onPressGoogle = async () => {
    try {
      setLoadingProvider("google");
      await GoogleSignin.hasPlayServices();
      const result: any = await GoogleSignin.signIn();
      const idToken = result?.data?.idToken ?? result?.idToken;
      if (idToken) {
        await handleSocialLogin("google", idToken);
      } else {
        Alert.alert("Đăng nhập thất bại", "Không nhận được idToken.");
        setLoadingProvider(null);
      }
    } catch (e: any) {
      if (e?.code !== statusCodes.SIGN_IN_CANCELLED) {
        Alert.alert("Đăng nhập thất bại", "Vui lòng thử lại.");
      }
      setLoadingProvider(null);
    }
  };

  const handleSocialLogin = async (provider: "google", token: string) => {
    setLoadingProvider(provider);
    try {
      const res = await socialLogin({ provider, token });
      if (res.status) {
        router.replace("/Tabs");
      } else {
        Alert.alert("Đăng nhập thất bại", "Vui lòng thử lại.");
      }
    } finally {
      setLoadingProvider(null);
    }
  };

  const isLoading = loadingProvider !== null;

  return (
    <View style={{ gap: 10, marginTop: 8 }}>
      {/* Divider */}
      <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
        <View
          style={{
            flex: 1,
            height: 0.5,
            backgroundColor: theme.border.default,
          }}
        />
        <Text typography="labelLarge" style={{ opacity: 0.4 }}>
          hoặc
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
        <Text typography="titleMedium">Đăng nhập với Google</Text>
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
});

export default SocialButtons;
