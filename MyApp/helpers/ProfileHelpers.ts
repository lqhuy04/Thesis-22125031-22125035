import { sendMessage } from "./api/ApiClients";
import { CurrentPriceData } from "./DetailHelpers";

export const saveRiskAppetite = async ({
  period,
}: {
  period: string;
}): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/risk-appetite/", {
      method: "POST",
      body: JSON.stringify({ period }),
    });

    const { errorCode } = result || {};

    if (errorCode === 0) {
      return { status: true };
    } else {
      return { status: false };
    }
  } catch (error) {
    console.error(error);
    return { status: false };
  }
};

export type RiskAppetite = {
  period: string;
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

// ----------------------------------------------
export type FavoriteItem = CurrentPriceData & {
  id: string;
};

export const getFavoritelist = async (): Promise<{
  status: boolean;
  data: FavoriteItem[];
}> => {
  try {
    const result = await sendMessage("api/favorite");
    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
        data: data as FavoriteItem[],
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

export const checkStockInFavorite = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: boolean;
}> => {
  try {
    const result = await sendMessage("api/favorite/check", {
      method: "POST",
      body: JSON.stringify({
        symbol,
      }),
    });

    const { errorCode, data } = result || {};

    if (errorCode === 0) {
      return {
        status: true,
        data: data?.is_favorited,
      };
    } else {
      return {
        status: false,
        data: false,
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: false,
    };
  }
};

export const addStockToFavorite = async (
  symbol: string,
): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/favorite", {
      method: "POST",
      body: JSON.stringify({
        symbol,
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

export const deleteStockFromFavorite = async (
  symbol: string,
): Promise<{
  status: boolean;
}> => {
  try {
    const result = await sendMessage("api/favorite", {
      method: "DELETE",
      body: JSON.stringify({
        symbol,
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
