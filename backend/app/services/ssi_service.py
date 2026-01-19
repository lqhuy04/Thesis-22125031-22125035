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

    def search_securities(
        self,
        query: str = "",
        market: str = "",
        page_index: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Search securities by name/symbol and get current prices with 24h changes
        
        Args:
            query: Search query (symbol or company name)
            market: Filter by market (HOSE, HNX, UPCOM) - empty for all markets
            page_index: Page number for pagination
            page_size: Number of items per page
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            from datetime import datetime
            
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
                    "pageSize": 1000  # Get all securities for search
                }
                response = self._make_get_request(SSIEndpoints.SECURITIES, params)
                
                if response.get("status") == "Success" and response.get("data"):
                    securities = response.get("data", [])
                    
                    for sec in securities:
                        symbol = sec.get("Symbol") or ""
                        name = sec.get("StockName") or ""
                        
                        # Skip if no symbol
                        if not symbol:
                            continue
                        
                        # Filter by search query (case-insensitive)
                        if query and query.strip():
                            query_lower = query.lower().strip()
                            symbol_lower = symbol.lower() if symbol else ""
                            name_lower = name.lower() if name else ""
                            if query_lower not in symbol_lower and query_lower not in name_lower:
                                continue
                        
                        all_securities.append({
                            "symbol": symbol,
                            "name": name,
                            "market": mkt,
                        })
            
            # Sort by symbol
            all_securities.sort(key=lambda x: x["symbol"])
            
            # Apply pagination
            total = len(all_securities)
            start_idx = (page_index - 1) * page_size
            end_idx = start_idx + page_size
            paginated_securities = all_securities[start_idx:end_idx]
            
            # Build result with prices using daily OHLC data
            result_with_prices = []
            today_str = datetime.now().strftime("%d/%m/%Y")
            
            for sec in paginated_securities:
                symbol = sec["symbol"]
                
                # Get daily OHLC data for current price
                price_data = self._get_daily_price(symbol, today_str)
                
                result_with_prices.append({
                    "symbol": sec["symbol"],
                    "name": sec["name"],
                    "market": sec["market"],
                    "current_price": price_data.get("current_price"),
                    "price_change": price_data.get("price_change"),
                    "price_change_percent": price_data.get("price_change_percent")
                })
            
            return {
                "success": True,
                "data": result_with_prices,
                "total": total,
                "page_index": page_index,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Error searching securities: {str(e)}")
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

    def search_securities_fast(
        self,
        query: str = "",
        market: str = "",
        page_index: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Fast search for securities WITHOUT prices (instant response)
        Use get_stock_price() separately to load prices
        
        Args:
            query: Search query (symbol or company name)
            market: Filter by market (HOSE, HNX, UPCOM) - empty for all markets
            page_index: Page number for pagination
            page_size: Number of items per page
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
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
                        
                        # Filter by search query (case-insensitive)
                        if query and query.strip():
                            query_lower = query.lower().strip()
                            symbol_lower = symbol.lower() if symbol else ""
                            name_lower = name.lower() if name else ""
                            if query_lower not in symbol_lower and query_lower not in name_lower:
                                continue
                        
                        all_securities.append({
                            "symbol": symbol,
                            "name": name,
                            "market": mkt,
                        })
            
            # Sort by symbol
            all_securities.sort(key=lambda x: x["symbol"])
            
            # Apply pagination
            total = len(all_securities)
            start_idx = (page_index - 1) * page_size
            end_idx = start_idx + page_size
            paginated_securities = all_securities[start_idx:end_idx]
            
            return {
                "success": True,
                "data": paginated_securities,
                "total": total,
                "page_index": page_index,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"Error in fast search: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for a single stock using daily OHLC data
        
        Args:
            symbol: Stock symbol (e.g., VNM, FPT)
        
        Returns:
            Price data including current_price, price_change, price_change_percent, etc.
        """
        try:
            if not self._ensure_token():
                return {"success": False, "error": "Failed to get access token"}
            
            from datetime import datetime
            today_str = datetime.now().strftime("%d/%m/%Y")
            
            price_data = self._get_daily_price(symbol.upper(), today_str)
            
            return {
                "success": True,
                "data": {
                    "symbol": symbol.upper(),
                    "current_price": price_data.get("current_price"),
                    "price_change": price_data.get("price_change"),
                    "price_change_percent": price_data.get("price_change_percent")
                }
            }
        except Exception as e:
            logger.error(f"Error getting stock price for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

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


# Singleton instance
_ssi_service: Optional[SSIMarketDataService] = None

def get_ssi_service() -> SSIMarketDataService:
    """Get or create the SSI Market Data Service singleton"""
    global _ssi_service
    if _ssi_service is None:
        _ssi_service = SSIMarketDataService()
    return _ssi_service
