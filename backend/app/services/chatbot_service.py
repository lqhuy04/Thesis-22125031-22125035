import json
from typing import Any

from openai import OpenAI

from app.config import settings
from app.models.chatbot_schemas import ChatbotData
from app.services.market_service import MarketService, supabase


class ChatbotService:
    MODEL_NAME = "gpt-4o-mini"
    HORIZON_LOOKBACKS = {
        "short": 2000,
        "mid": 100,
        "long": 350,
    }
    HORIZON_TABLES = {
        "short": ["Stock_price_1m", "Stock_Price_1m"],
        "mid": ["Stock_Price_1d", "Stock_price_1d"],
        "long": ["Stock_Price_1d", "Stock_price_1d"],
    }

    @staticmethod
    def _fetch_candles(symbol: str, horizon: str, limit: int) -> list[dict[str, Any]]:
        """Fetch recent candles for the requested horizon with table-name fallback."""
        table_candidates = ChatbotService.HORIZON_TABLES.get(horizon, ChatbotService.HORIZON_TABLES["short"])

        for table_name in table_candidates:
            try:
                result = (
                    supabase.table(table_name)
                    .select("trading_time, open, high, low, close, volume")
                    .eq("symbol", symbol)
                    .order("trading_time", desc=True)
                    .limit(limit)
                    .execute()
                )
                if result.data:
                    # Return ASC order for easier trend calculations.
                    return list(reversed(result.data))
            except Exception:
                continue

        return []

    @staticmethod
    def _build_compact_summary(candles: list[dict[str, Any]], horizon: str, timeframe: str) -> dict[str, Any]:
        """Compress candle data into compact stats to save prompt tokens."""
        if not candles:
            return {}

        closes = [float(item.get("close") or 0) for item in candles]
        highs = [float(item.get("high") or 0) for item in candles]
        lows = [float(item.get("low") or 0) for item in candles]
        volumes = [float(item.get("volume") or 0) for item in candles]

        first_close = closes[0]
        last_close = closes[-1]
        pct_change = ((last_close - first_close) / first_close * 100) if first_close else 0.0

        # Keep a tiny sampled close series (12 points max) instead of full candles.
        sample_size = min(12, len(closes))
        stride = max(1, len(closes) // sample_size)
        sampled_close_series = [round(closes[i], 3) for i in range(0, len(closes), stride)][:sample_size]

        return {
            "timeframe": timeframe,
            "time_horizon": horizon,
            "window_records": len(candles),
            "start_time": candles[0].get("trading_time"),
            "end_time": candles[-1].get("trading_time"),
            "first_close": round(first_close, 3),
            "last_close": round(last_close, 3),
            "change_pct": round(pct_change, 3),
            "high_max": round(max(highs), 3),
            "low_min": round(min(lows), 3),
            "volume_sum": int(sum(volumes)),
            "sampled_close_series": sampled_close_series,
        }

    @staticmethod
    def _build_market_instruction(horizon: str) -> str:
        if horizon == "short":
            return (
                "Focus on very short-term intraday behavior, momentum, and immediate support/resistance. "
                "Base the answer only on the provided 1m summary."
            )
        if horizon == "mid":
            return (
                "Focus on swing behavior, trend persistence, and broader price structure. "
                "Base the answer only on the provided daily summary."
            )
        return (
            "Focus on the broader medium-term trend visible in the provided daily summary. "
            "Do not turn daily price data into unsupported fundamentals."
        )

    @staticmethod
    def _select_lookback(horizon: str) -> int:
        return ChatbotService.HORIZON_LOOKBACKS.get(horizon, 120)

    @staticmethod
    def chat(
        message: str,
        system_prompt: str | None = None,
        symbol: str | None = None,
        time_horizon: str = "short",
    ) -> ChatbotData:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        messages = []

        symbol_value = (symbol or "").strip().upper()
        horizon_value = (time_horizon or "short").strip().lower()
        lookback_limit = ChatbotService._select_lookback(horizon_value)
        if symbol_value:
            current_price = MarketService.get_current_stock_price(symbol_value)
            timeframe = "1m" if horizon_value == "short" else "1d"
            candles = ChatbotService._fetch_candles(symbol_value, horizon_value, limit=lookback_limit)
            compact_summary = ChatbotService._build_compact_summary(candles, horizon_value, timeframe)

            if not current_price:
                return ChatbotData(
                    model=ChatbotService.MODEL_NAME,
                    reply=(
                        f"Insufficient data for symbol {symbol_value}. "
                        "Please check the symbol or try again later."
                    ),
                )

            market_context = {
                "symbol": symbol_value,
                "time_horizon": horizon_value,
                "timeframe": timeframe,
                "current_stock_price": current_price,
                "compact_summary": compact_summary,
            }

            grounded_system_prompt = (
                "You are a Vietnamese stock analysis assistant. "
                "Use only the market data provided by the user context. "
                "Do not invent prices, support/resistance levels, indicators, or events. "
                "If any requested metric is missing, explicitly say it is missing. "
                "Output must be concise, factual, and educational (not financial advice). "
                f"{ChatbotService._build_market_instruction(horizon_value)}"
            )

            if system_prompt:
                grounded_system_prompt = f"{grounded_system_prompt}\n\nAdditional instruction: {system_prompt}"

            messages.append({"role": "system", "content": grounded_system_prompt})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"User question: {message}\n\n"
                        "Ground truth market data (JSON):\n"
                        f"{json.dumps(market_context, ensure_ascii=False)}"
                    ),
                }
            )
        else:
            generic_system_prompt = (
                "You are a helpful assistant. "
                "If real-time market data is required but not provided, say that data is missing "
                "instead of guessing values."
            )
            if system_prompt:
                generic_system_prompt = f"{generic_system_prompt}\n\nAdditional instruction: {system_prompt}"

            messages.append({"role": "system", "content": generic_system_prompt})
            messages.append({"role": "user", "content": message})

        completion = client.chat.completions.create(
            model=ChatbotService.MODEL_NAME,
            messages=messages,
            temperature=0.2,
        )

        reply = completion.choices[0].message.content if completion.choices else ""
        return ChatbotData(model=ChatbotService.MODEL_NAME, reply=reply or "")
