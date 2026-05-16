import { Platform } from "react-native";
import Constants from "expo-constants";

export const getBaseUrl = (): string => {
  if (Platform.OS === "ios") {
    return "http://localhost:8000/";
  }

  // Expo tự biết IP máy tính đang chạy Metro bundler
  const debuggerHost = Constants.expoConfig?.hostUri;
  const ip = debuggerHost?.split(":")[0];

  return ip ? `http://${ip}:8000/` : "http://10.0.2.2:8000/";
};
