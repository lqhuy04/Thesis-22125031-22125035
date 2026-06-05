import { Platform } from "react-native";
import Constants from "expo-constants";

// Backend đã deploy trên Railway (dùng cho bản production build)
const PRODUCTION_API_URL = "https://backend-server-production-1625.up.railway.app/";

export const getBaseUrl = (): string => {
  // Bản production (build release) → luôn gọi backend đã deploy
  if (!__DEV__) {
    return PRODUCTION_API_URL;
  }

  // --- Development: chạy với Metro bundler ---
  if (Platform.OS === "ios") {
    return "http://localhost:8000/";
  }

  // Expo tự biết IP máy tính đang chạy Metro bundler
  const debuggerHost = Constants.expoConfig?.hostUri;
  const ip = debuggerHost?.split(":")[0];

  return ip ? `http://${ip}:8000/` : "http://10.0.2.2:8000/";
};
