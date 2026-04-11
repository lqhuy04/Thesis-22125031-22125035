import os
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment.")
    return create_client(supabase_url, supabase_key)

def get_articles(symbol: str, from_date: str, to_date: str):
    """
    Lấy danh sách bài báo liên quan đến một mã chứng khoán + thị trường trong khoảng thời gian nhất định.
    """
    try: 
        supabase = _get_supabase_client();
    
        stock = supabase.table("Stock").select("id").eq("stock_symbol", symbol).execute()
        
        stock_id = stock.data[0]["id"] if stock.data else None
        if not stock_id:
            return []
        
        result = (
            supabase.table("Article_Stock")
            .select("Article(*)")
            .eq("stock_id", stock_id)
            .execute()
        )
        
        if not result.data:
            return []
        
        formatted_result = []
        for item in result.data:
            article = item.get("Article")
            if not article:
                continue

            article_time = article.get("time")
            if not article_time:
                continue

            # Filter theo khoảng ngày
            if from_date <= article_time <= to_date:
                formatted_result.append({
                    "time": article_time,
                    "title": article.get("title"),
                    "summary": article.get("summary"),
                })
        
        # Sort theo thời gian cũ -> mới
        formatted_result.sort(key=lambda x: x["time"])
        return formatted_result

    except Exception as e:
        print(f"[Database Service] get_articles error: {e}")
        return []
    
def get_fundamental_analysis(symbol: str, indicators: list[str]):
    """
    Lấy chỉ số phân tích cơ bản cho một mã chứng khoán.
    """
    try:
        supabase = _get_supabase_client();
    
        stock = supabase.table("Stock").select("id").eq("stock_symbol", symbol).execute()
        
        stock_id = stock.data[0]["id"] if stock.data else None
        if not stock_id:
            return {
                "summary": "",
                "indicators": {},
            }
        
        summary_result = (
            supabase.table("FA_Summary")
            .select("summary")
            .eq("stock_id", stock_id)
            .execute()
        )
        
        if not summary_result.data:
            return {
                "summary": "",
                "indicators": {},
            }
        
        if not indicators:
            return {"summary": summary_result.data[0]["summary"], "indicators": {}}
        
        indicators_result = (
            supabase.table("FA_Indicator")
            .select(",".join(indicators))
            .eq("stock_id", stock_id)
            .execute()
        )
        
        if  not indicators_result.data:
            return {
                "summary": "",
                "indicators": {},
            }
        
        return  {
            "summary": summary_result.data[0]["summary"],
            "indicators": indicators_result.data[0],
        }
            
    except Exception as e:
        print(f"[Database Service] get_fundamental_analysis error: {e}")
        return {
            "summary": "",
            "indicators": {},
        }
        
        
        
def get_technical_analysis(symbol: str, interval: str, from_date: str, to_date: str, indicators: list[str]):
    """
    Lấy chỉ số phân tích kỹ thuật cho một mã chứng khoán.
    """
    try:
        from_iso = f"{from_date}T00:00:00+00:00"
        to_iso = f"{to_date}T23:59:59+00:00"

        supabase = _get_supabase_client();
        response = supabase.table(f"Stock_Price_{interval}") \
                .select("trading_time, open, high, low, close, volume") \
                .eq("symbol", symbol.upper()) \
                .gte("trading_time", from_iso) \
                .lte("trading_time", to_iso) \
                .order("trading_time", desc=False) \
                .execute()
                
        if not response.data:
            return {
                "priceData": [],
                "indicatorsData": [],
            }
            
        if not indicators:     
            return {
                "priceData": response.data,
                "indicatorsData": [],
            }
            
        
        
    except Exception as e:
        print(f"[Database Service] get_technical_analysis error: {e}")
        return {
            "priceData": [],
            "indicatorsData": [],
        }