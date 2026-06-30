import { sendMessage } from "./api/ApiClients";
import { CurrentPriceData, New } from "./DetailHelpers";

export type MarketIndex = {
  IndexId: string;
  IndexValue: number;
  TradingDate: string;
  Time: string | null;
  Change: number;
  RatioChange: number;
  TotalTrade: number;
  TotalMatchVol: number;
  TotalMatchVal: number;
  TypeIndex: string | null;
  IndexName: string;
  Advances: number;
  NoChanges: number;
  Declines: number;
  Ceilings: number;
  Floors: number;
  TotalDealVol: number;
  TotalDealVal: number;
  TotalVol: number;
  TotalVal: number;
  TradingSession: string;
};

export const getMarketIndices = async (): Promise<{
  status: boolean;
  data: MarketIndex[];
}> => {
  try {
    const result = await sendMessage("api/market-index");
    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
        data: Array.isArray(data) ? (data as MarketIndex[]) : [],
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

export const getMacroEcomNews = async (
  limit?: number,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const result = await sendMessage(
      limit ? `api/articles/macro?limit=${limit}` : `api/articles/macro`,
    );

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

export const getAllNews = async (
  limit?: number,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const result = await sendMessage(
      limit ? `api/articles?limit=${limit}` : `api/articles`,
    );

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

export const getNewsByCategoryId = async (
  category_id: string,
  limit?: number,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const result = await sendMessage(
      limit
        ? `api/articles/category/${category_id}?limit=${limit}`
        : `api/articles/category/${category_id}`,
    );

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

export const getBusinessNews = async (
  limit?: number,
): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const result = await sendMessage(
      limit ? `api/articles/business?limit=${limit}` : `api/articles/business`,
    );

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

export const getIndustryMovement = async (
  industryId: string,
  limit?: number,
): Promise<{
  status: boolean;
  data: CurrentPriceData[];
}> => {
  try {
    const result = await sendMessage(
      limit
        ? `api/industry-movement?industry_id=${industryId}&limit=${limit}`
        : `api/industry-movement?industry_id=${industryId}`,
    );

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as CurrentPriceData[],
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

export const getAllStocks = async (
  page: number = 1,
  pageSize: number = 20,
): Promise<{
  status: boolean;
  data: CurrentPriceData[];
  page: number;
  totalPages: number;
}> => {
  try {
    const result = await sendMessage(
      `api/all-stocks?page=${page}&page_size=${pageSize}`,
    );

    const { errorCode, data, page: resPage, totalPages } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as CurrentPriceData[],
        page: resPage ?? page,
        totalPages: totalPages ?? 0,
      };
    }

    return {
      status: false,
      data: [],
      page,
      totalPages: 0,
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
      page,
      totalPages: 0,
    };
  }
};

export type TodayHighlight = CurrentPriceData & {
  news: New[];
};

export const getTodayHighlights = async (): Promise<{
  status: boolean;
  data: TodayHighlight[];
}> => {
  try {
    const result = await sendMessage(`api/articles/today-highlight`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as TodayHighlight[],
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

export type SuggestionItem = {
  logo: string;
  symbol: string;
  company_name: string;
  current_price: number;
  price_change: number;
  per_price_change: number;
};

export type SuggestionMsgType =
  | "top_gainers"
  | "top_decliners"
  | "top_volume"
  | "cheap_under_50k"
  | "top_searched"
  | "top_watchlist";

// Time window for trend categories (top_gainers / top_decliners / top_volume).
export type SuggestionInterval = "today" | "1w" | "1mo" | "3mo" | "6mo";

export const getInvestingIdea = async (
  msgType: SuggestionMsgType,
  limit?: number,
  interval?: SuggestionInterval,
): Promise<{
  status: boolean;
  data: SuggestionItem[];
}> => {
  try {
    const result = await sendMessage(
      `api/investing-idea?msgType=${msgType}&limit=${limit != null ? limit : 5}` +
        (interval ? `&interval=${interval}` : ""),
    );

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: (data as SuggestionItem[]) ?? [],
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
