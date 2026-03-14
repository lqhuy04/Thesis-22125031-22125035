import React, { useState } from "react";
import { KeyboardAvoidingView, ScrollView } from "react-native";
import { useTheme } from "@/hooks/ThemeContext";
import SignInComponent from "@/components/authentication/SignIn";
import SignUpComponent from "@/components/authentication/SignUp";
import AuthenticationTab from "@/components/authentication/AuthenticationTab";
import { SafeAreaView } from "react-native-safe-area-context";

const Authentication = () => {
  const [tab, setTab] = useState<"signIn" | "signUp">("signIn");

  const { theme } = useTheme();

  return (
    <SafeAreaView
      style={{
        padding: 12,
        backgroundColor: theme.background.bg,
        flex: 1,
      }}
    >
      <AuthenticationTab tab={tab} setTab={setTab} />

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={"padding"}>
        <ScrollView keyboardShouldPersistTaps="handled">
          {tab === "signIn" ? <SignInComponent /> : <SignUpComponent />}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export default Authentication;
