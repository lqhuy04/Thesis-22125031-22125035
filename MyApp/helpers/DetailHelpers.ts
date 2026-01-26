import { baseUrl } from "./base";

export type Content = {
  type: "text" | "image";
  url?: string;
  text?: string;
};

export type New = {
  id: string;
  title: string;
  link: string;
  stock_symbol: string;
  description: string;
  time: string;
  image_url: string;
  published_at: string;
  content: {
    blocks: Content[];
  };
  source: string;
};

export const fetchNews = async (symbol: string): Promise<{
  status: boolean;
  data: New[];
}> => {
  try {
    const response = await fetch(baseUrl + `news?stock_symbol=${symbol}`, {
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
        data: data?.items as New[],
      };
    }

    return {
      status: false,
      data: [],
    }
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: [],
    };
  }
};

//------------------------------------------------------------
export type FundamentalAnalysisIndexes = {
  pe_ratio: number; // P/E
  pb_ratio: number; // P/B
  eps: number; // EPS
  market_cap_billion: number; // Vốn hóa (tỷ đồng)
  shares_outstanding_million: number; // Khối lượng lưu hành (triệu cổ phiếu)
  roe: number; // ROE
  gross_margin: number; // Biên lợi nhuận gộp
  revenue_yoy: number; // Doanh thu YoY
  eps_yoy: number; // EPS YoY
  debt_to_equity: number; // Nợ/VCSH
  current_ratio: number; // Hệ số thanh toán hiện hành
  fcf: number; // FCF
  ev_ebitda: number; // EV/EBITDA
}

export const fetchFundamentalAnalysisIndexes = async (symbol: string): Promise<{
    status: boolean,
    data: FundamentalAnalysisIndexes | null,
} > => {
  try {
    const response = await fetch(baseUrl + `api/financial/analysis/${symbol}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();
    return {
      status: true,
      data: result?.metrics
    };
  } catch (error) {
    console.error(error);
    return {
      status: false,
      data: null
    };
  }
};
