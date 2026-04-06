import { sendMessage } from "./api/ApiClients";

export type SearchStockItem = {
  stock_id: string;
  symbol: string;
  company_name: string;
  exchange: string;
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
