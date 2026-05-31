from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any
import pandas as pd

from agentic_ai.analyze.agents.aggregator import aggregator_agent
from agentic_ai.analyze.nodes.article import article_agent
from agentic_ai.analyze.nodes.fundamental_analysis import fundamental_analysis_agent
from agentic_ai.analyze.nodes.technical_analysis import technical_analysis_agent
from agentic_ai.analyze.state import AgentState


class BacktestPipeline:
    def __init__(self, symbol: str, trade_config: dict[str, Any]) -> None:
        self.symbol = symbol
        self.trade_config = trade_config
        self._cache: dict[str, Any] = {}

    def _build_state(self, date: str, interval: str, lookback_days: int) -> AgentState:
        end_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=lookback_days)
        from_date = start_date.strftime("%Y-%m-%d")

        plan = {
            "technical_analysis_agent": {
                "interval": interval,
                "from_date": from_date,
                "to_date": date,
            },
            "article_agent": {
                "from_date": from_date,
                "to_date": date,
            },
            "fundamental_analysis_agent": {},
        }

        return {
            "mode": "auto",
            "user_input": f"Backtest pipeline for {self.symbol} on {date}",
            "risk_appetite": {},
            "symbol": self.symbol,
            "plan": plan,
            "agent_results": {},
            "final_output": None,
            "error": None,
        }

    def run_pipeline_at(
        self,
        date: str,
        interval: str,
        lookback_days: int,
    ) -> dict[str, Any]:
        state = self._build_state(date, interval, lookback_days)

        technical_result = technical_analysis_agent(state)
        state["agent_results"].update(technical_result.get("agent_results", {}))

        article_cache_key = f"article:{date}"
        if article_cache_key in self._cache:
            state["agent_results"]["article_agent"] = self._cache[article_cache_key]
        else:
            article_result = article_agent(state)
            article_value = article_result.get("agent_results", {}).get("article_agent")
            state["agent_results"]["article_agent"] = article_value
            self._cache[article_cache_key] = article_value

        fundamental_result = fundamental_analysis_agent(state)
        state["agent_results"].update(fundamental_result.get("agent_results", {}))

        aggregator_result = aggregator_agent(state)
        final_output = aggregator_result.get("final_output", {})

        technical_output = state["agent_results"].get("technical_analysis_agent", {})
        total_score = None
        if isinstance(technical_output, dict):
            total_score = technical_output.get("total_score")

        return {
            "date": date,
            "recommendation": final_output.get("recommendation"),
            "confidence": final_output.get("confidence"),
            "data_sources_used": final_output.get("data_sources_used", []),
            "total_score": total_score,
            "analysis": final_output.get("analysis"),
        }

    def run_pipeline_batch(
        self,
        dates: list[str],
        interval: str,
        lookback_days: int,
        delay_seconds: float = 0.5,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        total = len(dates)

        for idx, date in enumerate(dates, start=1):
            try:
                result = self.run_pipeline_at(date, interval, lookback_days)
                recommendation = result.get("recommendation")
                confidence = result.get("confidence")
                print(f"[{idx}/{total}] {date} -> {recommendation} ({confidence})")
                results.append(result)
            except Exception as exc:
                print(f"[{idx}/{total}] {date} -> ERROR: {exc}")
                results.append({"date": date, "error": str(exc)})

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        return results

    def filter_signal_dates(self, df: pd.DataFrame, min_score: int = 3) -> list[str]:
        total_score = df["total_score"]
        mask = (total_score >= min_score) & (total_score.shift(1) < min_score)
        dates = df.loc[mask, "datetime"] if "datetime" in df.columns else df.index[mask]
        return [pd.to_datetime(date).strftime("%Y-%m-%d") for date in dates]
