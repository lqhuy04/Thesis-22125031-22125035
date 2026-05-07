import * as SecureStore from "expo-secure-store";
import { jwtDecode } from "jwt-decode";

interface JwtPayload {
  exp: number;
}

export interface Session {
  token: string;
  email: string;
  user_id: string;
}

const SESSION_KEYS = {
  TOKEN: "access_token",
  EMAIL: "email",
  USER_ID: "user_id",
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

export const saveSession = async ({ token, email, user_id }: Session) => {
  await Promise.all([
    SecureStore.setItemAsync(SESSION_KEYS.TOKEN, token),
    SecureStore.setItemAsync(SESSION_KEYS.EMAIL, email),
    SecureStore.setItemAsync(SESSION_KEYS.USER_ID, user_id),
  ]);
};

export const getSession = async (): Promise<Session | null> => {
  const [token, email, user_id] = await Promise.all([
    SecureStore.getItemAsync(SESSION_KEYS.TOKEN),
    SecureStore.getItemAsync(SESSION_KEYS.EMAIL),
    SecureStore.getItemAsync(SESSION_KEYS.USER_ID),
  ]);

  if (!token || !email || !user_id) return null;

  if (isTokenExpired(token)) {
    await removeSession();
    return null;
  }

  return { token, email, user_id };
};

export const removeSession = async () => {
  await Promise.all([
    SecureStore.deleteItemAsync(SESSION_KEYS.TOKEN),
    SecureStore.deleteItemAsync(SESSION_KEYS.EMAIL),
    SecureStore.deleteItemAsync(SESSION_KEYS.USER_ID),
  ]);
};
