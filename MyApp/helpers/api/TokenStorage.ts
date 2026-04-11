import * as SecureStore from "expo-secure-store";
import { jwtDecode } from "jwt-decode";

interface JwtPayload {
  exp: number; // seconds
}

const isTokenExpired = (token: string): boolean => {
  try {
    const decoded = jwtDecode<JwtPayload>(token);

    if (!decoded.exp) return true;

    const currentTime = Date.now(); // convert to seconds

    return decoded.exp * 1000 < currentTime;
  } catch (error) {
    console.error("Error decoding token:", error);
    return true; // token lỗi => coi như expired
  }
};

const TOKEN_KEY = "access_token";

export const saveToken = async (token: string) => {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
};

export const getToken = async () => {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);

  if (!token) return null;

  if (isTokenExpired(token)) {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    return null;
  }

  return token;
};

export const removeToken = async () => {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
};
