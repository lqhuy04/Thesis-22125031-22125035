import { getSession } from "./TokenStorage";
import { baseUrl } from "./base";
import { authEvents, AUTH_EXPIRED_EVENT } from "./authEvents";

export const sendMessage = async (
  endpoint: string,
  options: RequestInit = {},
) => {
  const session = await getSession();
  const token = session?.token;

  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(options.headers || {}),
  };

  const response = await fetch(baseUrl + endpoint, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    authEvents.emit(AUTH_EXPIRED_EVENT); // 🔥 bắn event
    throw new Error("Unauthorized");
  }

  return response.json();
};
