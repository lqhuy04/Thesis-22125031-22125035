import * as SecureStore from "expo-secure-store";
import { jwtDecode } from "jwt-decode";

interface JwtPayload {
  exp: number;
}

export interface Session {
  token: string;
  refresh_token: string;
}

const SESSION_KEYS = {
  TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
} as const;

const isTokenExpired = (token: string): boolean => {
  try {
    const decoded = jwtDecode<JwtPayload>(token);

    if (!decoded.exp) return true;

    const currentTime = Date.now();

    return decoded.exp * 1000 < currentTime;
  } catch (error) {
    console.error("Error decoding token:", error);
    return true;
  }
};

export const saveSession = async ({ token, refresh_token }: Session) => {
  await Promise.all([
    SecureStore.setItemAsync(SESSION_KEYS.TOKEN, token),
    SecureStore.setItemAsync(SESSION_KEYS.REFRESH_TOKEN, refresh_token),
  ]);
};

export const getSession = async (): Promise<Session | null> => {
  const [token, refresh_token] = await Promise.all([
    SecureStore.getItemAsync(SESSION_KEYS.TOKEN),
    SecureStore.getItemAsync(SESSION_KEYS.REFRESH_TOKEN),
  ]);

  if (!token || !refresh_token) return null;

  if (isTokenExpired(token)) {
    await removeSession();
    return null;
  }

  return { token, refresh_token };
};

export const removeSession = async () => {
  await Promise.all([
    SecureStore.deleteItemAsync(SESSION_KEYS.TOKEN),
    SecureStore.deleteItemAsync(SESSION_KEYS.REFRESH_TOKEN),
  ]);
};
