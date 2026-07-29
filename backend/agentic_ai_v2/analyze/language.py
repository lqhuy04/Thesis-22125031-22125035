"""Language helpers shared by user-facing v2 analysis agents."""

from typing import Any, Literal


AnalysisLanguage = Literal["vi", "en"]


def normalize_language(value: Any) -> AnalysisLanguage:
    """Keep existing clients backward-compatible by defaulting to Vietnamese."""
    return "en" if str(value or "").strip().lower() == "en" else "vi"


def output_language_instruction(value: Any) -> str:
    """Return a strong output-only instruction for the selected app language."""
    if normalize_language(value) == "en":
        return (
            "OUTPUT LANGUAGE: Write all user-facing text entirely in English. "
            "Translate Vietnamese source content and financial terms naturally. "
            "Do not include a Vietnamese version."
        )
    return (
        "NGÔN NGỮ ĐẦU RA: Viết toàn bộ nội dung hiển thị cho người dùng bằng "
        "tiếng Việt. Không kèm bản dịch tiếng Anh."
    )


def localized_text(value: Any, *, vi: str, en: str) -> str:
    """Select deterministic fallback text in the requested language."""
    return en if normalize_language(value) == "en" else vi
