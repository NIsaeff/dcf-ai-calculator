"""Simple Yahoo Finance API integration to get EBIT data."""

import yfinance as yf

def get_ebit(ticker):
    """Get EBIT (Earnings Before Interest and Tax) for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        
        if financials.empty:
            return None
            
        # EBIT is typically listed as "EBIT" or "Operating Income"
        if "EBIT" in financials.index:
            ebit = financials.loc["EBIT"].iloc[0]  # Most recent year
        elif "Operating Income" in financials.index:
            ebit = financials.loc["Operating Income"].iloc[0]
        else:
            return None
            
        return float(ebit)
    except Exception as e:
        print(f"Error fetching EBIT for {ticker}: {e}")
        return None

def get_tax_expense(ticker):
    """Get Tax Provision (tax expense) for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        
        if financials.empty:
            return None
            
        if "Tax Provision" in financials.index:
            tax_expense = financials.loc["Tax Provision"].iloc[0]  # Most recent year
            return float(tax_expense)
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching tax expense for {ticker}: {e}")
        return None

def get_depreciation_amortization(ticker):
    """Get Depreciation and Amortization from cash flow statement."""
    # Note: Other options available:
    # - "Reconciled Depreciation" (from income statement)
    # - "Depreciation Amortization Depletion" (from cash flow statement)
    try:
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow
        
        if cashflow.empty:
            return None
            
        if "Depreciation And Amortization" in cashflow.index:
            da = cashflow.loc["Depreciation And Amortization"].iloc[0]  # Most recent year
            return float(da)
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching D&A for {ticker}: {e}")
        return None

def get_capital_expenditures(ticker):
    """Get Capital Expenditures from cash flow statement (for FCFF calculation)."""
    try:
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow
        
        if cashflow.empty:
            return None
            
        if "Capital Expenditure" in cashflow.index:
            capex = cashflow.loc["Capital Expenditure"].iloc[0]  # Most recent year
            return float(abs(capex))  # Return absolute value (CapEx is negative in cash flow)
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching CapEx for {ticker}: {e}")
        return None

def get_working_capital_change(ticker):
    """Get Change in Working Capital from cash flow statement (for FCFF calculation)."""
    try:
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow
        
        if cashflow.empty:
            return None
            
        if "Change In Working Capital" in cashflow.index:
            wc_change = cashflow.loc["Change In Working Capital"].iloc[0]  # Most recent year
            return float(wc_change)  # Positive = increase in WC (reduces FCF), Negative = decrease in WC (increases FCF)
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching working capital change for {ticker}: {e}")
        return None

if __name__ == "__main__":
    # Test with Apple
    ticker = input("Enter stock ticker: ").upper()
    ebit = get_ebit(ticker)
    tax_expense = get_tax_expense(ticker)
    da = get_depreciation_amortization(ticker)
    capex = get_capital_expenditures(ticker)
    wc_change = get_working_capital_change(ticker)
    
    print(f"EBIT for {ticker}: ${ebit:,.0f}" if ebit else f"Could not fetch EBIT for {ticker}")
    print(f"Tax Expense for {ticker}: ${tax_expense:,.0f}" if tax_expense else f"Could not fetch tax expense for {ticker}")
    print(f"D&A for {ticker}: ${da:,.0f}" if da else f"Could not fetch D&A for {ticker}")
    print(f"CapEx for {ticker}: ${capex:,.0f}" if capex else f"Could not fetch CapEx for {ticker}")
    print(f"Working Capital Change for {ticker}: ${wc_change:,.0f}" if wc_change else f"Could not fetch WC change for {ticker}")
