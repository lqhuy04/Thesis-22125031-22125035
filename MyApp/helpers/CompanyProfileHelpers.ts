import { sendMessage } from "./api/ApiClients";

export type CompanyProfile = {
  symbol: string | null;
  company_name: string | null;
  description: string | null;
  address: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  fax: string | null;
  sic_code: string | null;
  industry_name: string | null;
  icb_code: number | null;
  founded_date: string | null;
  charter_capital_billion: number | null;
  employee_count: number | null;
  branch_count: number | null;
  listing_date: string | null;
  exchange: string | null;
  ipo_price: number | null;
  listed_volume: number | null;
  market_cap_billion: number | null;
  shares_outstanding: number | null;
  data_source: string | null;
  crawled_at: string | null;
  updated_at: string | null;
};

export const getCompanyProfile = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: CompanyProfile | null;
}> => {
  try {
    const result = await sendMessage(`api/company/${symbol}/profile`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as CompanyProfile,
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

export type SubsidiaryCompany = {
  symbol: string | null;
  company_name: string | null;
  sub_symbol: string | null;
  charter_capital_billion: number | null;
  ownership_pct: number | null;
  relationship_type: string | null;
};

export const getCompanySubsidiaries = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: {
    subsidiaries: SubsidiaryCompany[];
    associates: SubsidiaryCompany[];
  };
}> => {
  try {
    const result = await sendMessage(`api/company/${symbol}/subsidiaries`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: {
          subsidiaries:
            data?.filter(
              (d: any) =>
                d.company_name != null && d.relationship_type === "subsidiary",
            ) || [],
          associates:
            data?.filter(
              (d: any) =>
                d.company_name != null && d.relationship_type === "associate",
            ) || [],
        },
      };
    }
    return {
      status: false,
      data: {
        subsidiaries: [],
        associates: [],
      },
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: {
        subsidiaries: [],
        associates: [],
      },
    };
  }
};

export type CompanyLeader = {
  full_name: string | null;
  position: string | null;
};

export const getCompanyLeaders = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: CompanyLeader[];
}> => {
  try {
    const result = await sendMessage(`api/company/${symbol}/leaders`);

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as CompanyLeader[],
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
