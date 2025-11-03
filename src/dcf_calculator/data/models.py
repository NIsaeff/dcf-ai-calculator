"""Pydantic models for financial data validation and structured extraction."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import date


class FinancialMetric(BaseModel):
    """Single financial metric with metadata."""
    value: float = Field(..., description="Numeric value of the metric")
    unit: str = Field(default="USD", description="Currency or unit (e.g., 'USD', 'shares')")
    fiscal_year: str = Field(..., description="Fiscal year (e.g., '2023')")
    fiscal_period: str = Field(default="FY", description="Fiscal period (FY, Q1, Q2, Q3, Q4)")
    source: Optional[str] = Field(default=None, description="Data source (XBRL, LLM, Yahoo, etc.)")
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score 0-1")

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        """Ensure value is not NaN or infinite."""
        if v != v or abs(v) == float('inf'):  # Check for NaN or inf
            raise ValueError("Value must be a finite number")
        return v


class FCFFComponents(BaseModel):
    """Free Cash Flow to Firm components for a single period."""
    fiscal_year: str = Field(..., description="Fiscal year")
    ebit: FinancialMetric = Field(..., description="Earnings Before Interest and Tax (Operating Income)")
    tax_expense: FinancialMetric = Field(..., description="Income tax expense")
    depreciation_amortization: FinancialMetric = Field(..., description="Depreciation and Amortization")
    capital_expenditures: FinancialMetric = Field(..., description="Capital Expenditures (CapEx)")
    working_capital_change: Optional[FinancialMetric] = Field(default=None, description="Change in Working Capital")

    @property
    def fcff(self) -> float:
        """Calculate FCFF from components."""
        wc_change = self.working_capital_change.value if self.working_capital_change else 0.0
        return (self.ebit.value -
                self.tax_expense.value +
                self.depreciation_amortization.value -
                self.capital_expenditures.value -
                wc_change)


class HistoricalFCFF(BaseModel):
    """Historical FCFF data for multiple years."""
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: Optional[str] = Field(default=None, description="Company name")
    years: List[FCFFComponents] = Field(..., description="List of yearly FCFF components")

    @field_validator('years')
    @classmethod
    def validate_years(cls, v):
        """Ensure years are in descending order (most recent first)."""
        if len(v) < 1:
            raise ValueError("Must have at least one year of data")
        return v


class WACCComponents(BaseModel):
    """Weighted Average Cost of Capital components."""
    ticker: str = Field(..., description="Stock ticker symbol")
    fiscal_year: str = Field(..., description="Fiscal year for these values")

    # Market values
    market_cap: FinancialMetric = Field(..., description="Market capitalization (equity value)")
    total_debt: FinancialMetric = Field(..., description="Total debt (book or market value)")

    # Cost components
    cost_of_equity: Optional[float] = Field(default=None, description="Cost of equity (as decimal, e.g., 0.10 = 10%)")
    cost_of_debt: Optional[float] = Field(default=None, description="Cost of debt (as decimal)")
    tax_rate: Optional[float] = Field(default=None, description="Effective tax rate (as decimal)")

    # CAPM components (if cost_of_equity not directly available)
    beta: Optional[float] = Field(default=None, description="Stock beta")
    risk_free_rate: Optional[float] = Field(default=None, description="Risk-free rate (as decimal)")
    market_risk_premium: Optional[float] = Field(default=None, description="Market risk premium (as decimal)")

    @property
    def wacc(self) -> Optional[float]:
        """Calculate WACC if all components available."""
        if not all([self.cost_of_equity, self.cost_of_debt, self.tax_rate]):
            return None

        equity_value = self.market_cap.value
        debt_value = self.total_debt.value
        total_value = equity_value + debt_value

        if total_value == 0:
            return None

        equity_weight = equity_value / total_value
        debt_weight = debt_value / total_value

        wacc = (equity_weight * self.cost_of_equity +
                debt_weight * self.cost_of_debt * (1 - self.tax_rate))

        return wacc


class IncomeStatement(BaseModel):
    """Income statement extracted from SEC filings."""
    fiscal_year: str = Field(..., description="Fiscal year")
    revenue: Optional[FinancialMetric] = Field(default=None, description="Total revenue/sales")
    operating_income: Optional[FinancialMetric] = Field(default=None, description="Operating income (EBIT)")
    net_income: Optional[FinancialMetric] = Field(default=None, description="Net income")
    interest_expense: Optional[FinancialMetric] = Field(default=None, description="Interest expense")
    tax_expense: Optional[FinancialMetric] = Field(default=None, description="Income tax expense")
    ebitda: Optional[FinancialMetric] = Field(default=None, description="EBITDA if reported")


class BalanceSheet(BaseModel):
    """Balance sheet extracted from SEC filings."""
    fiscal_year: str = Field(..., description="Fiscal year")
    total_assets: Optional[FinancialMetric] = Field(default=None, description="Total assets")
    total_liabilities: Optional[FinancialMetric] = Field(default=None, description="Total liabilities")
    total_equity: Optional[FinancialMetric] = Field(default=None, description="Shareholders' equity")
    current_assets: Optional[FinancialMetric] = Field(default=None, description="Current assets")
    current_liabilities: Optional[FinancialMetric] = Field(default=None, description="Current liabilities")
    long_term_debt: Optional[FinancialMetric] = Field(default=None, description="Long-term debt")
    short_term_debt: Optional[FinancialMetric] = Field(default=None, description="Short-term debt")


class CashFlowStatement(BaseModel):
    """Cash flow statement extracted from SEC filings."""
    fiscal_year: str = Field(..., description="Fiscal year")
    operating_cash_flow: Optional[FinancialMetric] = Field(default=None, description="Cash from operations")
    depreciation_amortization: Optional[FinancialMetric] = Field(default=None, description="D&A")
    capital_expenditures: Optional[FinancialMetric] = Field(default=None, description="CapEx")
    free_cash_flow: Optional[FinancialMetric] = Field(default=None, description="FCF if reported")
    working_capital_change: Optional[FinancialMetric] = Field(default=None, description="Change in working capital")


class CompanyFinancials(BaseModel):
    """Complete financial statements for a company."""
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Official company name")
    cik: Optional[str] = Field(default=None, description="SEC CIK number")
    fiscal_year_end: Optional[str] = Field(default=None, description="Fiscal year end (e.g., 'December')")

    income_statements: List[IncomeStatement] = Field(default_factory=list)
    balance_sheets: List[BalanceSheet] = Field(default_factory=list)
    cash_flow_statements: List[CashFlowStatement] = Field(default_factory=list)


class LLMExtractionResult(BaseModel):
    """Result from LLM-based financial data extraction."""
    ticker: str = Field(..., description="Stock ticker symbol")
    extraction_date: str = Field(..., description="Date of extraction")
    source_filing: str = Field(..., description="SEC filing type (10-K, 10-Q, etc.)")
    filing_date: str = Field(..., description="Filing date")

    # Extracted data
    financials: CompanyFinancials = Field(..., description="Extracted financial statements")

    # Metadata
    extraction_method: str = Field(default="llm", description="Method used (xbrl, llm, hybrid)")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall extraction confidence")
    notes: Optional[List[str]] = Field(default=None, description="Extraction notes or warnings")

    @property
    def is_high_confidence(self) -> bool:
        """Check if extraction has high confidence (>= 0.8)."""
        return self.confidence_score >= 0.8


class DCFInputs(BaseModel):
    """Complete inputs needed for DCF valuation."""
    ticker: str = Field(..., description="Stock ticker symbol")

    # Historical data
    historical_fcff: HistoricalFCFF = Field(..., description="Historical FCFF data")

    # WACC components
    wacc_data: WACCComponents = Field(..., description="WACC calculation components")

    # Projection assumptions
    projection_years: int = Field(default=5, ge=1, le=10, description="Years to project")
    terminal_growth_rate: float = Field(default=0.025, ge=0.0, le=0.10, description="Terminal growth rate")

    # Additional data
    shares_outstanding: Optional[FinancialMetric] = Field(default=None, description="Shares outstanding")
    current_stock_price: Optional[float] = Field(default=None, description="Current stock price")

    @property
    def is_complete(self) -> bool:
        """Check if all required inputs are available."""
        return all([
            len(self.historical_fcff.years) >= 3,  # At least 3 years of data
            self.wacc_data.wacc is not None,
            self.shares_outstanding is not None
        ])
