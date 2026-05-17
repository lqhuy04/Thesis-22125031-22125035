import { sendMessage } from "./api/ApiClients";
import * as SecureStore from "expo-secure-store";

export type SearchStockItem = {
  stock_id: string;
  symbol: string;
  company_name: string;
  logo: string;
  exchange: string;
  current_price: number;
  price_change: number;
  per_price_change: number;
};

export const searchStocks = async (
  query: string,
): Promise<SearchStockItem[]> => {
  try {
    const result = await sendMessage(`api/search/${query}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return data as SearchStockItem[];
    } else {
      return [];
    }
  } catch (error) {
    console.error(error);
    return [];
  }
};

const HISTORY_KEY = "search_history";

export const getSearchHistory = async (): Promise<SearchStockItem[]> => {
  const raw = await SecureStore.getItemAsync(HISTORY_KEY);
  return raw ? JSON.parse(raw) : [];
};

export const addToSearchHistory = async (item: SearchStockItem) => {
  const history = await getSearchHistory();

  // Nếu trùng mã thì không lưu
  const isDuplicate = history.some((h) => h.symbol === item.symbol);
  if (isDuplicate) return;

  // Nếu đã đủ 5 thì bỏ mã cũ nhất (cuối mảng)
  const trimmed = history.length >= 5 ? history.slice(0, 4) : history;

  const updated = [item, ...trimmed];
  await SecureStore.setItemAsync(HISTORY_KEY, JSON.stringify(updated));
};

export const removeFromSearchHistory = async (symbol: string) => {
  const history = await getSearchHistory();
  const updated = history.filter((h) => h.symbol !== symbol);
  await SecureStore.setItemAsync(HISTORY_KEY, JSON.stringify(updated));
};

export const clearSearchHistory = async () => {
  await SecureStore.deleteItemAsync(HISTORY_KEY);
};
