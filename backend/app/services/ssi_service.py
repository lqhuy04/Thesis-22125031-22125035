"""
SSI FC Data Service
Handles all interactions with SSI's FC Data API for market data

Note: This implementation uses direct HTTP requests instead of the ssi-fc-data library
due to a bug in the library where access_token() passes '_req_body' but _make_post_request()
expects 'data' parameter.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from app.config import get_ssi_config, settings
from app.services.price_db_service import PriceDBService
import logging
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

logger = logging.getLogger(__name__)


# API Endpoints
class SSIEndpoints:
    ACCESS_TOKEN = "api/v2/Market/AccessToken"
    SECURITIES = "api/v2/Market/Securities"
    SECURITIES_DETAILS = "api/v2/Market/SecuritiesDetails"
    INDEX_COMPONENTS = "api/v2/Market/IndexComponents"
    INDEX_LIST = "api/v2/Market/IndexList"
    DAILY_OHLC = "api/v2/Market/DailyOhlc"
    INTRADAY_OHLC = "api/v2/Market/IntradayOhlc"
    DAILY_INDEX = "api/v2/Market/DailyIndex"
    DAILY_STOCK_PRICE = "api/v2/Market/DailyStockPrice"


class SSIMarketDataService:
    """Service class for SSI Market Data API operations"""
    
    def __init__(self):
        from datetime import datetime

        self._config = get_ssi_config()
        self._access_token: Optional[str] = None
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # Per (symbol, interval) in-memory cooldown to avoid redundant sync on repeated calls.
        self._last_sync_at: Dict[tuple, datetime] = {}
        self._sync_cooldown_seconds = 120
        self._daily_price_cache: Dict[str, Dict[str, Any]] = {}
        self._daily_price_cache_ttl_seconds = 60
        self._top_stocks_refresh_lock = threading.Lock()
        self._top_stocks_refresh_running = False
    
    @property
    def config(self):
        return self._config

    def _is_api_success(self, response: Dict[str, Any]) -> bool:
        """Check whether SSI response indicates a successful business result."""
        if not isinstance(response, dict):
            return False
        status = str(response.get("status", "")).strip().lower()
        if not status:
            # Some SSI endpoints may omit status and only return data.
            return bool(response.get("data") is not None)
        return status == "success"

    def _is_auth_error(self, response: Dict[str, Any]) -> bool:
        """Detect token/auth-related API failures from SSI payload."""
        status = str(response.get("status", "")).strip().lower()
        message = str(response.get("message", "")).strip().lower()
        if status in {"unauthorized", "forbidden"}:
            return True
        if "unauthorized" in message or "token" in message or "expired" in message:
            return True
        return False

    def _should_skip_sync(self, symbol: str, interval: str) -> bool:
        """Return True only when DB already has full+fresh cache for this symbol/interval."""
        from datetime import datetime

        key = (symbol.upper(), interval.lower())
        last_sync = self._last_sync_at.get(key)
        if not last_sync:
            return False

        age_seconds = (datetime.now() - last_sync).total_seconds()
        if age_seconds > self._sync_cooldown_seconds:
            return False

        return self._is_db_full_and_latest_today(symbol, interval, target_limit=1000)

    def _is_db_full_and_latest_today(self, symbol: str, interval: str, target_limit: int = 1000) -> bool:
        """
        Fast-return condition:
        - DB has at least target_limit rows for this symbol+interval
        - Latest row belongs to the current calendar day
        """
        latest_rows = PriceDBService.get_latest_prices(symbol=symbol, limit=target_limit, interval=interval)
        return self._is_records_full_and_latest_today(latest_rows, target_limit)

    def _is_records_full_and_latest_today(self, rows: list, target_limit: int = 1000) -> bool:
        """Evaluate cache readiness from already-fetched DB rows."""
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo
            vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        except Exception:
            vn_tz = None

        if len(rows) < target_limit:
            return False

        latest_row = rows[-1] if rows else None
        if not latest_row:
            return False

        latest_raw = str(latest_row.get("trading_time", "")).strip()
        if not latest_raw:
            return False

        try:
            # Normalize ISO parsing with optional Z suffix.
            parsed = datetime.fromisoformat(latest_raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                latest_local = parsed
            elif vn_tz:
                latest_local = parsed.astimezone(vn_tz).replace(tzinfo=None)
            else:
                latest_local = parsed.replace(tzinfo=None)
        except Exception:
            # Fallback: compare date part in raw ISO string.
            latest_date_part = latest_raw.split("T")[0]
            today_date_part = datetime.now().strftime("%Y-%m-%d")
            return latest_date_part == today_date_part

        today_local = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return latest_local.date() == today_local.date()

    def _mark_synced_now(self, symbol: str, interval: str) -> None:
        """Update sync timestamp for cooldown checks."""
        from datetime import datetime

        self._last_sync_at[(symbol.upper(), interval.lower())] = datetime.now()
    
    def _make_post_request(self, endpoint: str, data: dict) -> Dict[str, Any]:
        """Make a POST request to SSI API"""
        url = f"{self._config.url}{endpoint}"
        payload = json.dumps(data)
        response = requests.post(url, headers=self._headers, data=payload)
        return response.json()
    
    def _make_get_request(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
        """Make a GET request to SSI API"""
        url = f"{self._config.url}{endpoint}"
        headers = self._headers.copy()
        if self._access_token:
            headers["Authorization"] = f"{self._config.auth_type} {self._access_token}"
        response = requests.get(url, headers=headers, params=params)
        payload = response.json()

        # Retry once on auth failure by refreshing token.
        if self._is_auth_error(payload):
            token_result = self._get_access_token()
            if token_result.get("success") and self._access_token:
                retry_headers = self._headers.copy()
                retry_headers["Authorization"] = f"{self._config.auth_type} {self._access_token}"
                retry_response = requests.get(url, headers=retry_headers, params=params)
                return retry_response.json()

        return payload
    
    def _ensure_token(self) -> bool:
        """Ensure we have a valid access token"""
        if not self._access_token:
            result = self._get_access_token()
            if result.get("success") and result.get("data", {}).get("data", {}).get("accessToken"):
                self._access_token = result["data"]["data"]["accessToken"]
                return True
            return False
        return True
    
    def _get_access_token(self) -> Dict[str, Any]:
        """Get access token from SSI API"""
        try:
            data = {
                "consumerID": self._config.consumerID,
                "consumerSecret": self._config.consumerSecret
            }
            response = self._make_post_request(SSIEndpoints.ACCESS_TOKEN, data)
            
            # Store the token for subsequent requests
            if response.get("data", {}).get("accessToken"):
                self._access_token = response["data"]["accessToken"]
            
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_securities_list(
        self, 
        market: str, 
        page_index: int = 1, 
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get list of securities from a specific market
        
        Args:
            market: Market code (e.g., 'HNX', 'HOSE', 'UPCOM')
            page_index: Page number for pagination
            page_size: Number of items per page
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "market": market,
                "pageIndex": page_index,
                "pageSize": page_size
            }
            response = self._make_get_request(SSIEndpoints.SECURITIES, params)
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting securities list: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_securities_details(
        self, 
        market: str, 
        symbol: str, 
        page_index: int = 1, 
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get details of a specific security
        
        Args:
            market: Market code (e.g., 'HNX', 'HOSE', 'UPCOM')
            symbol: Stock symbol (e.g., 'ACB', 'VNM')
            page_index: Page number for pagination
            page_size: Number of items per page
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "market": market,
                "symbol": symbol,
                "pageIndex": page_index,
                "pageSize": page_size
            }
            response = self._make_get_request(SSIEndpoints.SECURITIES_DETAILS, params)
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting securities details: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_index_components(
        self, 
        index_code: str, 
        page_index: int = 1, 
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get components of a specific index
        
        Args:
            index_code: Index code (e.g., 'VN30', 'VN100', 'HNX30')
            page_index: Page number for pagination
            page_size: Number of items per page
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "indexCode": index_code,
                "pageIndex": page_index,
                "pageSize": page_size
            }
            response = self._make_get_request(SSIEndpoints.INDEX_COMPONENTS, params)
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting index components: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_index_list(
        self, 
        exchange: str, 
        page_index: int = 1, 
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get list of indices for an exchange
        
        Args:
            exchange: Exchange code (e.g., 'hose', 'hnx')
            page_index: Page number for pagination
            page_size: Number of items per page
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "exchange": exchange,
                "pageIndex": page_index,
                "pageSize": page_size
            }
            response = self._make_get_request(SSIEndpoints.INDEX_LIST, params)
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting index list: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_daily_ohlc(
        self, 
        symbol: str, 
        from_date: str, 
        to_date: str, 
        page_index: int = 1, 
        page_size: int = 100,
        ascending: bool = True
    ) -> Dict[str, Any]:
        """
        Get daily OHLC (Open, High, Low, Close) data for a stock
        
        Args:
            symbol: Stock symbol (e.g., 'VNM', 'FPT')
            from_date: Start date in format 'DD/MM/YYYY'
            to_date: End date in format 'DD/MM/YYYY'
            page_index: Page number for pagination
            page_size: Number of items per page
            ascending: Sort order (True for ascending, False for descending)
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "symbol": symbol,
                "fromDate": from_date,
                "toDate": to_date,
                "pageIndex": page_index,
                "pageSize": page_size,
                "ascending": str(ascending).lower()
            }
            response = self._make_get_request(SSIEndpoints.DAILY_OHLC, params)
            if not self._is_api_success(response):
                return {
                    "success": False,
                    "error": response.get("message") or "SSI Daily OHLC request failed",
                    "data": response,
                }
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting daily OHLC: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_intraday_ohlc(
        self, 
        symbol: str, 
        from_date: str, 
        to_date: str, 
        page_index: int = 1, 
        page_size: int = 100,
        ascending: bool = True,
        resolution: int = 1
    ) -> Dict[str, Any]:
        """
        Get intraday OHLC data for a stock
        
        Args:
            symbol: Stock symbol (e.g., 'VNM', 'FPT')
            from_date: Start date in format 'DD/MM/YYYY'
            to_date: End date in format 'DD/MM/YYYY'
            page_index: Page number for pagination
            page_size: Number of items per page
            ascending: Sort order (True for ascending, False for descending)
            resolution: Time resolution in minutes (1, 5, 15, 30, 60)
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "symbol": symbol,
                "fromDate": from_date,
                "toDate": to_date,
                "pageIndex": page_index,
                "pageSize": page_size,
                "ascending": str(ascending).lower(),
                "resolution": resolution
            }
            response = self._make_get_request(SSIEndpoints.INTRADAY_OHLC, params)
            if not self._is_api_success(response):
                return {
                    "success": False,
                    "error": response.get("message") or "SSI Intraday OHLC request failed",
                    "data": response,
                }
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting intraday OHLC: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_daily_index(
        self, 
        request_id: str,
        index_id: str, 
        from_date: str, 
        to_date: str, 
        page_index: int = 1, 
        page_size: int = 100,
        order_by: str = "",
        order: str = ""
    ) -> Dict[str, Any]:
        """
        Get daily index data
        
        Args:
            request_id: Unique request identifier
            index_id: Index ID (e.g., 'VN100', 'VN30')
            from_date: Start date in format 'DD/MM/YYYY'
            to_date: End date in format 'DD/MM/YYYY'
            page_index: Page number for pagination
            page_size: Number of items per page
            order_by: Field to order by
            order: Sort order ('asc' or 'desc')
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "requestId": request_id,
                "indexId": index_id,
                "fromDate": from_date,
                "toDate": to_date,
                "pageIndex": page_index,
                "pageSize": page_size,
                "orderBy": order_by,
                "order": order
            }
            response = self._make_get_request(SSIEndpoints.DAILY_INDEX, params)
            if not self._is_api_success(response):
                return {
                    "success": False,
                    "error": response.get("message") or "SSI Daily Index request failed",
                    "data": response,
                }

            # Keep only SSI inner `data` for the API's standardized wrapper.
            return {"success": True, "data": response.get("data", [])}
        except Exception as e:
            logger.error(f"Error getting daily index: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_daily_stock_price(
        self, 
        symbol: str, 
        from_date: str, 
        to_date: str, 
        page_index: int = 1, 
        page_size: int = 100,
        market: str = "hose"
    ) -> Dict[str, Any]:
        """
        Get daily stock price data
        
        Args:
            symbol: Stock symbol (e.g., 'VNM', 'FPT')
            from_date: Start date in format 'DD/MM/YYYY'
            to_date: End date in format 'DD/MM/YYYY'
            page_index: Page number for pagination
            page_size: Number of items per page
            market: Market code (e.g., 'hose', 'hnx', 'upcom')
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            params = {
                "symbol": symbol,
                "fromDate": from_date,
                "toDate": to_date,
                "pageIndex": page_index,
                "pageSize": page_size,
                "market": market
            }
            response = self._make_get_request(SSIEndpoints.DAILY_STOCK_PRICE, params)
            return {"success": True, "data": response}
        except Exception as e:
            logger.error(f"Error getting daily stock price: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_daily_price(self, symbol: str, date_str: str) -> Dict[str, Any]:
        """
        Get the daily OHLC price for a symbol with price change from previous day
        
        Args:
            symbol: Stock symbol
            date_str: Date in DD/MM/YYYY format
        
        Returns:
            Dict with: current_price, price_change, price_change_percent
        """
        try:
            from datetime import datetime, timedelta, time
            
            # Get last 7 days to ensure we have at least 2 trading days
            today = datetime.strptime(date_str, "%d/%m/%Y")
            from_date = today - timedelta(days=7)
            from_date_str = from_date.strftime("%d/%m/%Y")
            
            params = {
                "symbol": symbol,
                "fromDate": from_date_str,
                "toDate": date_str,
                "pageIndex": 1,
                "pageSize": 10,
                "ascending": "false"  # Latest first
            }
            
            response = self._make_get_request(SSIEndpoints.DAILY_OHLC, params)
            
            if response.get("status") == "Success":
                data_list = response.get("data", [])
                
                if data_list and len(data_list) > 0:
                    # Latest day (today or most recent trading day)
                    latest = data_list[0]
                    current_price = self._parse_number(latest.get("Close") or latest.get("close"))
                    
                    # Calculate change from previous day's close
                    price_change = None
                    price_change_percent = None
                    
                    if len(data_list) >= 2 and current_price:
                        # Previous trading day
                        previous = data_list[1]
                        prev_close = self._parse_number(previous.get("Close") or previous.get("close"))
                        
                        if prev_close and prev_close > 0:
                            # Formula: (Current Price - Previous Close) / Previous Close × 100
                            price_change = round(current_price - prev_close, 2)
                            price_change_percent = round((price_change / prev_close) * 100, 2)
                    
                    return {
                        "current_price": current_price,
                        "price_change": price_change,
                        "price_change_percent": price_change_percent
                    }
            
            return {}
        except Exception as e:
            logger.warning(f"Error getting daily price for {symbol}: {str(e)}")
            return {}
    
    def _parse_number(self, value) -> Optional[float]:
        """Parse a number from string or return None"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                normalized = value.strip().replace("%", "").replace(" ", "")
                if not normalized:
                    return None
                # Handle common locale formats: 1,234.56 or 1,23
                if "," in normalized and "." in normalized:
                    normalized = normalized.replace(",", "")
                elif "," in normalized:
                    normalized = normalized.replace(",", ".")
                value = normalized
            return float(value)
        except (ValueError, TypeError):
            return None

    def _extract_price_change_fields(self, security: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """Extract current/change fields from SSI security payload using common key variants."""
        current_price_keys = ["MatchedPrice", "CurrentPrice", "Close", "Last", "Price"]
        change_keys = ["Change", "PriceChange", "Delta"]
        change_percent_keys = [
            "RatioChange",
            "ChangePc",
            "PriceChangePercent",
            "PercentChange",
            "PctChange",
            "ChangePercent",
        ]

        def _first_number(keys: list[str]) -> Optional[float]:
            for key in keys:
                if key in security:
                    parsed = self._parse_number(security.get(key))
                    if parsed is not None:
                        return parsed
            return None

        return {
            "current_price": _first_number(current_price_keys),
            "price_change": _first_number(change_keys),
            "price_change_percent": _first_number(change_percent_keys),
        }

    def _get_prices_from_market_snapshots(self, symbols: list[str]) -> Dict[str, Dict[str, Optional[float]]]:
        """Fetch symbol price snapshots from SSI SECURITIES endpoint by market."""
        target_symbols = {s.upper() for s in symbols if s}
        if not target_symbols:
            return {}

        snapshot_prices: Dict[str, Dict[str, Optional[float]]] = {}

        for market in ["HOSE", "HNX", "UPCOM"]:
            params = {
                "market": market,
                "pageIndex": 1,
                "pageSize": 1000,
            }
            response = self._make_get_request(SSIEndpoints.SECURITIES, params)
            if response.get("status") != "Success":
                continue

            for sec in response.get("data", []) or []:
                symbol = str(sec.get("Symbol") or "").upper().strip()
                if not symbol or symbol not in target_symbols:
                    continue

                parsed = self._extract_price_change_fields(sec)
                if parsed.get("current_price") is None and parsed.get("price_change_percent") is None:
                    continue

                snapshot_prices[symbol] = parsed

        return snapshot_prices
    
    def _fetch_prices_parallel(self, securities: list, date_str: str, max_workers: int = 10) -> None:
        """
        Fetch prices for multiple securities in parallel
        
        Args:
            securities: List of security dicts to update with price data
            date_str: Date string in DD/MM/YYYY format
            max_workers: Maximum number of parallel requests (default: 10)
        """
        def fetch_single_price(security):
            """Helper function to fetch price for a single security"""
            try:
                price_data = self._get_daily_price(security["symbol"], date_str)
                return security["symbol"], price_data
            except Exception as e:
                logger.warning(f"Error fetching price for {security['symbol']}: {str(e)}")
                return security["symbol"], {}
        
        # Create a mapping of symbol to security for quick lookup
        symbol_to_security = {sec["symbol"]: sec for sec in securities}
        
        # Fetch all prices in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(fetch_single_price, sec): sec["symbol"] 
                for sec in securities
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                try:
                    symbol, price_data = future.result()
                    security = symbol_to_security[symbol]
                    security.update({
                        "current_price": price_data.get("current_price"),
                        "price_change": price_data.get("price_change"),
                        "price_change_percent": price_data.get("price_change_percent")
                    })
                except Exception as e:
                    symbol = future_to_symbol[future]
                    logger.error(f"Failed to process price for {symbol}: {str(e)}")

    def _get_daily_price_with_retry(self, symbol: str, date_str: str, retries: int = 3, throttle_seconds: float = 1.05) -> Dict[str, Any]:
        """Get daily price with simple retry/backoff to handle SSI rate limits."""
        for attempt in range(retries):
            price_data = self._get_daily_price(symbol, date_str)
            if price_data and price_data.get("current_price") is not None:
                return price_data

            if attempt < retries - 1:
                time.sleep(throttle_seconds)

        return price_data if "price_data" in locals() else {}

    def _get_cached_daily_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return cached daily price when still fresh."""
        from datetime import datetime

        cached = self._daily_price_cache.get(symbol.upper())
        if not cached:
            return None

        cached_at = cached.get("cached_at")
        if not cached_at:
            return None

        age = (datetime.now() - cached_at).total_seconds()
        if age > self._daily_price_cache_ttl_seconds:
            return None

        return cached.get("data")

    def _set_cached_daily_price(self, symbol: str, price_data: Dict[str, Any]) -> None:
        """Store daily price in short-lived cache."""
        from datetime import datetime

        self._daily_price_cache[symbol.upper()] = {
            "cached_at": datetime.now(),
            "data": price_data,
        }

    def _refresh_missing_top_stock_prices_async(self, symbols: list[str], date_str: str) -> None:
        """Refresh missing symbol prices in background so later requests can return complete data."""
        symbols = [s.upper() for s in symbols if s]
        if not symbols:
            return

        with self._top_stocks_refresh_lock:
            if self._top_stocks_refresh_running:
                return
            self._top_stocks_refresh_running = True

        def _worker():
            try:
                for i, symbol in enumerate(symbols):
                    if self._get_cached_daily_price(symbol) is not None:
                        continue

                    price_data = self._get_daily_price_with_retry(symbol, date_str, retries=2, throttle_seconds=1.05)
                    if price_data and price_data.get("current_price") is not None:
                        self._set_cached_daily_price(symbol, price_data)

                    if i < len(symbols) - 1:
                        time.sleep(1.05)
            finally:
                with self._top_stocks_refresh_lock:
                    self._top_stocks_refresh_running = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def search_securities(
        self,
        query: str = "",
        market: str = "",
        page_index: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Search for securities with current prices (uses parallel fetching for speed)
        
        Args:
            query: Search query (symbol only)
            market: Filter by market (HOSE, HNX, UPCOM) - empty for all markets
            page_index: Page number for pagination
            page_size: Number of items per page
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            from datetime import datetime
            today_str = datetime.now().strftime("%d/%m/%Y")
            
            # Determine which markets to search
            markets_to_search = []
            if market and market.strip():
                markets_to_search = [market.upper()]
            else:
                markets_to_search = ["HOSE", "HNX", "UPCOM"]
            
            all_securities = []
            
            for mkt in markets_to_search:
                # Get securities list for the market
                params = {
                    "market": mkt,
                    "pageIndex": 1,
                    "pageSize": 1000
                }
                response = self._make_get_request(SSIEndpoints.SECURITIES, params)
                
                if response.get("status") == "Success" and response.get("data"):
                    securities = response.get("data", [])
                    
                    for sec in securities:
                        symbol = sec.get("Symbol") or ""
                        name = sec.get("StockName") or ""
                        
                        if not symbol:
                            continue
                        
                        # Filter out covered warrants (CQ securities), ETFs (QUY securities), and Chứng quyền
                        if "CQ " in name or name.startswith("CQ") or name.startswith("QUY") or "Chứng quyền" in name:
                            continue
                        
                        # Filter by search query - symbol only (case-insensitive)
                        if query and query.strip():
                            query_lower = query.lower().strip()
                            symbol_lower = symbol.lower() if symbol else ""
                            if query_lower not in symbol_lower:
                                continue
                        
                        all_securities.append({
                            "symbol": symbol,
                            "name": name,
                            "market": mkt,
                        })
            
            # Sort by symbol
            all_securities.sort(key=lambda x: x["symbol"])
            
            # Apply pagination first
            total = len(all_securities)
            start_idx = (page_index - 1) * page_size
            end_idx = start_idx + page_size
            paginated_securities = all_securities[start_idx:end_idx]
            
            # Fetch prices in parallel for better performance
            self._fetch_prices_parallel(paginated_securities, today_str)
            
            return {
                "success": True,
                "data": paginated_securities,
                "total": total,
                "page_index": page_index,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Error searching securities: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for a single stock using daily OHLC data,
        including calculated ceiling, floor, and reference prices.
        
        Ceiling = RefPrice * (1 + band), Floor = RefPrice * (1 - band)
        Band: HOSE 7%, HNX 10%, UPCOM 15%
        RefPrice: previous trading day's close (HOSE/HNX) or average price (UPCOM)
        
        Args:
            symbol: Stock symbol (e.g., VNM, FPT)
        
        Returns:
            Price data including current_price, price_change, ceiling_price, floor_price, reference_price
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            from datetime import datetime, timedelta
            import math
            today_str = datetime.now().strftime("%d/%m/%Y")
            symbol_upper = symbol.upper()
            
            # 1. Get last 7 days of OHLC to have at least 2 trading days
            today = datetime.now()
            from_date = today - timedelta(days=7)
            from_date_str = from_date.strftime("%d/%m/%Y")
            
            params = {
                "symbol": symbol_upper,
                "fromDate": from_date_str,
                "toDate": today_str,
                "pageIndex": 1,
                "pageSize": 10,
                "ascending": "false"  # Latest first
            }
            
            response = self._make_get_request(SSIEndpoints.DAILY_OHLC, params)
            
            current_price = None
            price_change = None
            price_change_percent = None
            reference_price = None
            ceiling_price = None
            floor_price = None
            
            if response.get("status") == "Success":
                data_list = response.get("data", [])
                
                if data_list and len(data_list) > 0:
                    latest = data_list[0]
                    current_price = self._parse_number(latest.get("Close") or latest.get("close"))
                    
                    if len(data_list) >= 2 and current_price:
                        previous = data_list[1]
                        prev_close = self._parse_number(previous.get("Close") or previous.get("close"))
                        
                        if prev_close and prev_close > 0:
                            price_change = round(current_price - prev_close, 2)
                            price_change_percent = round((price_change / prev_close) * 100, 2)
                            reference_price = prev_close
            
            # 2. Detect market for the symbol to determine fluctuation band
            if reference_price:
                market = self._detect_market(symbol_upper)
                band = {"HOSE": 0.07, "HNX": 0.10, "UPCOM": 0.15}.get(market, 0.07)
                
                # Ceiling and floor prices, rounded down to nearest 100 (standard VN stock pricing)
                raw_ceiling = reference_price * (1 + band)
                raw_floor = reference_price * (1 - band)
                ceiling_price = math.floor(raw_ceiling / 100) * 100
                floor_price = math.floor(raw_floor / 100) * 100
            
            return {
                "success": True,
                "data": {
                    "symbol": symbol_upper,
                    "current_price": current_price,
                    "price_change": price_change,
                    "price_change_percent": price_change_percent,
                    "reference_price": reference_price,
                    "ceiling_price": ceiling_price,
                    "floor_price": floor_price,
                }
            }
        except Exception as e:
            logger.error(f"Error getting stock price for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

    def _detect_market(self, symbol: str) -> str:
        """
        Detect which market a stock belongs to (HOSE, HNX, UPCOM).
        Searches each market's securities list for the symbol.
        
        Args:
            symbol: Stock symbol (uppercase)
        
        Returns:
            Market string: 'HOSE', 'HNX', or 'UPCOM'. Defaults to 'HOSE' if not found.
        """
        try:
            for market in ["HOSE", "HNX", "UPCOM"]:
                params = {
                    "market": market,
                    "symbol": symbol,
                    "pageIndex": 1,
                    "pageSize": 10
                }
                response = self._make_get_request(SSIEndpoints.SECURITIES_DETAILS, params)
                if response.get("status") == "Success" and response.get("data"):
                    data = response["data"]
                    if isinstance(data, list) and len(data) > 0:
                        return market
            return "HOSE"  # Default fallback
        except Exception as e:
            logger.warning(f"Error detecting market for {symbol}: {str(e)}")
            return "HOSE"

    def _round_time_to_interval(self, time_str: str, interval_minutes: int) -> str:
        """
        Round time to nearest interval within market sessions.
        Sessions:
        - Morning: [09:15, 11:30)
        - Afternoon: [13:00, 14:45]
        
        Args:
            time_str: Time string in format HH:MM:SS
            interval_minutes: Interval in minutes (15, 120, etc.)
        
        Returns:
            Rounded time string in format HH:MM:00.
            Returns empty string if input falls in lunch break.
        """
        try:
            from datetime import datetime
            time_obj = datetime.strptime(time_str, "%H:%M:%S")

            MORNING_OPEN = 9 * 60 + 15
            MORNING_BREAK = 11 * 60 + 30
            AFTERNOON_OPEN = 13 * 60
            MARKET_CLOSE = 14 * 60 + 45

            current_minutes = time_obj.hour * 60 + time_obj.minute

            # Clamp outside market hours.
            if current_minutes < MORNING_OPEN:
                current_minutes = MORNING_OPEN
            if current_minutes > MARKET_CLOSE:
                current_minutes = MARKET_CLOSE

            # Skip lunch-break values to avoid synthetic break-time buckets.
            if MORNING_BREAK <= current_minutes < AFTERNOON_OPEN:
                return ""

            # Round down within each session separately.
            anchor = MORNING_OPEN if current_minutes < MORNING_BREAK else AFTERNOON_OPEN
            elapsed = current_minutes - anchor
            rounded_elapsed = (elapsed // interval_minutes) * interval_minutes
            rounded_minutes = anchor + rounded_elapsed

            # Cap morning session before lunch; cap afternoon at market close.
            if anchor == MORNING_OPEN and rounded_minutes >= MORNING_BREAK:
                rounded_minutes = MORNING_BREAK - interval_minutes
            if rounded_minutes > MARKET_CLOSE:
                rounded_minutes = MARKET_CLOSE

            hours = rounded_minutes // 60
            mins = rounded_minutes % 60

            return f"{hours:02d}:{mins:02d}:00"
        except:
            return time_str
    
    def _aggregate_intraday_data(self, data_list: list, interval_minutes: int) -> list:
        """
        Aggregate intraday data by time intervals (e.g., group by 5-minute buckets)
        
        For each time bucket (9:00, 9:05, 9:10...):
        - Take the first Open of the bucket
        - Take the highest High of the bucket
        - Take the lowest Low of the bucket
        - Take the last Close of the bucket
        - Sum the Volume of the bucket
        
        Args:
            data_list: List of intraday OHLC data points
            interval_minutes: Interval in minutes (5, 60, etc.)
        
        Returns:
            Aggregated data list with rounded time intervals
        """
        if not data_list:
            return []
        
        from collections import defaultdict
        
        # Group data by rounded time
        time_buckets = defaultdict(list)
        
        for item in data_list:
            if "Time" in item and "TradingDate" in item:
                rounded_time = self._round_time_to_interval(item["Time"], interval_minutes)
                if not rounded_time:
                    continue
                bucket_key = f"{item['TradingDate']}_{rounded_time}"
                time_buckets[bucket_key].append(item)
        
        # Aggregate each bucket (sort by YYYY/MM/DD_HH:MM:SS for correct chronological order)
        def _sort_bucket_key(key):
            trading_date, time_part = key.split("_")
            day, month, year = trading_date.split("/")
            return f"{year}/{month}/{day}_{time_part}"
        
        aggregated = []
        for bucket_key in sorted(time_buckets.keys(), key=_sort_bucket_key):
            bucket_items = time_buckets[bucket_key]
            # Ensure OHLC uses true chronological order inside each bucket.
            bucket_items = sorted(bucket_items, key=lambda x: x.get("Time", "00:00:00"))
            
            if not bucket_items:
                continue
            
            # Extract date and time from bucket key
            trading_date, rounded_time = bucket_key.split("_")
            
            # Aggregate OHLC
            first_item = bucket_items[0]
            last_item = bucket_items[-1]
            
            aggregated_item = {
                "Symbol": first_item.get("Symbol", ""),
                "TradingDate": trading_date,
                "Time": rounded_time,
                "Open": first_item.get("Open", "0"),  # First open
                "High": max([float(item.get("High", 0)) for item in bucket_items]),  # Highest high
                "Low": min([float(item.get("Low", 999999)) for item in bucket_items if float(item.get("Low", 999999)) > 0]),  # Lowest low
                "Close": last_item.get("Close", "0"),  # Last close
                "Volume": sum([float(item.get("Volume", 0)) for item in bucket_items]),  # Total volume
                # "Value": last_item.get("Value", "0")  # Last value
            }
            
            # Convert back to strings for consistency
            aggregated_item["High"] = str(int(aggregated_item["High"]))
            aggregated_item["Low"] = str(int(aggregated_item["Low"]))
            aggregated_item["Volume"] = str(int(aggregated_item["Volume"]))
            
            aggregated.append(aggregated_item)
        
        return aggregated

    def _aggregate_daily_data(self, data_list: list, mode: str = "week") -> list:
        """
        Aggregate daily OHLC data into weekly or monthly buckets.
        
        For each bucket:
        - Open: first day's Open
        - High: highest High across all days
        - Low: lowest Low across all days  
        - Close: last day's Close
        - Volume: sum of all days' Volume
        - TradingDate: last day's TradingDate (the closing date of that period)
        
        Args:
            data_list: List of daily OHLC data points (must be in ascending order)
            mode: 'week' for weekly aggregation, 'month' for monthly aggregation
        
        Returns:
            Aggregated data list
        """
        if not data_list:
            return []
        
        from datetime import datetime
        from collections import OrderedDict
        
        buckets = OrderedDict()
        
        for item in data_list:
            trading_date_str = item.get("TradingDate", "")
            try:
                dt = datetime.strptime(trading_date_str, "%d/%m/%Y")
            except ValueError:
                continue
            
            if mode == "week":
                # ISO year-week as bucket key
                iso_year, iso_week, _ = dt.isocalendar()
                bucket_key = f"{iso_year}-W{iso_week:02d}"
            else:
                # Year-month as bucket key
                bucket_key = f"{dt.year}-{dt.month:02d}"
            
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(item)
        
        aggregated = []
        for bucket_key, bucket_items in buckets.items():
            if not bucket_items:
                continue
            
            first_item = bucket_items[0]
            last_item = bucket_items[-1]
            
            aggregated_item = {
                "Symbol": first_item.get("Symbol", ""),
                "Market": first_item.get("Market", ""),
                "TradingDate": last_item.get("TradingDate", ""),
                "Time": "14:45:00",
                "Open": first_item.get("Open", "0"),
                "High": max([float(item.get("High", 0)) for item in bucket_items]),
                "Low": min([float(item.get("Low", 999999)) for item in bucket_items if float(item.get("Low", 999999)) > 0]),
                "Close": last_item.get("Close", "0"),
                "Volume": sum([float(item.get("Volume", 0)) for item in bucket_items]),
            }
            
            aggregated_item["High"] = str(int(aggregated_item["High"]))
            aggregated_item["Low"] = str(int(aggregated_item["Low"]))
            aggregated_item["Volume"] = str(int(aggregated_item["Volume"]))
            
            aggregated.append(aggregated_item)
        
        return aggregated

    def _sync_15m_data_up_to_now(self, symbol: str) -> None:
        '''Syncs missing 15m price data from SSI to DB from the last known time up to now.'''
        from datetime import datetime, timedelta
        latest_time = PriceDBService.get_latest_trading_time(symbol)
        now_date = datetime.now()
        
        if not latest_time:
            sync_start = now_date - timedelta(days=30)
        else:
            sync_start = latest_time - timedelta(days=1)
            
        today_close_str = now_date.strftime("%Y-%m-%d 14:45:00")
        try:
            is_fully_updated = latest_time and latest_time >= datetime.strptime(today_close_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            is_fully_updated = False
            
        if not is_fully_updated:
            page_index = 1
            all_sync_data = []
            
            # Make sure we don't exceed SSI's 30-day limit for intraday calls
            current_sync_start = sync_start
            while current_sync_start <= now_date:
                current_sync_end = min(current_sync_start + timedelta(days=20), now_date)
                
                chunk_start_str = current_sync_start.strftime("%d/%m/%Y")
                chunk_end_str = current_sync_end.strftime("%d/%m/%Y")
                
                chunk_page_index = 1
                while True:
                    response = self.get_intraday_ohlc(
                        symbol=symbol,
                        from_date=chunk_start_str,
                        to_date=chunk_end_str,
                        page_index=chunk_page_index,
                        page_size=1000,
                        ascending=True,
                        resolution=1
                    )
                    if not response.get("success"):
                        break
                    data = response.get("data", {}).get("data", [])
                    if not data:
                        break
                    all_sync_data.extend(data)
                    
                    if len(data) < 1000 or len(data) == 0:
                        break
                    chunk_page_index += 1
                
                current_sync_start = current_sync_end + timedelta(days=1)
                
            aggregated_sync_data = self._aggregate_intraday_data(all_sync_data, 15) if all_sync_data else []
                
            # Insert to DB
            records = []
            for item in aggregated_sync_data:
                t_date = item.get("TradingDate")
                t_time = item.get("Time")
                if not t_date or not t_time:
                    continue
                dt_str = f"{t_date} {t_time}"
                try:
                    dt_obj = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    continue
                if latest_time and dt_obj <= latest_time:
                    continue
                    
                records.append({
                    "symbol": symbol,
                    "trading_time": dt_obj.isoformat(),
                    "open": float(item.get("Open", 0)),
                    "high": float(item.get("High", 0)),
                    "low": float(item.get("Low", 0)),
                    "close": float(item.get("Close", 0)),
                    "volume": float(item.get("Volume", 0))
                })
            
            if records:
                PriceDBService.insert_prices(records)

    def _format_db_to_ssi(self, db_prices: list) -> list:
        from datetime import datetime
        formatted = []
        for r in db_prices:
            t_str = r["trading_time"].split('+')[0].replace('Z', '')
            try:
                t_dt = datetime.fromisoformat(t_str)
            except ValueError:
                t_dt = datetime.strptime(t_str[:19], "%Y-%m-%dT%H:%M:%S")
                
            formatted.append({
                "TradingDate": t_dt.strftime("%d/%m/%Y"),
                "Time": t_dt.strftime("%H:%M:%S"),
                "Open": str(r["open"]),
                "High": str(r["high"]),
                "Low": str(r["low"]),
                "Close": str(r["close"]),
                "Volume": str(r["volume"])
            })
        return formatted

    def _get_and_sync_15m_data(self, symbol: str, from_date_str: str, to_date_str: str) -> list:
        from datetime import datetime, timedelta
        symbol = symbol.upper()
        self._sync_15m_data_up_to_now(symbol)
        
        start_obj = datetime.strptime(from_date_str, "%d/%m/%Y")
        end_obj = datetime.strptime(to_date_str, "%d/%m/%Y") + timedelta(days=1, seconds=-1)
        db_prices = PriceDBService.get_prices(symbol, start_obj, end_obj)
        return self._format_db_to_ssi(db_prices)

    def _ssi_item_to_db_record(self, symbol: str, item: Dict[str, Any], default_time: str = "14:45:00") -> Optional[Dict[str, Any]]:
        """Convert SSI candle format into DB row format."""
        from datetime import datetime

        trading_date = item.get("TradingDate")
        if not trading_date:
            return None

        trading_time = item.get("Time") or default_time
        try:
            dt_obj = datetime.strptime(f"{trading_date} {trading_time}", "%d/%m/%Y %H:%M:%S")
        except ValueError:
            return None

        return {
            "symbol": symbol.upper(),
            "trading_time": dt_obj.isoformat(),
            "open": float(self._parse_number(item.get("Open") or item.get("open")) or 0),
            "high": float(self._parse_number(item.get("High") or item.get("high")) or 0),
            "low": float(self._parse_number(item.get("Low") or item.get("low")) or 0),
            "close": float(self._parse_number(item.get("Close") or item.get("close")) or 0),
            "volume": float(self._parse_number(item.get("Volume") or item.get("volume")) or 0),
        }

    def _upsert_latest_records(self, symbol: str, interval: str, items: list, limit: int = 1000) -> int:
        """Upsert rows into interval table, then trim older rows beyond latest N."""
        records = []
        for item in items:
            record = self._ssi_item_to_db_record(symbol, item)
            if record:
                records.append(record)

        if not records:
            return 0

        PriceDBService.insert_prices(records, interval=interval)
        PriceDBService.prune_to_latest(symbol, limit=limit, interval=interval)
        return len(records)

    def _fetch_intraday_chunk(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        resolution: int = 1,
        page_size: int = 1000,
    ) -> list:
        """Fetch one date chunk with pagination and return all rows."""
        chunk_data = []
        page_index = 1
        chunk_count = 0

        while True:
            response = None
            for attempt in range(2):
                response = self.get_intraday_ohlc(
                    symbol=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    page_index=page_index,
                    page_size=page_size,
                    ascending=True,
                    resolution=resolution,
                )
                if response.get("success"):
                    break
                # Refresh token once and retry current page.
                if attempt == 0:
                    self._get_access_token()

            if not response.get("success"):
                logger.warning(
                    f"Failed intraday chunk fetch for {symbol} ({from_date}-{to_date}): "
                    f"{response.get('error')}"
                )
                break

            payload = response.get("data", {})
            page_data = payload.get("data", [])
            if not page_data:
                break

            chunk_data.extend(page_data)
            chunk_count += len(page_data)

            total_record = payload.get("totalRecord", 0)
            if len(page_data) < page_size or (total_record and chunk_count >= total_record):
                break
            page_index += 1

        return chunk_data

    def _fetch_intraday_data_in_chunks(
        self,
        symbol: str,
        from_obj,
        to_obj,
        resolution: int = 1,
        page_size: int = 1000,
        chunk_days: int = 10,
        parallel: bool = False,
        max_workers: int = 4,
    ) -> list:
        """Fetch SSI intraday data in <=20-day chunks to avoid SSI date-range failures."""
        from datetime import datetime, timedelta

        all_data = []
        chunks = []
        current_start = from_obj

        while current_start <= to_obj:
            current_end = min(current_start + timedelta(days=chunk_days), to_obj)
            from_date = current_start.strftime("%d/%m/%Y")
            to_date = current_end.strftime("%d/%m/%Y")
            chunks.append((from_date, to_date))
            current_start = current_end + timedelta(days=1)

        if parallel and len(chunks) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_chunk = {
                    executor.submit(
                        self._fetch_intraday_chunk,
                        symbol,
                        from_date,
                        to_date,
                        resolution,
                        page_size,
                    ): (from_date, to_date)
                    for from_date, to_date in chunks
                }
                for future in as_completed(future_to_chunk):
                    try:
                        chunk_rows = future.result()
                        if chunk_rows:
                            all_data.extend(chunk_rows)
                    except Exception as e:
                        chunk_from, chunk_to = future_to_chunk[future]
                        logger.warning(
                            f"Parallel chunk fetch failed for {symbol} ({chunk_from}-{chunk_to}): {str(e)}"
                        )
        else:
            for from_date, to_date in chunks:
                chunk_rows = self._fetch_intraday_chunk(
                    symbol=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    resolution=resolution,
                    page_size=page_size,
                )
                if chunk_rows:
                    all_data.extend(chunk_rows)

        # Normalize order after parallel fetch.
        def _item_sort_key(item):
            try:
                return datetime.strptime(
                    f"{item.get('TradingDate', '')} {item.get('Time', '00:00:00')}",
                    "%d/%m/%Y %H:%M:%S",
                )
            except Exception:
                return datetime.min

        all_data.sort(key=_item_sort_key)

        return all_data

    def _fetch_daily_chunk(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        page_size: int = 1000,
    ) -> list:
        """Fetch one daily chunk with pagination and return all rows."""
        chunk_data = []
        page_index = 1

        while True:
            response = self.get_daily_ohlc(
                symbol=symbol.lower(),
                from_date=from_date,
                to_date=to_date,
                page_index=page_index,
                page_size=page_size,
                ascending=True,
            )

            if not response.get("success"):
                logger.warning(
                    f"Failed daily chunk fetch for {symbol} ({from_date}-{to_date}): "
                    f"{response.get('error')}"
                )
                break

            payload = response.get("data", {})
            page_data = payload.get("data", [])
            if not page_data:
                break

            chunk_data.extend(page_data)
            total_record = payload.get("totalRecord", 0)
            if len(page_data) < page_size or (total_record and len(chunk_data) >= total_record):
                break
            page_index += 1

        return chunk_data

    def _fetch_daily_data_in_chunks(
        self,
        symbol: str,
        from_obj,
        to_obj,
        chunk_days: int = 365,
        page_size: int = 1000,
        parallel: bool = False,
        max_workers: int = 4,
    ) -> list:
        """Fetch daily OHLC in date chunks, optionally in parallel for cold start."""
        from datetime import datetime, timedelta

        all_data = []
        chunks = []
        current_start = from_obj

        while current_start <= to_obj:
            current_end = min(current_start + timedelta(days=chunk_days), to_obj)
            chunks.append((current_start.strftime("%d/%m/%Y"), current_end.strftime("%d/%m/%Y")))
            current_start = current_end + timedelta(days=1)

        if parallel and len(chunks) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_chunk = {
                    executor.submit(
                        self._fetch_daily_chunk,
                        symbol,
                        from_date,
                        to_date,
                        page_size,
                    ): (from_date, to_date)
                    for from_date, to_date in chunks
                }
                for future in as_completed(future_to_chunk):
                    try:
                        chunk_rows = future.result()
                        if chunk_rows:
                            all_data.extend(chunk_rows)
                    except Exception as e:
                        chunk_from, chunk_to = future_to_chunk[future]
                        logger.warning(
                            f"Parallel daily chunk fetch failed for {symbol} ({chunk_from}-{chunk_to}): {str(e)}"
                        )
        else:
            for from_date, to_date in chunks:
                chunk_rows = self._fetch_daily_chunk(
                    symbol=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    page_size=page_size,
                )
                if chunk_rows:
                    all_data.extend(chunk_rows)

        # Normalize order after parallel fetch.
        def _item_sort_key(item):
            try:
                time_part = item.get("Time") or "14:45:00"
                return datetime.strptime(
                    f"{item.get('TradingDate', '')} {time_part}",
                    "%d/%m/%Y %H:%M:%S",
                )
            except Exception:
                return datetime.min

        all_data.sort(key=_item_sort_key)
        return all_data

    def _sync_latest_interval_records(self, symbol: str, limit: int = 1000, interval: Optional[str] = None) -> None:
        """Fetch and store latest records for 15m, 1h, and 1d intervals."""
        from datetime import datetime, timedelta

        if not self._ensure_token():
            logger.warning(f"Skip syncing latest interval records for {symbol}: token unavailable")
            return

        symbol = symbol.upper()
        now = datetime.now()
        target_limit = max(1000, limit)
        sync_15m = interval in {None, "15m"}
        sync_1h = interval in {None, "1h"}
        sync_1d = interval in {None, "1d"}

        intraday_source_data = []

        if sync_15m:
            # 15m sync: resume from latest DB row with overlap, similar to backfill script.
            latest_15m = PriceDBService.get_latest_trading_time(symbol, interval="15m")
            existing_15m_count = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="15m"))
            cold_start_15m = existing_15m_count == 0
            if latest_15m and existing_15m_count >= target_limit:
                intraday_start_15m = latest_15m - timedelta(days=1)
            else:
                # Fetch enough recent data to fill up to 1000 x 15m candles.
                intraday_start_15m = now - timedelta(days=180)

            intraday_source_data = self._fetch_intraday_data_in_chunks(
                symbol=symbol,
                from_obj=intraday_start_15m,
                to_obj=now,
                resolution=1,
                page_size=1000,
                chunk_days=10,
                parallel=cold_start_15m,
                max_workers=4,
            )
            if not intraday_source_data:
                # Defensive retry: refresh token and retry a narrower recent window.
                self._get_access_token()
                intraday_source_data = self._fetch_intraday_data_in_chunks(
                    symbol=symbol,
                    from_obj=max(now - timedelta(days=45), intraday_start_15m),
                    to_obj=now,
                    resolution=1,
                    page_size=1000,
                    chunk_days=7,
                    parallel=False,
                )

            if intraday_source_data:
                aggregated_15m = self._aggregate_intraday_data(intraday_source_data, 15)
                latest_15m_items = aggregated_15m[-target_limit:] if len(aggregated_15m) > target_limit else aggregated_15m
                self._upsert_latest_records(symbol, "15m", latest_15m_items, limit=target_limit)

            # Ensure we truly have 1000 records: backfill older windows until count reaches target.
            count_15m = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="15m"))
            backfill_round = 0
            while count_15m < target_limit and backfill_round < 8:
                oldest_15m = PriceDBService.get_oldest_trading_time(symbol, interval="15m")
                if not oldest_15m:
                    break

                backfill_end = oldest_15m - timedelta(minutes=1)
                backfill_start = backfill_end - timedelta(days=30)
                older_intraday_data = self._fetch_intraday_data_in_chunks(
                    symbol=symbol,
                    from_obj=backfill_start,
                    to_obj=backfill_end,
                    resolution=1,
                    page_size=1000,
                    chunk_days=10,
                )

                if not older_intraday_data:
                    break

                older_15m = self._aggregate_intraday_data(older_intraday_data, 15)
                if not older_15m:
                    break

                self._upsert_latest_records(symbol, "15m", older_15m, limit=target_limit)

                new_count_15m = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="15m"))
                if new_count_15m <= count_15m:
                    break

                count_15m = new_count_15m
                backfill_round += 1

            if count_15m < target_limit:
                logger.warning(f"15m records for {symbol} still below target: {count_15m}/{target_limit}")

        if sync_1h:
            # 1h sync: staged fetch (recent first), then backfill only if still below target.
            latest_1h = PriceDBService.get_latest_trading_time(symbol, interval="1h")
            existing_1h_count = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="1h"))

            if latest_1h and existing_1h_count >= target_limit and intraday_source_data:
                intraday_source_for_1h = intraday_source_data
            else:
                if latest_1h and existing_1h_count >= target_limit:
                    intraday_start_1h = latest_1h - timedelta(days=3)
                else:
                    # Cold start / underfilled: fetch recent window first (enough for most symbols).
                    intraday_start_1h = now - timedelta(days=320)

                intraday_source_for_1h = self._fetch_intraday_data_in_chunks(
                    symbol=symbol,
                    from_obj=intraday_start_1h,
                    to_obj=now,
                    resolution=1,
                    page_size=1000,
                    chunk_days=20,
                    parallel=False,
                    max_workers=2,
                )

            if intraday_source_for_1h:
                aggregated_1h = self._aggregate_intraday_data(intraday_source_for_1h, 60)
                latest_1h_items = aggregated_1h[-target_limit:] if len(aggregated_1h) > target_limit else aggregated_1h
                self._upsert_latest_records(symbol, "1h", latest_1h_items, limit=target_limit)

            # Ensure 1h table reaches the target count by fetching older windows when needed.
            count_1h = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="1h"))
            backfill_1h_round = 0
            while count_1h < target_limit and backfill_1h_round < 10:
                oldest_1h = PriceDBService.get_oldest_trading_time(symbol, interval="1h")
                if not oldest_1h:
                    break

                backfill_end_1h = oldest_1h - timedelta(minutes=1)
                backfill_start_1h = backfill_end_1h - timedelta(days=120)
                older_intraday_1h = self._fetch_intraday_data_in_chunks(
                    symbol=symbol,
                    from_obj=backfill_start_1h,
                    to_obj=backfill_end_1h,
                    resolution=1,
                    page_size=1000,
                    chunk_days=7,
                    parallel=False,
                    max_workers=2,
                )

                if not older_intraday_1h:
                    break

                older_1h = self._aggregate_intraday_data(older_intraday_1h, 60)
                if not older_1h:
                    break

                self._upsert_latest_records(symbol, "1h", older_1h, limit=target_limit)

                new_count_1h = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="1h"))
                if new_count_1h <= count_1h:
                    break

                count_1h = new_count_1h
                backfill_1h_round += 1

            if count_1h < target_limit:
                logger.warning(f"1h records for {symbol} still below target: {count_1h}/{target_limit}")

        if sync_1d:
            latest_1d = PriceDBService.get_latest_trading_time(symbol, interval="1d")

            # If we already have 1d data, fetch incrementally from the latest DB day to today.
            if latest_1d:
                incremental_from = latest_1d.strftime("%d/%m/%Y")
                incremental_daily = self._fetch_daily_data_in_chunks(
                    symbol=symbol,
                    from_obj=latest_1d,
                    to_obj=now,
                    chunk_days=90,
                    page_size=1000,
                    parallel=False,
                    max_workers=2,
                )
                if incremental_daily:
                    for item in incremental_daily:
                        item["Time"] = item.get("Time") or "14:45:00"
                        item.pop("Value", None)
                    self._upsert_latest_records(symbol, "1d", incremental_daily, limit=target_limit)
                else:
                    logger.info(f"No incremental 1d rows for {symbol} from {incremental_from} to today")
            else:
                # Cold start: fetch latest candles first to guarantee recency.
                latest_daily_response = self.get_daily_ohlc(
                    symbol=symbol.lower(),
                    from_date="01/01/2000",
                    to_date=now.strftime("%d/%m/%Y"),
                    page_index=1,
                    page_size=target_limit,
                    ascending=False,
                )
                if latest_daily_response.get("success") and latest_daily_response.get("data", {}).get("data"):
                    latest_daily_items = latest_daily_response["data"]["data"]
                    latest_daily_items.reverse()
                    for item in latest_daily_items:
                        item["Time"] = item.get("Time") or "14:45:00"
                        item.pop("Value", None)
                    self._upsert_latest_records(symbol, "1d", latest_daily_items, limit=target_limit)

            # Top-up older windows only when latest-first query still yields fewer than target rows.
            count_1d = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="1d"))
            backfill_1d_round = 0
            while count_1d < target_limit and backfill_1d_round < 4:
                oldest_1d = PriceDBService.get_oldest_trading_time(symbol, interval="1d")
                if not oldest_1d:
                    break

                backfill_end_1d = oldest_1d - timedelta(days=1)
                backfill_start_1d = backfill_end_1d - timedelta(days=730)
                older_daily_data = self._fetch_daily_data_in_chunks(
                    symbol=symbol,
                    from_obj=backfill_start_1d,
                    to_obj=backfill_end_1d,
                    chunk_days=365,
                    page_size=1000,
                    parallel=False,
                    max_workers=2,
                )

                if not older_daily_data:
                    break

                for item in older_daily_data:
                    item["Time"] = item.get("Time") or "14:45:00"
                    item.pop("Value", None)

                self._upsert_latest_records(symbol, "1d", older_daily_data, limit=target_limit)

                new_count_1d = len(PriceDBService.get_latest_prices(symbol, limit=target_limit, interval="1d"))
                if new_count_1d <= count_1d:
                    break

                count_1d = new_count_1d
                backfill_1d_round += 1

            if count_1d < target_limit:
                logger.warning(f"1d records for {symbol} still below target: {count_1d}/{target_limit}")

    def get_latest_historical_chart_data(self, symbol: str, interval: str = "15m", limit: int = 1000) -> Dict[str, Any]:
        '''
        Get strictly the latest N available records up to today for a specific timeframe interval (15m, 1h, 1d)
        '''
        try:
            symbol = symbol.upper()
            interval = interval.lower()

            if interval not in {"15m", "1h", "1d"}:
                return {"success": False, "error": f"Unsupported interval: {interval}"}

            # Keep this endpoint fixed to latest 1000 records.
            normalized_limit = 1000

            # Fetch once for fast-path check; reuse rows if already full and fresh.
            current_rows = PriceDBService.get_latest_prices(
                symbol=symbol,
                limit=normalized_limit,
                interval=interval,
            )

            formatted = self._format_db_to_ssi(current_rows)
            return {
                "success": True,
                "data": formatted,
            }
            
        except Exception as e:
            logger.error(f"Error getting latest historical data: {str(e)}")
            return {"success": False, "error": str(e)}

# Singleton instance
_ssi_service: Optional[SSIMarketDataService] = None

def get_ssi_service() -> SSIMarketDataService:
    """Get or create the SSI Market Data Service singleton"""
    global _ssi_service
    if _ssi_service is None:
        _ssi_service = SSIMarketDataService()
    return _ssi_service