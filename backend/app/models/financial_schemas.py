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


class BalanceSheetSchema(BaseModel):
    """Schema for Financial Balance Sheets"""
    symbol: str = Field(..., description="Stock symbol")
    year: int = Field(..., description="Year")
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    short_term_investments_net: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory_net: Optional[float] = None
    long_term_assets: Optional[float] = None
    fixed_assets: Optional[float] = None
    long_term_investments: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    accounts_payable: Optional[float] = None
    short_term_loans: Optional[float] = None
    long_term_liabilities: Optional[float] = None
    long_term_loans: Optional[float] = None
    equity: Optional[float] = None
    paid_in_capital: Optional[float] = None
    retained_earnings: Optional[float] = None
    total_liabilities_and_equity: Optional[float] = None


class CashFlowSchema(BaseModel):
    """Schema for Financial Cash Flows"""
    symbol: str = Field(..., description="Stock symbol")
    year: int = Field(..., description="Year")
    cfo: Optional[float] = None
    profit_before_wc_changes: Optional[float] = None
    profit_before_tax_cf: Optional[float] = None
    depreciation: Optional[float] = None
    cfi: Optional[float] = None
    capex: Optional[float] = None
    dividends_received: Optional[float] = None
    cff: Optional[float] = None
    proceeds_from_share_issuance: Optional[float] = None
    proceeds_from_loans: Optional[float] = None
    repayment_of_loans: Optional[float] = None
    dividends_paid: Optional[float] = None
    net_cash_change: Optional[float] = None
    cash_beginning: Optional[float] = None
    cash_ending: Optional[float] = None


class FinancialIndicatorSchema(BaseModel):
    """Schema for Financial Indicators"""
    symbol: str = Field(..., description="Stock symbol")
    year: int = Field(..., description="Year")
    cash_cycle_days: Optional[float] = None
    net_income: Optional[float] = None
    profit_yoy: Optional[float] = None
    revenue: Optional[float] = None
    revenue_yoy: Optional[float] = None
    market_cap: Optional[float] = None
    eps: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    p_cash_flow: Optional[float] = None
    shares_outstanding: Optional[float] = None
    ev_ebitda: Optional[float] = None
    bvps: Optional[float] = None
    cash_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    days_receivable: Optional[float] = None
    days_inventory: Optional[float] = None
    quick_ratio: Optional[float] = None
    days_payable: Optional[float] = None
    gross_margin: Optional[float] = None
    ebit_margin: Optional[float] = None
    net_margin: Optional[float] = None
    current_ratio: Optional[float] = None
    asset_turnover: Optional[float] = None
    loans_to_equity: Optional[float] = None
    financial_leverage: Optional[float] = None
    roic: Optional[float] = None
    interest_coverage: Optional[float] = None
    fixed_asset_turnover: Optional[float] = None


class IncomeStatementSchema(BaseModel):
    """Schema for Financial Income Statements"""
    symbol: str = Field(..., description="Stock symbol")
    year: int = Field(..., description="Year")
    gross_revenue: Optional[float] = None
    net_revenue: Optional[float] = None
    cogs: Optional[float] = None
    gross_profit: Optional[float] = None
    financial_income: Optional[float] = None
    financial_expense: Optional[float] = None
    interest_expense: Optional[float] = None
    selling_expense: Optional[float] = None
    admin_expense: Optional[float] = None
    operating_profit: Optional[float] = None
    profit_before_tax: Optional[float] = None
    income_tax_expense: Optional[float] = None
    net_profit_after_tax: Optional[float] = None
    net_income_parent: Optional[float] = None
    eps_basic: Optional[float] = None
    ebit: Optional[float] = None
    ebitda: Optional[float] = None