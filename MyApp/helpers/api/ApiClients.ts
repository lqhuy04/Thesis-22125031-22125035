import { getSession, refreshSession, Session } from "./TokenStorage";
import { getBaseUrl } from "./base";
import { authEvents, AUTH_EXPIRED_EVENT } from "./authEvents";

// Mutex để tránh refresh bị gọi nhiều lần song song
let refreshPromise: Promise<Session | null> | null = null;

export const sendMessage = async <T = any>(
  endpoint: string,
  options: RequestInit = {},
  _isRetry = false, // tránh vòng lặp vô tận
): Promise<T> => {
  const session = await getSession();
  const token = session?.token;

  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(options.headers || {}),
  };

  const baseUrl = await getBaseUrl();

  const response = await fetch(baseUrl + endpoint, { ...options, headers });

  if (response.status === 401) {
    if (_isRetry) {
      authEvents.emit(AUTH_EXPIRED_EVENT);
      throw new Error("Unauthorized");
    }

    if (!refreshPromise) {
      refreshPromise = refreshSession().finally(() => {
        refreshPromise = null;
      });
    }

    const newSession = await refreshPromise;

    if (!newSession) {
      authEvents.emit(AUTH_EXPIRED_EVENT);
      throw new Error("Unauthorized");
    }

    return sendMessage<T>(endpoint, options, true); // ← pass T vào recursive call
  }

  return response.json() as Promise<T>;
};
