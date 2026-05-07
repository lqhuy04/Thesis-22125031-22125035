import { getSession } from "./TokenStorage";
import { baseUrl } from "./base";

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

  return response.json();
};
