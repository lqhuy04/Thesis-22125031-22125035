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
  industry: string,
  limit?: number,
): Promise<{
  status: boolean;
  data: CurrentPriceData[];
}> => {
  try {
    const result = await sendMessage(
      limit
        ? `api/industry-movement?industry=${industry}&limit=${limit}`
        : `api/industry-movement?industry=${industry}`,
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
