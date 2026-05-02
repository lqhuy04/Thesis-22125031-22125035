import { sendMessage } from "./api/ApiClients";
import { MarketIndex } from "./MarketHelpers";

function parseTradingTime(tradingTime: string): { date: string; time: string } {
  const date = new Date(tradingTime);

  const day = String(date.getUTCDate()).padStart(2, "0");
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const year = date.getUTCFullYear();

  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  const seconds = String(date.getUTCSeconds()).padStart(2, "0");

  return {
    date: `${day}/${month}/${year}`, // "30/03/2026"
    time: `${hours}:${minutes}:${seconds}`, // "10:30:00"
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
  image_url: string;
  published_at: string;
  content: string;
  source: string;
  sentiment?: string;
};

export const fetchNews = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const result = await sendMessage(`api/articles/stock/${symbol}?limit=10`);

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
export type FundamentalAnalysisIndexes = {
  pe_ratio: number; // P/E
  pb_ratio: number; // P/B
  eps: number; // EPS
  market_cap_billion: number; // Vốn hóa (tỷ đồng)
  shares_outstanding_million: number; // Khối lượng lưu hành (triệu cổ phiếu)
  roe: number; // ROE
  gross_margin: number; // Biên lợi nhuận gộp
  revenue_yoy: number; // Doanh thu YoY
  eps_yoy: number; // EPS YoY
  debt_to_equity: number; // Nợ/VCSH
  current_ratio: number; // Hệ số thanh toán hiện hành
  fcf: number; // FCF
  ev_ebitda: number; // EV/EBITDA
};

export const fetchFundamentalAnalysisIndexes = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: FundamentalAnalysisIndexes | null;
}> => {
  try {
    const result = await sendMessage(`api/fundamental-metrics/${symbol}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data?.metrics as FundamentalAnalysisIndexes,
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
export type CurrentPriceData = {
  stock_id: string;
  symbol: string;
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
