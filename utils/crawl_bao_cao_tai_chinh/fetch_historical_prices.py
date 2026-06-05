"""
Fetch Historical Stock Prices for Financial Metrics Calculation
Fetches end-of-year stock prices using local backend API
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
import time

class HistoricalPricesFetcher:
    """Fetch historical stock prices from local backend API"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
        print(f"[OK] Using backend API at {self.backend_url}")
    
    def get_year_end_price(self, symbol: str, year: int) -> Optional[float]:
        """
        Get stock price at end of year (last trading day of December)
        Args:
            symbol: Stock symbol (e.g., 'VNM')
            year: Year (e.g., 2023)
        Returns:
            Stock price in VND or None if not found
        """
        try:
            # Get last trading day of the year
            end_date = datetime(year, 12, 31)
            # Go back to find last trading day (skip weekends)
            while end_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                end_date -= timedelta(days=1)
            
            # Start from a week before to ensure we get data
            start_date = end_date - timedelta(days=10)
            
            # Format dates as DD/MM/YYYY
            from_date = start_date.strftime('%d/%m/%Y')
            to_date = end_date.strftime('%d/%m/%Y')
            
            # Call local backend API
            url = f"{self.backend_url}/market-data/ohlc/daily/{symbol}"
            params = {
                'from_date': from_date,
                'to_date': to_date,
                'page_index': 1,
                'page_size': 20,
                'ascending': False  # Get latest first
            }
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                result = response.json()
                
                # Navigate the response structure
                data_wrapper = result.get('data', {})
                data_list = data_wrapper.get('data', [])
                
                if data_list and len(data_list) > 0:
                    # Get the most recent close price
                    close_price = float(data_list[0].get('Close', 0))
                    if close_price > 0:
                        print(f"[OK] Found {symbol} {year} price: {close_price:,.0f} VND")
                        return close_price
            
            print(f"Could not find price for {symbol} in {year}")
            return None
            
        except Exception as e:
            print(f"Error fetching price for {symbol} {year}: {e}")
            return None
    
    def get_shares_outstanding(self, symbol: str, year: int) -> Optional[float]:
        """
        Get shares outstanding for a specific year (in millions)
        Args:
            symbol: Stock symbol
            year: Year
        Returns:
            Shares outstanding in millions or None
        """
        # Try different markets
        for market in ['HOSE', 'HNX', 'UPCOM']:
            try:
                # Try to get from backend securities details endpoint
                url = f"{self.backend_url}/market-data/securities/{symbol}"
                params = {
                    'market': market,
                    'page_index': 1,
                    'page_size': 10
                }
                
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    result = response.json()
                    data_wrapper = result.get('data', {})
                    data_list = data_wrapper.get('data', [])
                    
                    if data_list and len(data_list) > 0:
                        # Navigate to RepeatedInfo[0].ListedShare
                        repeated_info = data_list[0].get('RepeatedInfo', [])
                        if repeated_info and len(repeated_info) > 0:
                            listed_share = repeated_info[0].get('ListedShare')
                            if listed_share:
                                shares = float(listed_share) / 1_000_000
                                if shares > 0:
                                    print(f"[OK] Found {symbol} shares outstanding ({market}): {shares:.2f}M")
                                    return shares
            except Exception as e:
                continue
        
        print(f"Could not find shares outstanding for {symbol} {year}")
        return None
    
    def get_company_name(self, symbol: str) -> Optional[str]:
        """
        Get company name from securities details
        Args:
            symbol: Stock symbol
        Returns:
            Company name (Vietnamese) or None
        """
        # Try different markets
        for market in ['HOSE', 'HNX', 'UPCOM']:
            try:
                url = f"{self.backend_url}/market-data/securities/{symbol}"
                params = {
                    'market': market,
                    'page_index': 1,
                    'page_size': 10
                }
                
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    result = response.json()
                    data_wrapper = result.get('data', {})
                    data_list = data_wrapper.get('data', [])
                    
                    if data_list and len(data_list) > 0:
                        repeated_info = data_list[0].get('RepeatedInfo', [])
                        if repeated_info and len(repeated_info) > 0:
                            # Get Vietnamese name
                            company_name = repeated_info[0].get('SymbolName')
                            if company_name:
                                print(f"[OK] Found company name: {company_name}")
                                return company_name
            except Exception as e:
                continue
        
        return None
    
    def get_historical_prices_for_beta(self, symbol: str, year: int, 
                                       market_symbol: str = "VNINDEX") -> tuple:
        """
        Get daily prices for the year to calculate beta
        Args:
            symbol: Stock symbol
            year: Year
            market_symbol: Market index symbol
        Returns:
            Tuple of (stock_prices_df, market_prices_df)
        """
        # This would fetch daily prices for the entire year
        # For beta calculation, we need at least weekly or monthly data
        # Simplified version - return None for now
        print(f"Beta calculation requires full year daily/weekly data - not implemented yet")
        return None, None

def fetch_market_data_for_years(symbol: str, years: List[int]) -> Dict[int, Dict[str, float]]:
    """
    Fetch all required market data for multiple years
    Args:
        symbol: Stock symbol
        years: List of years to fetch data for
    Returns:
        Dictionary with year as key and data dict as value
    """
    fetcher = HistoricalPricesFetcher()
    market_data = {}
    
    # Get company name once (doesn't change by year)
    company_name = fetcher.get_company_name(symbol)
    
    for year in years:
        print(f"\nFetching market data for {symbol} - {year}...")
        year_data = {}
        
        # Add company name
        if company_name:
            year_data['company_name'] = company_name
        
        # Get end of year stock price
        price = fetcher.get_year_end_price(symbol, year)
        if price:
            year_data['stock_price'] = price
        
        # Get shares outstanding (same for all years, but fetching per year for consistency)
        shares = fetcher.get_shares_outstanding(symbol, year)
        if shares:
            year_data['shares_outstanding'] = shares
        
        # Add to result if we have some data
        if year_data:
            market_data[year] = year_data
        
        # Be nice to the APIs
        time.sleep(0.5)
    
    return market_data

if __name__ == "__main__":
    # Test fetching
    symbol = "VNM"
    years = [2023, 2024]
    
    print(f"Testing historical data fetch for {symbol}")
    data = fetch_market_data_for_years(symbol, years)
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    for year, year_data in data.items():
        print(f"\n{year}:")
        for key, value in year_data.items():
            if isinstance(value, str):
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value:,.2f}")
