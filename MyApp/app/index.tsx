import { Redirect } from "expo-router";
import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { getToken } from "@/helpers/api/TokenStorage";

export default function Index() {
  const [loading, setLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      setLoading(true);
      const token = await getToken();

      if (token != null) {
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
    return <Redirect href="/HomeTabs" />;
  }

  return <Redirect href="/Authentication" />;
}
