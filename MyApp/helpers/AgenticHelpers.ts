import { sendMessage } from "./api/ApiClients";
import { getRiskAppetite } from "./ProfileHelpers";

export type AnalysisData = {
  summary: string;
  recommendation: string;
  reasoning: string;
  confidence: number;
  tactical_suggestion: string;
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
        plan: {},
        symbol: symbol,
        risk_appetite: riskAppetite.data,
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
