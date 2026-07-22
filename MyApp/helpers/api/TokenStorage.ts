import * as SecureStore from "expo-secure-store";
import { jwtDecode } from "jwt-decode";
import { getBaseUrl } from "./base";

interface JwtPayload {
  exp: number;
  email?: string;
}

export interface Session {
  token: string;
  refresh_token: string;
}

const SESSION_KEYS = {
  TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
} as const;

export const isTokenExpired = (token: string): boolean => {
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

  return { token, refresh_token };
};

export const getSessionEmail = async (): Promise<string | null> => {
  try {
    const token = await SecureStore.getItemAsync(SESSION_KEYS.TOKEN);

    if (!token) return null;

    const { email } = jwtDecode<JwtPayload>(token);
    return email?.trim() || null;
  } catch (error) {
    console.error("Error decoding session email:", error);
    return null;
  }
};

export const removeSession = async () => {
  await Promise.all([
    SecureStore.deleteItemAsync(SESSION_KEYS.TOKEN),
    SecureStore.deleteItemAsync(SESSION_KEYS.REFRESH_TOKEN),
  ]);
};

export const refreshSession = async (): Promise<Session | null> => {
  const session = await getSession();
  const refresh_token = session?.refresh_token;

  if (!refresh_token) return null;

  try {
    const baseUrl = await getBaseUrl();
    const response = await fetch(`${baseUrl}api/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ refresh_token }),
    });

    if (!response.ok) {
      await removeSession();
      return null;
    }

    const result = await response.json();
    const { errorCode, data } = result || {};

    if (errorCode !== 0) {
      await removeSession();
      return null;
    }

    const newSession: Session = {
      token: data.token,
      refresh_token: data.refresh_token,
    };

    await saveSession(newSession);
    return newSession;
  } catch {
    await removeSession();
    return null;
  }
};
