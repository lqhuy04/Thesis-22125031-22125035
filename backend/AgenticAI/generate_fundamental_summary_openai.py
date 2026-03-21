import json

from agents.service.openai_fundamental import summarize_fundamental


# Separate OpenAI script: generate and store fundamental summary in DB.
SYMBOL = "VHM"
COMPANY_NAME = None
YEAR = None
LIMIT = 5
SHOW_RAW = False


def main() -> None:
    result = summarize_fundamental(
        symbol=SYMBOL,
        company_name=COMPANY_NAME,
        year=YEAR,
        limit=LIMIT,
    )

    print(f"Symbol: {result['symbol']}")
    print(f"Company: {result['company_name']}")
    print(f"Source years: {result['source_years']}")
    print("\n=== OpenAI Fundamental Summary (Saved To DB) ===")
    print(result["analysis"])

    if SHOW_RAW:
        print("\n=== Raw Data ===")
        print(json.dumps(result["raw_data"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
