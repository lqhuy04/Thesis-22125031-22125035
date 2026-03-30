import { sendMessage } from "./api/ApiClients";

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
    const result = await sendMessage("api/index");
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
