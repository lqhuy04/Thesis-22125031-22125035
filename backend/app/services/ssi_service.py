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
import logging
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        self._config = get_ssi_config()
        self._access_token: Optional[str] = None
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @property
    def config(self):
        return self._config
    
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
        return response.json()
    
    def _ensure_token(self) -> bool:
        """Ensure we have a valid access token"""
        if not self._access_token:
            result = self.get_access_token()
            if result.get("success") and result.get("data", {}).get("data", {}).get("accessToken"):
                self._access_token = result["data"]["data"]["accessToken"]
                return True
            return False
        return True
    
    def get_access_token(self) -> Dict[str, Any]:
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
            return {"success": True, "data": response}
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
            from datetime import datetime, timedelta
            
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
            return float(value)
        except (ValueError, TypeError):
            return None
    
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

    def get_top_stocks(self, symbols: list = None) -> Dict[str, Any]:
        """
        Get price data for top/featured stocks (for home page display)
        
        Args:
            symbols: List of stock symbols. Default: ['VNM', 'FPT', 'VCB', 'VIC', 'VHM']
        
        Returns:
            List of stocks with current_price, price_change, price_change_percent
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            from datetime import datetime
            today_str = datetime.now().strftime("%d/%m/%Y")
            
            # Default popular Vietnamese stocks
            if not symbols:
                symbols = ['VNM', 'FPT', 'VCB', 'VIC', 'VHM']
            
            results = []
            for symbol in symbols:
                price_data = self._get_daily_price(symbol.upper(), today_str)
                results.append({
                    "symbol": symbol.upper(),
                    "current_price": price_data.get("current_price"),
                    "price_change": price_data.get("price_change"),
                    "price_change_percent": price_data.get("price_change_percent")
                })
            
            return {
                "success": True,
                "data": results
            }
        except Exception as e:
            logger.error(f"Error getting top stocks: {str(e)}")
            return {"success": False, "error": str(e)}

    def _round_time_to_interval(self, time_str: str, interval_minutes: int) -> str:
        """
        Round time to nearest interval aligned to market open (09:15).
        All times are clamped to trading hours [09:15, 14:45].
        
        Args:
            time_str: Time string in format HH:MM:SS
            interval_minutes: Interval in minutes (15, 120, etc.)
        
        Returns:
            Rounded time string in format HH:MM:00
        """
        try:
            from datetime import datetime
            time_obj = datetime.strptime(time_str, "%H:%M:%S")
            
            MARKET_OPEN = 9 * 60 + 15   # 09:15 = 555 minutes
            MARKET_CLOSE = 14 * 60 + 45  # 14:45 = 885 minutes
            
            current_minutes = time_obj.hour * 60 + time_obj.minute
            
            # Clamp to trading hours
            if current_minutes < MARKET_OPEN:
                current_minutes = MARKET_OPEN
            if current_minutes > MARKET_CLOSE:
                current_minutes = MARKET_CLOSE
            
            # Round down relative to market open
            elapsed = current_minutes - MARKET_OPEN
            rounded_elapsed = (elapsed // interval_minutes) * interval_minutes
            rounded_minutes = MARKET_OPEN + rounded_elapsed
            
            # Cap at market close
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

    def get_stock_prices_by_timeframe(
        self, 
        symbol: str, 
        timeframe: str,
        market: str = "hose"
    ) -> Dict[str, Any]:
        """
        Get stock prices based on timeframe with appropriate intervals
        
        Timeframe logic:
        - 1D (1 day): 15-minute intervals
        - 1W (1 week): 2-hour intervals
        - 1M (1 month): 12-hour intervals
        - 1Y (1 year): 1-week intervals (sampled from daily)
        - 5Y (5 years): 1-month intervals (sampled from daily)
        
        Args:
            symbol: Stock symbol (e.g., 'VNM', 'FPT')
            timeframe: Time frame ('1D', '1W', '1M', '1Y', '5Y')
            market: Market code (hose, hnx, upcom)
        
        Returns:
            Dict with success flag and data containing price points
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            from datetime import datetime, timedelta
            
            # Calculate date ranges
            today = datetime.now()
            
            timeframe_config = {
                "1D": {
                    "days": 0,
                    "use_intraday": True,
                    "resolution": 1,  # Get 1-min data to aggregate to 15-min
                    "aggregate_interval": 15,  # Aggregate to 15-minute intervals
                    "page_size": 500
                },
                "1W": {
                    "days": 7,
                    "use_intraday": True,
                    "resolution": 1,  # Get 1-min data to aggregate to 2-hour
                    "aggregate_interval": 120,  # Aggregate to 2-hour intervals
                    "page_size": 1000
                },
                "1M": {
                    "days": 30,
                    "use_intraday": False,
                    "page_size": 100,
                    "sample_interval": 1  # Every trading day
                },
                "1Y": {
                    "days": 365,
                    "use_intraday": False,
                    "page_size": 400,  # ~365 days
                    "sample_interval": 7  # Sample every 7 days (weekly)
                },
                "5Y": {
                    "days": 1825,  # 5 years
                    "use_intraday": False,
                    "page_size": 1000,
                    "sample_interval": 21  # ~21 trading days per month
                }
            }
            
            config = timeframe_config.get(timeframe)
            if not config:
                return {"success": False, "error": f"Invalid timeframe: {timeframe}"}
            
            # Calculate date range
            from_date_obj = today - timedelta(days=config["days"])
            from_date = from_date_obj.strftime("%d/%m/%Y")
            to_date = today.strftime("%d/%m/%Y")
            
            # Get data based on timeframe
            if config["use_intraday"]:
                # Use intraday OHLC for short timeframes
                result = self.get_intraday_ohlc(
                    symbol=symbol.lower(),
                    from_date=from_date,
                    to_date=to_date,
                    page_index=1,
                    page_size=config["page_size"],
                    ascending=True,
                    resolution=config["resolution"]
                )
            else:
                # Use daily OHLC for longer timeframes
                result = self.get_daily_ohlc(
                    symbol=symbol.lower(),
                    from_date=from_date,
                    to_date=to_date,
                    page_index=1,
                    page_size=config["page_size"],
                    ascending=True
                )
            
            if not result.get("success"):
                return result
            
            # Aggregate intraday data to clean intervals if needed
            if config["use_intraday"] and config.get("aggregate_interval"):
                if result.get("data", {}).get("data"):
                    data_list = result["data"]["data"]
                    aggregated_data = self._aggregate_intraday_data(
                        data_list, 
                        config["aggregate_interval"]
                    )
                    result["data"]["data"] = aggregated_data
                    result["data"]["totalRecord"] = len(aggregated_data)
            
            # Post-process daily data: sample at configured intervals, set Time=14:45, strip "Value"
            if not config["use_intraday"] and config.get("sample_interval") and result.get("data", {}).get("data"):
                data_list = result["data"]["data"]
                interval = config["sample_interval"]
                sampled_data = data_list[::interval] if len(data_list) > interval else data_list
                # Set Time to market close (14:45) and remove "Value" field
                for item in sampled_data:
                    item["Time"] = "14:45:00"
                    item.pop("Value", None)
                result["data"]["data"] = sampled_data
                result["data"]["totalRecord"] = len(sampled_data)
            
            # Add metadata about the timeframe
            interval_labels = {
                "1D": "15 minutes",
                "1W": "2 hours",
                "1M": "1 day",
                "1Y": "1 week",
                "5Y": "1 month",
            }
            if result.get("data"):
                result["data"]["timeframe"] = timeframe
                result["data"]["from_date"] = from_date
                result["data"]["to_date"] = to_date
                result["data"]["interval"] = interval_labels.get(timeframe, "unknown")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting stock prices by timeframe: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
_ssi_service: Optional[SSIMarketDataService] = None

def get_ssi_service() -> SSIMarketDataService:
    """Get or create the SSI Market Data Service singleton"""
    global _ssi_service
    if _ssi_service is None:
        _ssi_service = SSIMarketDataService()
    return _ssi_service


class SSIService:
    """Async wrapper for SSI Market Data Service"""
    
    @staticmethod
    async def get_historical_price(symbol: str, from_date: str, to_date: str, page_size: int = 100) -> Dict[str, Any]:
        """
        Get historical price data for a stock (async wrapper)
        
        Args:
            symbol: Stock symbol (e.g., 'VNM', 'FPT')
            from_date: Start date in format 'DD/MM/YYYY'
            to_date: End date in format 'DD/MM/YYYY'
            page_size: Number of records to return
            
        Returns:
            Dict with price data
        """
        service = get_ssi_service()
        result = service.get_daily_ohlc(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            page_size=page_size,
            ascending=False  # Latest first
        )
        
        if result.get("success"):
            response_data = result.get("data", {})
            if response_data.get("status") == "Success":
                return {"data": response_data.get("data", [])}
        
        return {"data": []}
