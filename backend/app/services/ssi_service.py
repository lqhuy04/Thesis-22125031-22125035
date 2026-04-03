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


# Singleton instance
_ssi_service: Optional[SSIMarketDataService] = None

def get_ssi_service() -> SSIMarketDataService:
    """Get or create the SSI Market Data Service singleton"""
    global _ssi_service
    if _ssi_service is None:
        _ssi_service = SSIMarketDataService()
    return _ssi_service