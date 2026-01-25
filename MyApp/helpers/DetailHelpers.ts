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

export const fetchNews = async (symbol: string): Promise<New[]> => {
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

    return data as New[];

    // if (errorCode === 0) {
    //   return data as New[];
    // }

    // return [];
  } catch (error) {
    console.error(error);
    return [];
  }
};
