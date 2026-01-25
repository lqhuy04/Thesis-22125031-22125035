import React, { useState } from "react";
import { KeyboardAvoidingView, ScrollView } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import { useLocalization } from "@/hooks/LocalizationContext";
import SignInComponent from "@/components/authentication/SignIn";
import SignUpComponent from "@/components/authentication/SignUp";
import { Button } from "@react-navigation/elements";
import AuthenticationTab from "@/components/authentication/AuthenticationTab";
import { SafeAreaView } from "react-native-safe-area-context";

const Authentication = () => {
  const [tab, setTab] = useState<"signIn" | "signUp">("signIn");

  const { theme, toggleTheme } = useTheme();
  const { setLanguage } = useLocalization();

  return (
    <SafeAreaView
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
        paddingTop: 80,
      }}
    >
      <AuthenticationTab tab={tab} setTab={setTab} />

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={"padding"}>
        <ScrollView keyboardShouldPersistTaps="handled">
          {tab === "signIn" ? <SignInComponent /> : <SignUpComponent />}

          <Button
            onPress={() => {
              toggleTheme();
            }}
          >
            Toggle Theme
          </Button>
          <Button
            onPress={() => {
              setLanguage("en");
            }}
          >
            English
          </Button>
          <Button
            onPress={() => {
              setLanguage("vi");
            }}
          >
            Vietnamese
          </Button>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export default Authentication;
