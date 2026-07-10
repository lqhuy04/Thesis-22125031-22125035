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

export type IncomeStatement = {
  symbol: string;
  year: number;
  gross_revenue: number | null;
  net_revenue: number | null;
  cogs: number | null;
  gross_profit: number | null;
  financial_income: number | null;
  financial_expense: number | null;
  interest_expense: number | null;
  selling_expense: number | null;
  admin_expense: number | null;
  operating_profit: number | null;
  profit_before_tax: number | null;
  income_tax_expense: number | null;
  net_profit_after_tax: number | null;
  net_income_parent: number | null;
  eps_basic: number | null;
  ebit: number | null;
  ebitda: number | null;
};

export const getIncomeStatements = async (
  stockSymbol: string,
): Promise<{
  status: boolean;
  data: IncomeStatement[];
}> => {
  try {
    const result = await sendMessage(
      `api/fundamental-analysis/${stockSymbol}/income-statements`,
    );
    const { errorCode, data } = result || {};

    if (errorCode === 0 && data && Array.isArray(data) && data.length > 0) {
      // Sắp xếp tăng dần theo năm để vẽ biểu đồ từ trái sang phải
      const sorted = [...(data as IncomeStatement[])].sort(
        (a, b) => a.year - b.year,
      );
      return {
        status: true,
        data: sorted,
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
    const { summary } = data || {};

    if (errorCode === 0 && data) {
      return {
        status: true,
        data: summary as string,
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
