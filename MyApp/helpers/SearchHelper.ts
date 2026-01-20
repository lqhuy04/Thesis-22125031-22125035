import { baseUrl } from "./base";

type SearchStockItemResponse = {
  symbol: string;
  name: string;
  market: string;
  current_price: number;
  price_change: number;
  price_change_percent: number;
};

export const searchStocks = async (
  query: string,
): Promise<SearchStockItemResponse[]> => {
  try {
    const response = await fetch(
      baseUrl + `market-data/search?query=${query}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      },
    );

    const result = await response.json();
    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return data as SearchStockItemResponse[];
    } else {
      return [];
    }
  } catch (error) {
    console.error(error);
    return [];
  }
};
