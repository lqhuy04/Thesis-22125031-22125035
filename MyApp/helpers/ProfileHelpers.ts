import { sendMessage } from "./api/ApiClients";

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
