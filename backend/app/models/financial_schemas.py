"""
Financial analysis schemas for fundamental analysis
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class FinancialRatiosSchema(BaseModel):
    """Schema for financial ratios and metrics"""
    
    # Valuation Metrics
    pe_ratio: Optional[float] = Field(None, description="Price-to-Earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price-to-Book ratio")
    eps: Optional[float] = Field(None, description="Earnings per Share (VND)")
    market_cap_billion: Optional[float] = Field(None, description="Market capitalization (Billion VND)")
    shares_outstanding_million: Optional[float] = Field(None, description="Shares outstanding (Million shares)")
    
    # Profitability Metrics
    roe: Optional[float] = Field(None, description="Return on Equity (%)")
    gross_margin: Optional[float] = Field(None, description="Gross profit margin (%)")
    net_margin: Optional[float] = Field(None, description="Net profit margin (%)")
    roa: Optional[float] = Field(None, description="Return on Assets (%)")
    
    # Growth Metrics
    revenue_yoy: Optional[float] = Field(None, description="Revenue growth year-over-year (%)")
    eps_yoy: Optional[float] = Field(None, description="EPS growth year-over-year (%)")
    profit_yoy: Optional[float] = Field(None, description="Profit growth year-over-year (%)")
    
    # Leverage Metrics
    debt_to_equity: Optional[float] = Field(None, description="Debt-to-Equity ratio")
    current_ratio: Optional[float] = Field(None, description="Current ratio")
    
    # Additional Metrics
    ev_ebitda: Optional[float] = Field(None, description="Enterprise Value to EBITDA")
    bvps: Optional[float] = Field(None, description="Book Value per Share (VND)")
    
    # Cash Flow (placeholder for future implementation)
    fcf: Optional[float] = Field(None, description="Free Cash Flow (Billion VND)")
    beta: Optional[float] = Field(None, description="Beta coefficient")


class FinancialAnalysisRequest(BaseModel):
    """Request for financial analysis"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., VNM, SSI)")
    year: Optional[str] = Field(None, description="Year for analysis (e.g., '2024'). If not provided, uses latest available year")


class FinancialAnalysisResponse(BaseModel):
    """Response for financial analysis"""
    symbol: str = Field(..., description="Stock symbol")
    company_name: Optional[str] = Field(None, description="Company name")
    analysis_date: datetime = Field(..., description="Date of analysis")
    year: str = Field(..., description="Year of financial data")
    metrics: FinancialRatiosSchema = Field(..., description="Financial metrics and ratios")
    data_source: str = Field("SSI iBoard", description="Source of financial data")


class MarketDataResponse(BaseModel):
    """Base response model for market data API"""
    data: Dict = Field({}, description="Response data")
    errorCode: int = Field(0, description="Error code (0 for success)")
    errorDesc: str = Field("", description="Error description")
    requestId: str = Field(..., description="Unique request ID")
    result: bool = Field(True, description="Request success status")