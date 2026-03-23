import { sendMessage } from "./api/ApiClients";

export type FinancialIndicators = {
  symbol: string;
  year: number;
  cash_cycle_days: number;
  net_income: number;
  profit_yoy: number;
  revenue: number;
  revenue_yoy: number;
  market_cap: number;
  eps: number;
  pe_ratio: number;
  pb_ratio: number;
  ps_ratio: number;
  p_cash_flow: number;
  shares_outstanding: number;
  ev_ebitda: number;
  bvps: number;
  cash_ratio: number;
  debt_to_equity: number;
  roe: number;
  roa: number;
  days_receivable: number;
  days_inventory: number;
  quick_ratio: number;
  days_payable: number;
  gross_margin: number;
  ebit_margin: number;
  net_margin: number;
  current_ratio: number;
  asset_turnover: number;
  loans_to_equity: number;
  financial_leverage: number;
  roic: number;
  interest_coverage: number;
  fixed_asset_turnover: number;
};

export const getFinancialIndicators = async (
  stockSymbol: string,
): Promise<{
  status: boolean;
  data: FinancialIndicators | null;
  annualData: FinancialIndicators[];
}> => {
  try {
    const result = await sendMessage(
      `api/fundamental-analysis/${stockSymbol}/financial-indicators`,
    );
    const { errorCode, data } = result || {};

    if (errorCode === 0 && data && Array.isArray(data) && data.length > 0) {
      return {
        status: true,
        data: data[0] as FinancialIndicators,
        annualData: data.slice(0, 5).reverse() as FinancialIndicators[],
      };
    } else {
      return {
        status: false,
        data: null,
        annualData: [],
      };
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null,
      annualData: [],
    };
  }
};

export type CashFlows = {
  symbol: string;
  year: number;
  cfo: number;
  profit_before_wc_changes: number;
  profit_before_tax_cf: number;
  depreciation: number;
  cfi: number;
  capex: number;
  dividends_received: number;
  cff: number;
  proceeds_from_share_issuance: number;
  proceeds_from_loans: number;
  repayment_of_loans: number;
  dividends_paid: number;
  net_cash_change: number;
  cash_beginning: number;
  cash_ending: number;
};

export const getCashFlows = async (
  stockSymbol: string,
): Promise<{
  status: boolean;
  data: CashFlows | null;
}> => {
  try {
    const result = await sendMessage(
      `api/fundamental-analysis/${stockSymbol}/cash-flows`,
    );
    const { errorCode, data } = result || {};

    if (errorCode === 0 && data && Array.isArray(data) && data.length > 0) {
      return {
        status: true,
        data: data[0] as CashFlows,
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

export const getFinancialAnalysisSummary = async (
  stockSymbol: string,
): Promise<{
  status: boolean;
  data: string | null;
}> => {
  try {
    const result = await sendMessage(
      `api/fundamental-analysis/${stockSymbol}/summary`,
    );
    const { errorCode, data } = result || {};

    if (errorCode === 0 && data) {
      return {
        status: true,
        data: data as string,
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
