import { sendMessage } from "./api/ApiClients";

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
};

export const fetchNews = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const result = await sendMessage(`api/news/${symbol}`);

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
  Symbol: string;
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
  timeframe: "15m" | "1h" | "1d",
): Promise<{
  status: boolean;
  data: StockPriceData[];
}> => {
  try {
    const result = await sendMessage(
      `api/stock-price-v2/${symbol}?interval=${timeframe}`,
    );

    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
        data: data?.data as StockPriceData[],
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

// export type StockData = {
//   Symbol: string;
//   TradingDate: string;
//   Time: string;
//   Open: string;
//   High: string;
//   Low: string;
//   Close: string;
//   Volume: string;
// };

// export const fetchStockData = async (
//   symbol: string,
//   timeframe: "1D" | "1W" | "1M" | "1Y" | "5Y",
// ): Promise<{
//   status: boolean;
//   data: StockData[];
// }> => {
//   try {
//     const result = await sendMessage(
//       `api/stock-price/${symbol}?timeframe=${timeframe}`,
//     );

//     const { errorCode, data } = result || {};
//     if (errorCode === 0) {
//       return {
//         status: true,
//         data: data?.data as StockData[],
//       };
//     }

//     return {
//       status: false,
//       data: [],
//     };
//   } catch (error) {
//     console.error(error);
//     return {
//       status: false,
//       data: [],
//     };
//   }
// };

//------------------------------------------------------------
export type AnalysisData = {
  symbol: string;
  fundamental_analysis: string;
  technical_analysis: string;
  news_analysis: string;
  recommendation: string;
};

export const getAnalysis = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: AnalysisData | null;
}> => {
  try {
    const result = await sendMessage(`api/analysis/${symbol}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as AnalysisData,
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
export type CurrentPriceData = {
  symbol: string;
  current_price: number;
  price_change: number;
  price_change_percent: number;
  reference_price: number;
  ceiling_price: number;
  floor_price: number;
};

export const fetchCurrentPriceData = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: CurrentPriceData | null;
}> => {
  try {
    const result = await sendMessage(`api/price/${symbol}`);

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
export type TechnicalIndicators = {
  sma_20: number;
  sma_50: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  volume: number;
  macd: number;
  DIF: number;
  DEA: number;
  rsi_14: number;
  stoch_k: number;
  stoch_d: number;
  stoch_j: number;
};

export type TechnicalIndicatorData = {
  date: string;
  time: string;
  indicators: TechnicalIndicators;
};

export const getTechnicalIndicators = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: TechnicalIndicatorData[];
}> => {
  try {
    const result = await sendMessage(`api/technical-indicators/${symbol}`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data?.series as TechnicalIndicatorData[],
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
