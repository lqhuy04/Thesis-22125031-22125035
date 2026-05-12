import React, { useEffect } from "react";
import { Alert, StyleSheet, TouchableOpacity, View } from "react-native";
import * as Google from "expo-auth-session/providers/google";
import * as Facebook from "expo-auth-session/providers/facebook";
import * as WebBrowser from "expo-web-browser";
import FontAwesome from "@expo/vector-icons/FontAwesome";
import { Text } from "../ui/Text";
import { useTheme } from "@/hooks/ThemeContext";
import { socialLogin } from "@/helpers/AuthenticationHelper";
import { router } from "expo-router";
import * as AuthSession from "expo-auth-session";

WebBrowser.maybeCompleteAuthSession();

const redirectUri = AuthSession.makeRedirectUri({
  scheme: "stockrium",
});

console.log("Redirect URI:", redirectUri);

const SocialButtons = () => {
  const { theme } = useTheme();

  // ── Google ────────────────────────────────────────────────────────────────
  const [, googleResponse, googlePromptAsync] = Google.useAuthRequest({
    webClientId:
      "372062103134-ucu0jacbo5g104ofijuqf1jobnspstu1.apps.googleusercontent.com",
    androidClientId:
      "372062103134-jv08s6160qi9quhc6fjmv2ugkcn4b7ca.apps.googleusercontent.com",
    iosClientId:
      "372062103134-tt5avvnivu4f50cmau3p8l72rj6i24og.apps.googleusercontent.com",
    redirectUri: "http://localhost:8081",
  });

  console.log("Google Response:", googleResponse);

  useEffect(() => {
    if (googleResponse?.type === "success") {
      const token = googleResponse.authentication?.idToken;
      if (token) handleSocialLogin("google", token);
    }
  }, [googleResponse]);

  // ── Facebook ──────────────────────────────────────────────────────────────
  const [, fbResponse, fbPromptAsync] = Facebook.useAuthRequest({
    clientId: "670026132766795",
    redirectUri: "https://auth.expo.io/@zhuskyz/stockrium",
  });

  useEffect(() => {
    if (fbResponse?.type === "success") {
      const token = fbResponse.authentication?.accessToken;
      if (token) handleSocialLogin("facebook", token);
    }
  }, [fbResponse]);

  // ── Gọi API ───────────────────────────────────────────────────────────────
  const handleSocialLogin = async (
    provider: "google" | "facebook",
    token: string,
  ) => {
    const res = await socialLogin({ provider, token });
    if (res.status) {
      router.replace("/Tabs");
    } else {
      Alert.alert("Đăng nhập thất bại", "Vui lòng thử lại.");
    }
  };

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
        onPress={() => googlePromptAsync()}
        style={[
          styles.socialBtn,
          {
            backgroundColor: theme.background.bg,
            borderColor: theme.border.default,
          },
        ]}
      >
        <FontAwesome name="google" size={18} color="#EA4335" />
        <Text typography="titleMedium">Đăng nhập với Google</Text>
      </TouchableOpacity>

      {/* Facebook */}
      <TouchableOpacity
        activeOpacity={0.8}
        onPress={() => fbPromptAsync()}
        style={[
          styles.socialBtn,
          {
            backgroundColor: theme.background.bg,
            borderColor: theme.border.default,
          },
        ]}
      >
        <FontAwesome name="facebook-official" size={18} color="#1877F2" />
        <Text typography="titleMedium">Đăng nhập với Facebook</Text>
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
