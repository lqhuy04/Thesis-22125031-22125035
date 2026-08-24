"""Persistence and ownership checks for Stockrium Lab experiments."""

from __future__ import annotations

from threading import Lock
from typing import Any
from uuid import uuid4

from psycopg.types.json import Jsonb

from agentic_ai.chatbot.db import get_pool
from app.models.experiment_schemas import ExperimentStatus, ExperimentType
from app.utils.reproducibility import build_reproducibility_metadata


TABLE_NAME = "experiments"
_LIST_COLUMNS = (
    "id, user_id, name, experiment_type, status, scope, symbol, mode, "
    "configuration, result_summary, result_reference, error_message, "
    "created_at, updated_at, completed_at, duration_ms"
)
_DETAIL_COLUMNS = (
    "id, user_id, name, experiment_type, status, scope, symbol, mode, "
    "configuration, reproducibility, result_summary, result_data, "
    "result_reference, error_message, created_at, updated_at, completed_at, "
    "duration_ms"
)
_LIST_KEYS = [
    "id",
    "user_id",
    "name",
    "experiment_type",
    "status",
    "scope",
    "symbol",
    "mode",
    "configuration",
    "result_summary",
    "result_reference",
    "error_message",
    "created_at",
    "updated_at",
    "completed_at",
    "duration_ms",
]
_DETAIL_KEYS = [
    "id",
    "user_id",
    "name",
    "experiment_type",
    "status",
    "scope",
    "symbol",
    "mode",
    "configuration",
    "reproducibility",
    "result_summary",
    "result_data",
    "result_reference",
    "error_message",
    "created_at",
    "updated_at",
    "completed_at",
    "duration_ms",
]


def _serialize_row(row: tuple | None, *, detail: bool = False) -> dict[str, Any] | None:
    if row is None:
        return None
    keys = _DETAIL_KEYS if detail else _LIST_KEYS
    result = dict(zip(keys, row))
    for key in ("created_at", "updated_at", "completed_at"):
        value = result.get(key)
        if value is not None:
            result[key] = value.isoformat()
    result["id"] = str(result["id"])
    return result


class ExperimentService:
    _table_ready = False
    _table_lock = Lock()

    @classmethod
    def ensure_table(cls) -> None:
        if cls._table_ready:
            return
        with cls._table_lock:
            if cls._table_ready:
                return
            pool = get_pool()
            with pool.connection() as conn:
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                        id UUID PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        experiment_type TEXT NOT NULL
                            CHECK (experiment_type IN ('backtest', 'analysis')),
                        status TEXT NOT NULL
                            CHECK (status IN ('running', 'completed', 'failed')),
                        scope TEXT NOT NULL,
                        symbol TEXT,
                        mode TEXT NOT NULL,
                        configuration JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        reproducibility JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        result_summary JSONB,
                        result_data JSONB,
                        result_reference TEXT,
                        error_message TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        completed_at TIMESTAMPTZ,
                        duration_ms BIGINT
                    );
                    """
                )
                conn.execute(
                    f"ALTER TABLE {TABLE_NAME} ADD COLUMN IF NOT EXISTS "
                    "reproducibility JSONB NOT NULL DEFAULT '{}'::jsonb;"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_user_created "
                    f"ON {TABLE_NAME} (user_id, created_at DESC);"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_user_type_status "
                    f"ON {TABLE_NAME} (user_id, experiment_type, status);"
                )
                # The API uses a privileged server-side PostgreSQL connection.
                # RLS blocks accidental direct access through Supabase/PostgREST.
                conn.execute(f"ALTER TABLE {TABLE_NAME} ENABLE ROW LEVEL SECURITY;")
            cls._table_ready = True

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        experiment_type: ExperimentType,
        scope: str,
        symbol: str | None,
        mode: str,
        configuration: dict[str, Any],
        name: str | None = None,
    ) -> dict[str, Any]:
        cls.ensure_table()
        experiment_id = str(uuid4())
        target = symbol or scope
        requested_name = (name or "").strip()
        experiment_name = requested_name or f"{experiment_type.value.title()} · {target}"
        reproducibility = build_reproducibility_metadata(
            experiment_type=experiment_type.value,
            configuration=configuration,
            scope=scope,
            symbol=symbol,
        )
        pool = get_pool()
        with pool.connection() as conn:
            row = conn.execute(
                f"""
                INSERT INTO {TABLE_NAME} (
                    id, user_id, name, experiment_type, status, scope,
                    symbol, mode, configuration, reproducibility
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING {_DETAIL_COLUMNS};
                """,
                (
                    experiment_id,
                    user_id,
                    experiment_name[:160],
                    experiment_type.value,
                    ExperimentStatus.RUNNING.value,
                    scope,
                    symbol,
                    mode,
                    Jsonb(configuration),
                    Jsonb(reproducibility),
                ),
            ).fetchone()
        return _serialize_row(row, detail=True) or {}

    @classmethod
    def complete(
        cls,
        *,
        experiment_id: str,
        user_id: str,
        result_summary: dict[str, Any],
        result_data: dict[str, Any] | None = None,
        result_reference: str | None = None,
    ) -> dict[str, Any]:
        cls.ensure_table()
        pool = get_pool()
        with pool.connection() as conn:
            row = conn.execute(
                f"""
                UPDATE {TABLE_NAME}
                SET status = %s,
                    result_summary = %s,
                    result_data = %s,
                    result_reference = %s,
                    error_message = NULL,
                    completed_at = now(),
                    updated_at = now(),
                    duration_ms = GREATEST(
                        0,
                        (EXTRACT(EPOCH FROM (now() - created_at)) * 1000)::BIGINT
                    )
                WHERE id = %s AND user_id = %s
                RETURNING {_DETAIL_COLUMNS};
                """,
                (
                    ExperimentStatus.COMPLETED.value,
                    Jsonb(result_summary),
                    Jsonb(result_data) if result_data is not None else None,
                    result_reference,
                    experiment_id,
                    user_id,
                ),
            ).fetchone()
        if row is None:
            raise PermissionError("Experiment not found for current user")
        return _serialize_row(row, detail=True) or {}

    @classmethod
    def fail(
        cls,
        *,
        experiment_id: str,
        user_id: str,
        error_message: str,
    ) -> None:
        cls.ensure_table()
        pool = get_pool()
        with pool.connection() as conn:
            conn.execute(
                f"""
                UPDATE {TABLE_NAME}
                SET status = %s,
                    error_message = %s,
                    completed_at = now(),
                    updated_at = now(),
                    duration_ms = GREATEST(
                        0,
                        (EXTRACT(EPOCH FROM (now() - created_at)) * 1000)::BIGINT
                    )
                WHERE id = %s AND user_id = %s;
                """,
                (
                    ExperimentStatus.FAILED.value,
                    (error_message or "Experiment failed")[:1000],
                    experiment_id,
                    user_id,
                ),
            )

    @classmethod
    def list_for_user(
        cls,
        *,
        user_id: str,
        experiment_type: ExperimentType | None = None,
        status: ExperimentStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        cls.ensure_table()
        conditions = ["user_id = %s"]
        params: list[Any] = [user_id]
        if experiment_type is not None:
            conditions.append("experiment_type = %s")
            params.append(experiment_type.value)
        if status is not None:
            conditions.append("status = %s")
            params.append(status.value)
        params.extend([limit, offset])
        pool = get_pool()
        with pool.connection() as conn:
            rows = conn.execute(
                f"""
                SELECT {_LIST_COLUMNS}
                FROM {TABLE_NAME}
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
                """,
                tuple(params),
            ).fetchall()
        return [_serialize_row(row) or {} for row in rows]

    @classmethod
    def get_for_user(
        cls,
        *,
        experiment_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        cls.ensure_table()
        pool = get_pool()
        with pool.connection() as conn:
            row = conn.execute(
                f"""
                SELECT {_DETAIL_COLUMNS}
                FROM {TABLE_NAME}
                WHERE id = %s AND user_id = %s
                LIMIT 1;
                """,
                (experiment_id, user_id),
            ).fetchone()
        return _serialize_row(row, detail=True)

    @classmethod
    def get_many_for_user(
        cls,
        *,
        experiment_ids: list[str],
        user_id: str,
    ) -> list[dict[str, Any]]:
        """Load experiment details in requested order, restricted to one owner."""
        cls.ensure_table()
        if not experiment_ids:
            return []
        if len(experiment_ids) > 5:
            raise ValueError("A comparison supports at most five experiments")

        placeholders = ", ".join(["%s"] * len(experiment_ids))
        pool = get_pool()
        with pool.connection() as conn:
            rows = conn.execute(
                f"""
                SELECT {_DETAIL_COLUMNS}
                FROM {TABLE_NAME}
                WHERE user_id = %s AND id IN ({placeholders});
                """,
                (user_id, *experiment_ids),
            ).fetchall()

        serialized = [_serialize_row(row, detail=True) or {} for row in rows]
        by_id = {item["id"]: item for item in serialized}
        return [by_id[item_id] for item_id in experiment_ids if item_id in by_id]
