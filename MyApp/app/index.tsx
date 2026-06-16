import { Redirect } from "expo-router";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { getSession, isTokenExpired } from "@/helpers/api/TokenStorage";
import { hasSeenOnboarding } from "@/helpers/onboarding";

type Target = "onboarding" | "tabs" | "auth";

export default function Index() {
  const [loading, setLoading] = useState(true);
  const [target, setTarget] = useState<Target>("auth");

  useEffect(() => {
    const checkAuth = async () => {
      const seenOnboarding = await hasSeenOnboarding();
      if (!seenOnboarding) {
        setTarget("onboarding");
        setLoading(false);
        return;
      }

      const session = await getSession();
      const refresh_token = session?.refresh_token;

      if (refresh_token != null && !isTokenExpired(refresh_token)) {
        setTarget("tabs");
      } else {
        setTarget("auth");
      }

      setLoading(false);
    };

    checkAuth();
  }, []);

  if (loading) {
    return <View />;
  }

  if (target === "onboarding") {
    return <Redirect href="/Onboarding" />;
  }

  if (target === "tabs") {
    return <Redirect href="/Tabs" />;
  }

  return <Redirect href="/Authentication" />;
}
