# Data Sources & API Design Documentation

## Overview

This document describes the implementation of data retrieval APIs for the DCF Calculator, focusing on Yahoo Finance and SEC EDGAR integrations for Free Cash Flow to Firm (FCFF) analysis.

## Yahoo Finance Implementation (`yahoofin_api.py`)

### API Documentation

- **Library**: yfinance (https://github.com/ranaroussi/yfinance)
- **Data Sources**: Income Statement (`stock.financials`) and Cash Flow Statement (`stock.cashflow`)
- **Historical Coverage**: 4 years of annual data

### Core Functions

#### Individual Component Functions

```python
get_ebit(ticker: str) -> Optional[float]
get_tax_expense(ticker: str) -> Optional[float]
get_depreciation_amortization(ticker: str) -> Optional[float]
get_capital_expenditures(ticker: str) -> Optional[float]
get_working_capital_change(ticker: str) -> Optional[float]
```

**Design Decisions:**

- **EBIT Source**: Uses "EBIT" field from income statement, fallback to "Operating Income"
- **Tax Expense**: Uses "Tax Provision" from income statement (actual tax expense)
- **D&A Source**: Uses "Depreciation And Amortization" from cash flow statement
  - _Alternative options noted_: "Reconciled Depreciation", "Depreciation Amortization Depletion"
- **CapEx Handling**: Takes absolute value of "Capital Expenditure" (negative in cash flow)
- **Working Capital**: Raw "Change In Working Capital" value (positive = increase, negative = decrease)

#### Historical Data Functions

```python
get_historical_fcff_data(ticker: str) -> Optional[Dict[str, Dict[str, float]]]
```

**Data Structure:**
NOTE: represent in thousands, millions?

```json
{
  "2024": {
    "ebit": 123216000000.0,
    "tax_expense": 29749000000.0,
    "depreciation_amortization": 11445000000.0,
    "capital_expenditures": 9447000000.0,
    "working_capital_change": 3651000000.0
  },
  "2023": { ... }
}
```

#### FCFF Calculation Functions

```python
calculate_fcff(ebit, tax_expense, da, capex, wc_change) -> float
calculate_historical_fcff(ticker: str) -> Optional[Dict[str, float]]
```

**FCFF Formula:**

```
FCFF = EBIT - Tax Expense + D&A - CapEx - Change in Working Capital
```

### Error Handling

- **Pattern**: Try/catch with specific error messages
- **Null Handling**: Returns `None` for missing data, functions check for empty DataFrames
- **Data Validation**: Converts to float, handles pandas iloc indexing

### Testing Results (Apple Inc.)

```
2024 FCFF: $91,814,000,000
2023 FCFF: $104,697,000,000
2022 FCFF: $99,333,000,000
2021 FCFF: $102,435,000,000
```

## SEC EDGAR Implementation (`edgar_api.py`)

### API Documentation

- **API**: SEC EDGAR (https://www.sec.gov/edgar/sec-api-documentation)
- **Endpoints Used**:
  - Company Tickers: `https://www.sec.gov/files/company_tickers.json`
  - Company Submissions: `https://data.sec.gov/submissions/CIK{cik}.json`
- **Rate Limiting**: SEC requires User-Agent header with contact info

### Core Functions

#### Company Identification

```python
get_company_cik(ticker: str) -> Optional[str]
```

- **Purpose**: Convert stock ticker to SEC Central Index Key (CIK)
- **Process**: Downloads company_tickers.json, searches for ticker match
- **Output**: 10-digit zero-padded CIK string (e.g., "0000320193" for AAPL)

#### Filing Retrieval

```python
get_company_filings(cik: str, filing_type: str = "10-K") -> Optional[List[Dict]]
```

- **Purpose**: Get list of recent company filings from SEC database
- **Default**: 10-K annual reports (10 most recent)
- **Output Structure**:

```json
[
  {
    "form": "10-K",
    "filing_date": "2024-11-01",
    "accession_number": "0000320193-24-000123"
  }
]
```

### SEC API Requirements

- **User-Agent Header**: Required by SEC, format: "App Name (contact@email.com)"
- **Rate Limiting**: SEC recommends 10 requests per second maximum
- **Data Access**: Public filings available without authentication

### Testing Results (Apple Inc.)

```
CIK: 0000320193
Recent 10-K Filings: 10 years (2015-2024)
Latest Filing: 2024-11-01 (0000320193-24-000123)
```

## Integration Strategy

### Data Complementarity

- **Yahoo Finance**: Quick access, 4 years, processed financial metrics
- **SEC EDGAR**: Detailed source, 10+ years, raw financial statements
- **Use Case**: Yahoo for rapid prototyping, EDGAR for comprehensive analysis

### Future Enhancements

1. **EDGAR Financial Statement Parsing**: Extract detailed line items from XBRL
2. **Data Validation**: Cross-reference Yahoo Finance vs EDGAR calculations
3. **Extended Historical Data**: Parse 10+ years from EDGAR for trend analysis
4. **Error Recovery**: Fallback between data sources when one fails

### Data Quality Considerations

- **Yahoo Finance**: Pre-processed, may have adjustments/reconciliations
- **SEC EDGAR**: Raw filings, requires more parsing but authoritative source
- **Recommendation**: Use Yahoo for development, validate with EDGAR for production

## Development Notes

- **Simple First Approach**: Individual functions before complex aggregations
- **Error Handling**: Graceful degradation when data unavailable
- **Testing Strategy**: Validate with known companies (AAPL, MSFT) before broader use

