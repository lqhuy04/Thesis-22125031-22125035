import { sendMessage } from "./api/ApiClients";

export type SearchStockItem = {
  symbol: string;
  name: string;
  market: string;
  current_price: number | null;
  price_change: number | null;
  price_change_percent: number | null;
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
