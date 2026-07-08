import { sendMessage } from "./api/ApiClients";
import { getRiskAppetite } from "./ProfileHelpers";

export type AnalysisDetail = {
  technical: string;
  fundamental: string;
  news: string;
  summary: string;
};

export type AnalysisScore = {
  news: number;
  technical: number;
  fundamental: number;
};

export type AnalysisData = {
  recommendation: string;
  entry_price: number | null;
  take_profit_price: number | null;
  stop_loss_price: number | null;
  max_hold_candles: number | null;
  confidence: number;
  confidence_threshold: number;
  analysis: AnalysisDetail;
  score: AnalysisScore;
};

export type TechnicalSelection = {
  ma?: boolean;
  boll?: boolean;
  rsi?: boolean;
  macd?: boolean;
  kdj?: boolean;
};

export type FundamentalSelection = {
  liquidity?: boolean;
  leverage?: boolean;
  efficiency?: boolean;
  profitability?: boolean;
  valuation?: boolean;
};

export type WeightSelection = {
  news: number;
  technical: number;
  fundamental: number;
};

export type DataSelection = {
  news?: boolean;
  technical?: TechnicalSelection | boolean;
  fundamental?: FundamentalSelection | boolean;
  weight?: WeightSelection;
};

export type AnalysisMode = "auto" | "manual";

export const getAnalysis = async (
  symbol: string,
  mode: AnalysisMode = "auto",
  dataSelection?: DataSelection,
): Promise<{
  status: boolean;
  data: AnalysisData | null;
}> => {
  try {
    const riskAppetite = await getRiskAppetite();

    const body: Record<string, unknown> = {
      mode,
      symbol,
      risk_appetite: riskAppetite?.data,
    };

    if (mode === "manual" && dataSelection !== undefined) {
      body.data_selection = dataSelection;
    }

    const result = await sendMessage("api/agentic/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as AnalysisData,
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

//------------------------------------------------------------
export type ChatResponse = {
  session_id: string;
  reply: string;
};

export const sendChatMessage = async (
  sessionId: string,
  message: string,
): Promise<{
  status: boolean;
  data: ChatResponse | null;
}> => {
  try {
    const result = await sendMessage("api/agentic/chat", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
      }),
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: data as ChatResponse,
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

/**
 * Nạp sẵn 1 lượt Q&A (câu hỏi + kết quả phân tích đã hiển thị) vào memory của
 * một session chat mới, để người dùng hỏi tiếp mà vẫn giữ ngữ cảnh phân tích.
 * Không chạy lại pipeline — backend chỉ ghi cặp message vào checkpoint.
 */
export const seedChatSession = async (
  sessionId: string,
  userMessage: string,
  assistantMessage: string,
): Promise<{ status: boolean }> => {
  try {
    const result = await sendMessage("api/agentic/chat/seed", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        user_message: userMessage,
        assistant_message: assistantMessage,
      }),
    });
    return { status: (result?.errorCode ?? -1) === 0 };
  } catch (error) {
    console.error(error);
    return { status: false };
  }
};

//------------------------------------------------------------
export type ChatSession = {
  session_id: string;
  title: string;
  updated_at: string;
};

export type ChatHistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

/** Danh sách các cuộc trò chuyện của user đang đăng nhập (mới nhất trước). */
export const getChatSessions = async (): Promise<{
  status: boolean;
  data: ChatSession[];
}> => {
  try {
    const result = await sendMessage("api/agentic/chat/sessions", {
      method: "GET",
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return { status: true, data: (data as ChatSession[]) ?? [] };
    }
    return { status: false, data: [] };
  } catch (error) {
    console.error(error);
    return { status: false, data: [] };
  }
};

/** Lịch sử tin nhắn của một cuộc trò chuyện. */
export const getChatHistory = async (
  sessionId: string,
): Promise<{
  status: boolean;
  data: ChatHistoryMessage[];
}> => {
  try {
    const result = await sendMessage(`api/agentic/chat/history/${sessionId}`, {
      method: "GET",
    });

    const { errorCode, data } = result || {};
    if (errorCode === 0) {
      return {
        status: true,
        data: (data?.messages as ChatHistoryMessage[]) ?? [],
      };
    }
    return { status: false, data: [] };
  } catch (error) {
    console.error(error);
    return { status: false, data: [] };
  }
};

/** Xóa một cuộc trò chuyện và toàn bộ lịch sử của nó. */
export const deleteChatSession = async (
  sessionId: string,
): Promise<{ status: boolean }> => {
  try {
    const result = await sendMessage(`api/agentic/chat/session/${sessionId}`, {
      method: "DELETE",
    });
    return { status: (result?.errorCode ?? -1) === 0 };
  } catch (error) {
    console.error(error);
    return { status: false };
  }
};
