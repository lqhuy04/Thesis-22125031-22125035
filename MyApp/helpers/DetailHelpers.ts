import { sendMessage } from "./api/ApiClients";
import { MarketIndex } from "./MarketHelpers";

function parseTradingTime(tradingTime: string): { date: string; time: string } {
  const date = new Date(tradingTime); // +07:00 đã được JS tự xử lý → convert sang UTC

  // Cộng thêm 7h để convert UTC → UTC+7
  const vnDate = new Date(date.getTime() + 7 * 60 * 60 * 1000);

  const day = String(vnDate.getUTCDate()).padStart(2, "0");
  const month = String(vnDate.getUTCMonth() + 1).padStart(2, "0");
  const year = vnDate.getUTCFullYear();
  const hours = String(vnDate.getUTCHours()).padStart(2, "0");
  const minutes = String(vnDate.getUTCMinutes()).padStart(2, "0");
  const seconds = String(vnDate.getUTCSeconds()).padStart(2, "0");

  return {
    date: `${day}/${month}/${year}`, // "22/04/2026"
    time: `${hours}:${minutes}:${seconds}`, // "13:15:00"
  };
}

export function parseDateTime(dateString: string, timeString: string): number {
  // ---- Parse date ----
  const dateParts = dateString.split("/");

  if (dateParts.length !== 3) {
    throw new Error("Invalid date format. Expected dd/mm/yyyy");
  }

  const day = parseInt(dateParts[0], 10);
  const month = parseInt(dateParts[1], 10) - 1;
  const year = parseInt(dateParts[2], 10);

  // ---- Parse time ----
  const timeParts = timeString.split(":");

  if (timeParts.length !== 3) {
    throw new Error("Invalid time format. Expected hh:mm:ss");
  }

  const hours = parseInt(timeParts[0], 10);
  const minutes = parseInt(timeParts[1], 10);
  const seconds = parseInt(timeParts[2], 10);

  const date = new Date(year, month, day, hours, minutes, seconds);

  // ---- Validate date ----
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month ||
    date.getDate() !== day
  ) {
    throw new Error("Invalid date");
  }

  // ---- Validate time ----
  if (
    hours < 0 ||
    hours > 23 ||
    minutes < 0 ||
    minutes > 59 ||
    seconds < 0 ||
    seconds > 59
  ) {
    throw new Error("Invalid time");
  }

  return date.getTime(); // ✅ return timestamp
}

export type Content = {
  type: "text" | "image";
  url?: string;
  content?: string;
};

export type New = {
  id: string;
  title: string;
  link: string;
  stock_symbol: string;
  description: string;
  time: string;
  thumbnail: string;
  published_at: string;
  content: string;
  source: string;
  sentiment?: string;
};

export const fetchNews = async (
  symbol: string,
  limit?: number,
  offset: number = 0,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const paginationParams = [
      ...(limit !== undefined ? [`limit=${limit}`] : []),
      ...(offset > 0 ? [`offset=${offset}`] : []),
    ];
    const query =
      paginationParams.length > 0 ? `?${paginationParams.join("&")}` : "";
    const result = await sendMessage(`api/articles/stock/${symbol}${query}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as New[],
      };
    }

    return {
      status: false,
      data: [],
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
    };
  }
};

//------------------------------------------------------------
export type StockPriceData = {
  symbol: string;
  TradingDate: string;
  Time: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
};

export const fetchStockDataByTimeFrame = async (
  symbol: string,
  timeframe: "1m" | "5m" | "15m" | "30m" | "1h" | "1d" | "1w" | "1M",
): Promise<{
  status: boolean;
  data: StockPriceData[];
}> => {
  try {
    const result = await sendMessage(
      `api/price/${symbol}?interval=${timeframe}`,
    );

    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      const result = data?.map((item: any) => {
        const { date, time } = parseTradingTime(item?.trading_time);
        return {
          symbol: item?.symbol,
          TradingDate: date,
          Time: time,
          Open: item?.open,
          High: item?.high,
          Low: item?.low,
          Close: item?.close,
          Volume: item?.volume,
        };
      });

      return {
        status: true,
        data: result,
      };
    } else {
      return {
        status: false,
        data: [],
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
    };
  }
};

//------------------------------------------------------------
export type MarketIndexValueData = {
  index_id: string;
  trading_time: string;
  value: number;
};

export const fetchIndexValueDataByTimeFrame = async (
  indexId: string,
  timeframe: "1m" | "5m" | "15m" | "30m" | "1h" | "1d" | "1w" | "1M",
): Promise<{
  status: boolean;
  data: MarketIndexValueData[];
}> => {
  try {
    const result = await sendMessage(
      `api/market-index-price/${indexId}?interval=${timeframe}`,
    );

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: (data ?? []) as MarketIndexValueData[],
      };
    }

    return {
      status: false,
      data: [],
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
    };
  }
};

//------------------------------------------------------------
export type CurrentPriceData = {
  stock_id: string;
  symbol: string;
  logo: string;
  company_name: string;
  exchange: string;
  PriceChange: number;
  PerPriceChange: number;
  CeilingPrice: number;
  FloorPrice: number;
  RefPrice: number;
  CurrentPrice: number;
  TotalMatchVol: number;
  TotalMatchVal: number;
};

export const fetchCurrentPriceData = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: CurrentPriceData | null;
}> => {
  try {
    const result = await sendMessage(`api/current-price/${symbol}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as CurrentPriceData,
      };
    }

    return {
      status: false,
      data: null,
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
    };
  }
};

//------------------------------------------------------------
export type RelatedStockItem = {
  symbol: string;
  current_price: number;
  per_price_change: number;
};

export const fetchRelatedStocks = async (
  symbol: string,
): Promise<RelatedStockItem[]> => {
  try {
    const result = await sendMessage(`api/related-stocks/${symbol}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return data as RelatedStockItem[];
    }

    return [];
  } catch (error) {
    console.error(error);
    return [];
  }
};

export const fetchRandomMarketIndexStocks = async (
  indexId: string,
  limit: number = 6,
): Promise<RelatedStockItem[]> => {
  try {
    const result = await sendMessage(
      `api/market-index/${indexId}/random-stocks?limit=${limit}`,
    );

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return data as RelatedStockItem[];
    }

    return [];
  } catch (error) {
    console.error(error);
    return [];
  }
};

//------------------------------------------------------------

export const fetchCurrentIndexData = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: MarketIndex | null;
}> => {
  try {
    const result = await sendMessage(`api/market-index/${symbol}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as MarketIndex,
      };
    }

    return {
      status: false,
      data: null,
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
    };
  }
};

//------------------------------------------------------------
export type TechnicalIndicatorData = {
  TradingDate: string;
  Time: string;
  sma_20: number;
  sma_50: number;
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  kdj_k: number;
  kdj_d: number;
  kdj_j: number;
  volume_ma_20: number;
  volume_ma_50: number;
};

export const getTechnicalIndicators = async (
  symbol: string,
  timeframe: "1m" | "5m" | "15m" | "30m" | "1h" | "1d" | "1w" | "1M",
): Promise<{
  status: boolean;
  data: TechnicalIndicatorData[];
}> => {
  try {
    const result = await sendMessage(
      `api/technical-indicators/${symbol}?interval=${timeframe}`,
    );

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as TechnicalIndicatorData[],
      };
    }

    return {
      status: false,
      data: [],
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
    };
  }
};
