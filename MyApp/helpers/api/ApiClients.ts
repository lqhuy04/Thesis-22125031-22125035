import { getSession, saveSession } from "./TokenStorage";
import { authEvents, AUTH_EXPIRED_EVENT } from "./authEvents";
import { getBaseUrl } from "./base";

// Mutex state
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onRefreshSuccess = (newToken: string) => {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
};

export const sendMessage = async (
  endpoint: string,
  options: RequestInit = {},
) => {
  const baseUrl = await getBaseUrl();
  const session = await getSession();
  const token = session?.token;
  const refresh_token = session?.refresh_token;

  const buildHeaders = (accessToken?: string) => ({
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    ...(options.headers || {}),
  });

  const response = await fetch(baseUrl + endpoint, {
    ...options,
    headers: buildHeaders(token),
  });

  if (response.status !== 401) {
    return response.json();
  }

  // --- 401: cần refresh token ---

  // Nếu đang có request khác đang refresh, chờ nó xong
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      subscribeTokenRefresh(async (newToken) => {
        try {
          const retryResponse = await fetch(baseUrl + endpoint, {
            ...options,
            headers: buildHeaders(newToken),
          });
          resolve(retryResponse.json());
        } catch (err) {
          reject(err);
        }
      });
    });
  }

  // Request đầu tiên bắt đầu refresh
  isRefreshing = true;

  try {
    const refreshResponse = await fetch(baseUrl + "api/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    });

    if (!refreshResponse.ok) {
      authEvents.emit(AUTH_EXPIRED_EVENT);
      throw new Error("Session expired. Please login again.");
    }

    const refreshData = await refreshResponse.json();
    const newToken = refreshData?.data.token;
    const newRefreshToken = refreshData?.data.refresh_token ?? refresh_token;

    if (!newToken || !newRefreshToken) {
      authEvents.emit(AUTH_EXPIRED_EVENT);
      throw new Error("Session expired. Please login again.");
    }

    await saveSession({ token: newToken, refresh_token: newRefreshToken });

    // Thông báo cho tất cả request đang chờ
    onRefreshSuccess(newToken);

    // Retry chính request này
    const retryResponse = await fetch(baseUrl + endpoint, {
      ...options,
      headers: buildHeaders(newToken),
    });

    return retryResponse.json();
  } finally {
    isRefreshing = false;
  }
};
