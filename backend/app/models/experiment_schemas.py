"""Schemas for user-owned Stockrium Lab experiments."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ExperimentType(str, Enum):
    BACKTEST = "backtest"
    ANALYSIS = "analysis"


class ExperimentStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentRecord(BaseModel):
    id: str
    user_id: str
    name: str
    experiment_type: ExperimentType
    status: ExperimentStatus
    scope: str
    symbol: str | None = None
    mode: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    reproducibility: dict[str, Any] = Field(default_factory=dict)
    result_summary: dict[str, Any] | None = None
    result_data: dict[str, Any] | None = None
    result_reference: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None


class ExperimentComparisonRequest(BaseModel):
    experiment_ids: list[UUID] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_unique_ids(self):
        if len(set(self.experiment_ids)) != len(self.experiment_ids):
            raise ValueError("Danh sách thử nghiệm không được chứa ID trùng nhau")
        return self
