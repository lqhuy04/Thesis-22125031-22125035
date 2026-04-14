import { sendMessage } from "./api/ApiClients";
import { New } from "./DetailHelpers";

export type MarketIndex = {
  IndexId: string;
  IndexValue: string;
  TradingDate: string;
  Time: string | null;
  Change: string;
  RatioChange: string;
  TotalTrade: string;
  TotalMatchVol: string;
  TotalMatchVal: string;
  TypeIndex: string | null;
  IndexName: string;
  Advances: string;
  NoChanges: string;
  Declines: string;
  Ceilings: string;
  Floors: string;
  TotalDealVol: string;
  TotalDealVal: string;
  TotalVol: string;
  TotalVal: string;
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
