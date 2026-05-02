import { sendMessage } from "./api/ApiClients";
import { CurrentPriceData } from "./DetailHelpers";

export const saveRiskAppetite = async ({
  experience,
  expectation,
  period,
  comfort_zone,
  capital_ratio,
}: {
  experience: string;
  expectation: string;
  period: string;
  comfort_zone: string;
  capital_ratio: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/risk-appetite/", {
      method: "POST",
      body: JSON.stringify({
        experience,
        expectation,
        period,
        comfort_zone,
        capital_ratio,
      }),
    });

    const { errorCode } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

export type RiskAppetite = {
  experience: string;
  expectation: string;
  period: string;
  comfort_zone: string;
  capital_ratio: string;
};

export const getRiskAppetite = async (): Promise<{
  status: boolean;
  data: RiskAppetite | null;
}> => {
  try {
    const result = await sendMessage("api/risk-appetite/");
    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
        data: data as RiskAppetite,
      };
    } else {
      return {
        status: false,
        data: null,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
    };
  }
};

// ---------------------------------------------------------------------
export type HistoryItem = {
  id: string;
  amount: number;
  buy_price: number;
  time: string;
};

export type WatchItem = CurrentPriceData & {
  id: string;
  history: HistoryItem[];
};

export const getWatchlist = async (): Promise<{
  status: boolean;
  data: WatchItem[];
}> => {
  try {
    const result = await sendMessage("api/portfolio");
    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
        data: data as WatchItem[],
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

export const addStockToWatchList = async ({
  symbol,
  amount,
  buy_price,
  time,
}: {
  symbol: string;
  amount: number;
  buy_price: number;
  time: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/portfolio", {
      method: "POST",
      body: JSON.stringify({
        symbol,
        amount,
        buy_price,
        time,
      }),
    });

    const { errorCode } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

export const removeWatchListRecords = async ({
  portfolio_ids,
}: {
  portfolio_ids: string[];
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/portfolio", {
      method: "DELETE",
      body: JSON.stringify({
        portfolio_ids,
      }),
    });

    const { errorCode } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};

export const updateWatchListRecord = async ({
  portfolio_id,
  amount,
  buy_price,
  time,
}: {
  portfolio_id: string;
  amount?: number;
  buy_price?: number;
  time?: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage(`api/portfolio/${portfolio_id}`, {
      method: "PUT",
      body: JSON.stringify({
        amount,
        buy_price,
        time,
      }),
    });

    const { errorCode } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
      };
    } else {
      return {
        status: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
    };
  }
};
