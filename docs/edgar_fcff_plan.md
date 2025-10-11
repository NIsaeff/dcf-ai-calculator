# EDGAR FCFF Implementation Plan

## Overview
This document outlines the plan to implement Free Cash Flow to Firm (FCFF) calculation using SEC EDGAR data instead of relying solely on Yahoo Finance.

## What is XBRL?
**XBRL (eXtensible Business Reporting Language)** is a global standard for exchanging business information. Key features:

- **Standardized Tags**: Financial concepts have consistent identifiers (e.g., `OperatingIncomeLoss` for EBIT)
- **Machine Readable**: Structured XML format allows automated data extraction
- **SEC Mandate**: All public companies must file financial statements in XBRL format
- **Consistency**: Same tag means same concept across all companies
- **Historical Data**: Available from 2009+ for most major companies

## What is CIK?
**CIK (Central Index Key)** is the SEC's unique identifier system:

- **10-digit number**: Each public company gets a unique identifier (e.g., Apple = `0000320193`)
- **SEC Database**: Primary key for all SEC filings and data
- **Ticker Mapping**: Our code maps stock tickers (AAPL) to CIKs
- **Required for EDGAR API**: All XBRL endpoints require CIK, not ticker symbols

## EDGAR FCFF Implementation Analysis

### Key XBRL Tags Identified:
1. **EBIT**: `OperatingIncomeLoss` - Operating Income (Loss)
2. **Tax Expense**: `IncomeTaxExpenseBenefit` - Income Tax Expense (Benefit)  
3. **Depreciation & Amortization**: `DepreciationDepletionAndAmortization`
4. **Capital Expenditures**: `PaymentsToAcquirePropertyPlantAndEquipment`
5. **Operating Cash Flow**: `NetCashProvidedByUsedInOperatingActivities` (alternative to manual WC calculation)

### EDGAR API Structure:
- **Endpoint Pattern**: `https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json`
- **Data Format**: JSON with historical values by fiscal year/quarter
- **Required Headers**: User-Agent with contact email
- **Rate Limit**: 10 requests/second maximum

### Proposed Functions to Add:

```python
def get_financial_concept(cik: str, concept: str) -> Optional[Dict]:
    """Get XBRL financial concept data from EDGAR."""
    
def get_operating_income(cik: str) -> Optional[Dict]:
    """Get Operating Income (EBIT) data."""
    
def get_tax_expense(cik: str) -> Optional[Dict]:
    """Get Income Tax Expense data."""
    
def get_depreciation_amortization(cik: str) -> Optional[Dict]:
    """Get Depreciation and Amortization data."""
    
def get_capital_expenditures(cik: str) -> Optional[Dict]:
    """Get Capital Expenditures data."""
    
def get_operating_cash_flow(cik: str) -> Optional[Dict]:
    """Get Operating Cash Flow data."""
    
def calculate_edgar_fcff(ticker: str, years: int = 5) -> Optional[Dict]:
    """Calculate FCFF using EDGAR data for specified years."""
```

### Implementation Strategy:
1. **Generic XBRL function** for any financial concept
2. **Specific wrapper functions** for each FCFF component
3. **Historical data extraction** for multiple years
4. **FCFF calculation** using EDGAR data
5. **Rate limiting** to comply with SEC requirements
6. **Error handling** for missing data or API failures

### Advantages over Yahoo Finance:
- **More comprehensive historical data** (10+ years vs 4 years)
- **Primary source data** directly from SEC filings
- **Quarterly and annual data** available
- **XBRL standardization** ensures consistency
- **Regulatory compliance** - data matches official filings

### Current Limitations:
- **More complex API** requiring CIK lookup first
- **Rate limiting** considerations (10 requests/second)
- **Working Capital** may need manual calculation from balance sheet items

## FCFF Formula Using EDGAR Data:
```
FCFF = Operating Income - Tax Expense + Depreciation & Amortization - Capital Expenditures - Change in Working Capital

Alternative approach:
FCFF = Operating Cash Flow - Capital Expenditures
```

## Implementation Status:
- ✅ EDGAR XBRL API structure understood  
- ✅ Key financial concept tags identified for FCFF calculation
- ✅ Function architecture designed
- ✅ Implementation strategy planned
- ✅ **COMPLETED**: All functions implemented in edgar_api.py

## Implementation Results:
**Functions Added:**
- `get_financial_concept(cik, concept)` - Generic XBRL data retrieval
- `get_operating_income(cik)` - EBIT data  
- `get_tax_expense(cik)` - Tax expense data
- `get_depreciation_amortization(cik)` - D&A data with fallback handling
- `get_capital_expenditures(cik)` - CapEx data
- `calculate_edgar_fcff(ticker, years=5)` - Complete FCFF calculation

**Key Features:**
- ✅ Rate limiting (100ms delay) for SEC compliance
- ✅ Fallback handling for different XBRL tags (e.g., D&A variations)
- ✅ Annual data extraction from 10-K filings
- ✅ Error handling for missing data
- ✅ 10+ years of historical data support

**Test Results:**
- **Apple (AAPL)**: 2024 FCFF = $95.5B, 2023 = $98.1B, 2022 = $100.5B
- **Microsoft (MSFT)**: 2025 FCFF = $64.2B, 2024 = $60.5B (used fallback D&A tag)
- **Performance**: ~2-3 seconds per company (includes rate limiting)

## API Examples:
```bash
# Get Apple's Operating Income data
curl -H "User-Agent: DCF Calculator Finance Club (contact@example.com)" \
  "https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/OperatingIncomeLoss.json"

# Get Apple's Tax Expense data  
curl -H "User-Agent: DCF Calculator Finance Club (contact@example.com)" \
  "https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/IncomeTaxExpenseBenefit.json"
```

## Benefits for DCF Calculator:
The EDGAR implementation will provide more reliable, comprehensive financial data for accurate DCF valuations, especially important for the Finance Club's $300k portfolio management.