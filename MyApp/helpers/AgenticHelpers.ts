import { sendMessage } from "./api/ApiClients";
import { getRiskAppetite } from "./ProfileHelpers";

export type AnalysisData = {
  recommendation: string;
  entry_price: number | null;
  take_profit_price: number | null;
  stop_loss_price: number | null;
  max_hold_candles: number | null;
  confidence: number;
  analysis: string;
};

export const getAnalysis = async (
  symbol: string,
): Promise<{
  status: boolean;
  data: AnalysisData | null;
}> => {
  try {
    const riskAppetite = await getRiskAppetite();

    const result = await sendMessage("api/agentic/analyze", {
      method: "POST",
      body: JSON.stringify({
        mode: "auto",
        symbol: symbol,
        risk_appetite: riskAppetite?.data,
      }),
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
