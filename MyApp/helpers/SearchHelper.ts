import { sendMessage } from "./api/ApiClients";

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

// Search History
export const saveSearchHistory = async (
  symbol: string,
): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/search-history", {
      method: "POST",
      body: JSON.stringify({ symbol }),
    });

    const { errorCode } = result || {};
    return { status: errorCode === 0 };
  } catch (error) {
    console.error(error);
    return { status: false };
  }
};

export type SearchHistoryItem = {
  symbol: string;
  current_price: number;
  per_price_change: number;
};

export const getSearchHistory = async (): Promise<SearchHistoryItem[]> => {
  try {
    const result = await sendMessage("api/search-history");

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return data as SearchHistoryItem[];
    } else {
      return [];
    }
  } catch (error) {
    console.error(error);
    return [];
  }
};
