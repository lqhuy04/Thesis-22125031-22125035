"""Reproducibility metadata and investment-safety notices for experiments."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any

from app.config import settings


REPRODUCIBILITY_SCHEMA_VERSION = "1.0"
PIPELINE_VERSION = "stockrium-agentic-v2"
PROMPT_BUNDLE_VERSION = "2026-08-24"

_INVESTMENT_DISCLAIMER = {
    "version": "2026-08-24",
    "severity": "warning",
    "title": "Không phải khuyến nghị đầu tư",
    "message": (
        "Kết quả AI và backtest chỉ phục vụ nghiên cứu, học tập và thử nghiệm. "
        "Thông tin có thể thiếu, chậm hoặc sai và không bảo đảm hiệu quả trong tương lai."
    ),
    "points": [
        "Backtest không phản ánh đầy đủ thanh khoản, trượt giá và điều kiện giao dịch thực tế.",
        "Kết quả AI có thể thay đổi theo dữ liệu thị trường và phiên bản mô hình.",
        "Người dùng tự chịu trách nhiệm khi đưa ra quyết định và nên tham khảo chuyên gia phù hợp.",
    ],
}


def investment_disclaimer() -> dict[str, Any]:
    return deepcopy(_INVESTMENT_DISCLAIMER)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def normalized_experiment_configuration(
    configuration: dict[str, Any],
) -> dict[str, Any]:
    """Remove labels and normalize identifiers that do not change execution."""
    normalized = deepcopy(configuration)
    normalized.pop("experiment_name", None)
    for field in ("symbol", "universe", "market_symbol"):
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = value.strip().upper()
    return normalized


def configuration_fingerprint(configuration: dict[str, Any]) -> str:
    normalized = normalized_experiment_configuration(configuration)
    return sha256(_canonical_json(normalized).encode("utf-8")).hexdigest()


def build_reproducibility_metadata(
    *,
    experiment_type: str,
    configuration: dict[str, Any],
    scope: str,
    symbol: str | None,
) -> dict[str, Any]:
    captured_at = datetime.now(timezone.utc)
    data_as_of_date = (
        captured_at.astimezone(timezone(timedelta(hours=7))).date().isoformat()
        if experiment_type == "analysis"
        else configuration.get("end_date")
    )
    config_hash = configuration_fingerprint(configuration)
    code_revision = settings.CODE_REVISION or "unknown"
    stable_context = {
        "configuration_sha256": config_hash,
        "app_version": settings.VERSION,
        "code_revision": code_revision,
        "pipeline_version": PIPELINE_VERSION,
        "prompt_bundle_version": PROMPT_BUNDLE_VERSION,
        "ai_model": settings.DEEPSEEK_MODEL,
        "experiment_type": experiment_type,
        "scope": scope,
        "symbol": symbol.strip().upper() if symbol else None,
        "data_as_of_date": data_as_of_date,
        "data_snapshot_mode": "live_sources",
    }
    run_fingerprint = sha256(
        _canonical_json(stable_context).encode("utf-8")
    ).hexdigest()
    risk_period = (
        (configuration.get("risk_appetite") or {}).get("period")
        if isinstance(configuration.get("risk_appetite"), dict)
        else None
    )

    return {
        "schema_version": REPRODUCIBILITY_SCHEMA_VERSION,
        "captured_at": captured_at.isoformat(),
        "configuration_sha256": config_hash,
        "run_fingerprint": run_fingerprint,
        "application": {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "code_revision": code_revision,
        },
        "pipeline": {
            "version": PIPELINE_VERSION,
            "prompt_bundle_version": PROMPT_BUNDLE_VERSION,
        },
        "ai": {
            "provider": "deepseek",
            "model": settings.DEEPSEEK_MODEL,
            "temperature": 0.1,
            "random_seed": None,
            "seed_supported": False,
        },
        "data": {
            "snapshot_mode": "live_sources",
            "immutable_snapshot": False,
            "as_of_date": data_as_of_date,
            "start_date": configuration.get("start_date"),
            "end_date": configuration.get("end_date"),
            "market_symbol": configuration.get("market_symbol"),
            "risk_period": risk_period,
        },
        "reproducibility_level": "configuration_only",
        "limitations": [
            "Cấu hình được lưu đầy đủ nhưng dữ liệu nguồn chưa được đóng băng thành snapshot bất biến.",
            "Nhà cung cấp AI không hỗ trợ seed trong pipeline hiện tại nên kết quả có thể thay đổi giữa các lần chạy.",
            "Muốn đối chiếu chính xác cần giữ nguyên code revision, model, prompt và dữ liệu nguồn.",
        ],
    }
