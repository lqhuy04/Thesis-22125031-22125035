import { baseUrl } from "./base";

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
    const response = await fetch(baseUrl + `api/company/${symbol}/profile`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();
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
