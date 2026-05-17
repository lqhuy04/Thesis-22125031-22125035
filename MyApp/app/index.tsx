import { Redirect } from "expo-router";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { getSession, isTokenExpired } from "@/helpers/api/TokenStorage";

export default function Index() {
  const [loading, setLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      setLoading(true);
      const session = await getSession();
      const refresh_token = session?.refresh_token;

      if (refresh_token != null && !isTokenExpired(refresh_token)) {
        setIsLoggedIn(true);
      }

      setLoading(false);
    };

    checkAuth();
  }, []);

  if (loading) {
    return <View />;
  }

  if (isLoggedIn) {
    return <Redirect href="/Tabs" />;
  }

  return <Redirect href="/Authentication" />;
}
