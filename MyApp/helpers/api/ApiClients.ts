import { getToken } from "./TokenStorage";
import { baseUrl } from "./base";

export const sendMessage = async (
  endpoint: string,
  options: RequestInit = {},
) => {
  const token = await getToken();

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

  return response.json();
};
