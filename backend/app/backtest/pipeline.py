from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable

import pandas as pd

from agentic_ai_v2.analyze.agents.orchestrator import build_analysis_plan
from agentic_ai_v2.analyze.agents.aggregator import aggregator_agent
from agentic_ai_v2.analyze.agents.article import article_agent
from agentic_ai_v2.analyze.agents.article_analysis import (
    article_analysis_agent,
)
from agentic_ai_v2.analyze.agents.fundamental import fundamental_agent
from agentic_ai_v2.analyze.agents.fundamental_analysis import (
    fundamental_analysis_agent,
)
from agentic_ai_v2.analyze.agents.recommendation import (
    TECHNICAL_SCORE_THRESHOLD,
    recommendation_agent,
)
from agentic_ai_v2.analyze.agents.technical import technical_agent
from agentic_ai_v2.analyze.agents.technical_analysis import (
    technical_analysis_agent,
)
from agentic_ai_v2.analyze.state import AgentState
from agentic_ai_v2.analyze.technical_scoring import (
    SCORE_COLUMN_BY_INDICATOR,
)


AgentCallable = Callable[[AgentState], dict]
TECHNICAL_SIGNAL_SCORE = (
    TECHNICAL_SCORE_THRESHOLD * len(SCORE_COLUMN_BY_INDICATOR)
)


class BacktestPipeline:
    """Historical adapter for the production v2 analysis agents.

    The existing backtest engine is daily, so its v2 risk period is fixed to
    ``mid_term`` (the production period whose technical interval is ``1d``).
    """

    def __init__(
        self,
        symbol: str,
        trade_config: dict[str, Any],
        mode: str = "auto",
        data_selection: dict | None = None,
    ) -> None:
        self.symbol = symbol
        self.trade_config = trade_config
        self.mode = mode
        self.data_selection = data_selection or {}
        self._cache: dict[str, dict[str, Any]] = {}

    def _build_state(
        self,
        date: str,
    ) -> AgentState:
        analysis_date = datetime.strptime(date, "%Y-%m-%d").date()
        plan = build_analysis_plan("mid_term", as_of_date=analysis_date)
        # Never read Current_Stock_Price in a historical simulation.
        # technical_agent will use the final candle at/before `date`.
        plan["technical"]["use_current_price"] = False
        plan["fundamental"] = {
            # fundamental_agent conservatively excludes annual rows from
            # the simulated year and all future years.
            "as_of_date": date,
        }

        return {
            "mode": self.mode,
            "user_input": f"Backtest pipeline for {self.symbol} on {date}",
            "risk_appetite": {"period": "mid_term"},
            "symbol": self.symbol,
            "data_selection": self.data_selection,
            "plan": plan,
            "agent_results": {},
            "final_output": None,
            "error": None,
        }

    def _source_enabled(self, source: str) -> bool:
        if self.mode == "auto":
            return True
        if source == "technical":
            # The request schema guarantees at least one selected indicator.
            return True
        if source == "article":
            return self.data_selection.get("news") is True
        if source == "fundamental":
            return self.data_selection.get("fundamental") is True
        return False

    def selected_indicators(self) -> list[str]:
        """Return the effective technical indicators in display order."""
        if self.mode == "auto":
            return list(SCORE_COLUMN_BY_INDICATOR)

        technical = self.data_selection.get("technical") or {}
        return [
            name
            for name in SCORE_COLUMN_BY_INDICATOR
            if technical.get(name) is True
        ]

    def configuration(self) -> dict[str, Any]:
        """Describe the effective historical pipeline for reports and the UI."""
        data_sources = ["technical"]
        if self._source_enabled("article"):
            data_sources.append("article")
        if self._source_enabled("fundamental"):
            data_sources.append("fundamental")

        default_weights = {
            "news": 0.20,
            "technical": 0.40,
            "fundamental": 0.40,
        }
        requested_weights = self.data_selection.get("weight")
        weights = (
            requested_weights
            if self.mode == "manual" and isinstance(requested_weights, dict)
            else default_weights
        )

        return {
            "mode": self.mode,
            "period": "mid_term",
            "interval": "1d",
            "data_sources": data_sources,
            "selected_indicators": self.selected_indicators(),
            "weights": weights,
        }

    @staticmethod
    def _apply_agent(state: AgentState, agent: AgentCallable) -> None:
        result = agent(state)
        if result.get("error"):
            raise RuntimeError(str(result["error"]))
        state["agent_results"].update(result.get("agent_results", {}))

    def _apply_cached_chain(
        self,
        state: AgentState,
        cache_key: str,
        source_agent: AgentCallable,
        analysis_agent: AgentCallable,
    ) -> None:
        cached = self._cache.get(cache_key)
        if cached is not None:
            state["agent_results"].update(cached)
            return

        before = set(state["agent_results"])
        self._apply_agent(state, source_agent)
        self._apply_agent(state, analysis_agent)
        chain_results = {
            key: value
            for key, value in state["agent_results"].items()
            if key not in before
        }
        self._cache[cache_key] = chain_results

    def _run_source_chain(
        self,
        state: AgentState,
        source_agent: AgentCallable,
        analysis_agent: AgentCallable,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        """Run one dependent source/analysis chain on isolated state.

        Each source branch receives its own ``agent_results`` dictionary so the
        three backtest branches can execute concurrently without mutating the
        shared state. Their results are merged only after every enabled branch
        has completed.
        """
        branch_state: AgentState = {
            **state,
            "agent_results": {},
        }

        if cache_key is None:
            self._apply_agent(branch_state, source_agent)
            self._apply_agent(branch_state, analysis_agent)
        else:
            self._apply_cached_chain(
                branch_state,
                cache_key=cache_key,
                source_agent=source_agent,
                analysis_agent=analysis_agent,
            )

        return dict(branch_state["agent_results"])

    def run_pipeline_at(
        self,
        date: str,
        interval: str,
    ) -> dict[str, Any]:
        if interval != "1d":
            raise ValueError(
                "Backtest v2 hiện chỉ hỗ trợ interval 1d / period mid_term."
            )

        state = self._build_state(date)
        article_from_date = state["plan"]["article"]["from_date"]

        source_chains: list[
            tuple[AgentCallable, AgentCallable, str | None]
        ] = [
            (
                technical_agent,
                technical_analysis_agent,
                None,
            )
        ]

        if self._source_enabled("article"):
            source_chains.append(
                (
                    article_agent,
                    article_analysis_agent,
                    f"article:{article_from_date}:{date}",
                )
            )

        if self._source_enabled("fundamental"):
            source_chains.append(
                (
                    fundamental_agent,
                    fundamental_analysis_agent,
                    f"fundamental:{date[:4]}",
                )
            )

        with ThreadPoolExecutor(
            max_workers=len(source_chains),
            thread_name_prefix="backtest-source",
        ) as executor:
            futures = [
                executor.submit(
                    self._run_source_chain,
                    state,
                    source_agent,
                    analysis_agent,
                    cache_key,
                )
                for source_agent, analysis_agent, cache_key in source_chains
            ]

            # Merge in a stable branch order after all work has been submitted.
            for future in futures:
                state["agent_results"].update(future.result())

        self._apply_agent(state, recommendation_agent)
        aggregate_result = aggregator_agent(state)
        if aggregate_result.get("error"):
            raise RuntimeError(str(aggregate_result["error"]))
        final_output = aggregate_result.get("final_output")
        if not isinstance(final_output, dict):
            raise RuntimeError("Aggregator v2 không trả về final_output hợp lệ.")

        source_names = ["technical"]
        if self._source_enabled("article"):
            source_names.append("article")
        if self._source_enabled("fundamental"):
            source_names.append("fundamental")

        technical_output = state["agent_results"].get("technical_agent") or {}
        score = final_output.get("score") or {}
        buy = bool(final_output.get("buy", False))

        return {
            "date": date,
            "buy": buy,
            # Kept for existing report JSON readers while the decision itself
            # now comes from the v2 boolean contract.
            "recommendation": "Mua" if buy else "Chờ",
            "entry_price": final_output.get("entry_price", 0.0),
            "take_profit_price": final_output.get(
                "take_profit_price",
                0.0,
            ),
            "stop_loss_price": final_output.get("stop_loss_price", 0.0),
            "max_hold_candles": final_output.get("max_hold_candles", 0),
            "confidence": final_output.get("confidence", 0.0),
            "data_sources_used": source_names,
            "score": score,
            "total_score": score.get("total", 0.0),
            "technical_total_score": technical_output.get(
                "total_score",
                0,
            ),
            "analysis": final_output.get("analysis") or {},
            "agent_breakdown": {
                "technical_agent": technical_output,
                "technical_analysis_agent": state["agent_results"].get(
                    "technical_analysis_agent"
                ),
                "fundamental_agent": state["agent_results"].get(
                    "fundamental_agent"
                ),
                "fundamental_analysis_agent": state["agent_results"].get(
                    "fundamental_analysis_agent"
                ),
                "article_agent": state["agent_results"].get("article_agent"),
                "article_analysis_agent": state["agent_results"].get(
                    "article_analysis_agent"
                ),
                "recommendation_agent": state["agent_results"].get(
                    "recommendation_agent"
                ),
            },
        }

    def run_pipeline_batch(
        self,
        dates: list[str],
        interval: str,
        delay_seconds: float = 0.5,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        total = len(dates)

        for idx, date in enumerate(dates, start=1):
            try:
                result = self.run_pipeline_at(
                    date,
                    interval,
                )
                recommendation = result.get("recommendation")
                confidence = result.get("confidence")
                print(
                    f"[{idx}/{total}] {date} -> "
                    f"{recommendation} ({confidence})"
                )
                results.append(result)
            except Exception as exc:
                print(f"[{idx}/{total}] {date} -> ERROR: {exc}")
                results.append({"date": date, "error": str(exc)})

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        return results

    def filter_signal_dates(
        self,
        df: pd.DataFrame,
    ) -> list[str]:
        selected_frame = self.apply_technical_selection(df)
        # A candidate is executable only when the following candle exists for
        # the next-open entry used by SignalGenerator and TradeSimulator.
        executable_frame = selected_frame.iloc[:-1]
        total_score = executable_frame["total_score"]
        mask = total_score >= TECHNICAL_SIGNAL_SCORE
        dates = (
            executable_frame.loc[mask, "datetime"]
            if "datetime" in executable_frame.columns
            else executable_frame.index[mask]
        )
        return [
            pd.to_datetime(date).strftime("%Y-%m-%d")
            for date in dates
        ]

    def apply_technical_selection(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Normalize selected indicator scores back onto the legacy 0–5 scale.

        The fixed production threshold remains 60% even when manual mode enables
        fewer than five indicators, matching the normalized score used by
        technical_analysis_agent and recommendation_agent.
        """
        selected = self.selected_indicators()

        if not selected:
            raise ValueError(
                "Backtest cần ít nhất một chỉ báo kỹ thuật được bật."
            )

        score_columns = [
            SCORE_COLUMN_BY_INDICATOR[name]
            for name in selected
        ]
        missing_columns = [
            column
            for column in score_columns
            if column not in df.columns
        ]
        if missing_columns:
            raise ValueError(
                "Backtest thiếu cột điểm kỹ thuật: "
                + ", ".join(missing_columns)
            )

        output = df.copy()
        selected_total = output[score_columns].sum(axis=1)
        output["total_score"] = selected_total * (
            len(SCORE_COLUMN_BY_INDICATOR) / len(score_columns)
        )

        # Preserve the 50-candle warm-up boundary created by ScoringEngine.
        if "total_score" in df.columns:
            output.loc[df["total_score"].isna(), "total_score"] = float("nan")
        return output
