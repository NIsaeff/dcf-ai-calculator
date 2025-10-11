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

def get_historical_fcff_data(ticker):
    """Get historical data for all FCFF components (4 years from Yahoo Finance)."""
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        cashflow = stock.cashflow
        
        if financials.empty or cashflow.empty:
            return None
            
        # Get years (columns)
        years = financials.columns.tolist()
        
        historical_data = {}
        for year in years:
            year_str = year.strftime('%Y')
            
            # Get EBIT
            ebit = financials.loc["EBIT", year] if "EBIT" in financials.index else None
            
            # Get Tax Expense
            tax = financials.loc["Tax Provision", year] if "Tax Provision" in financials.index else None
            
            # Get D&A
            da = cashflow.loc["Depreciation And Amortization", year] if "Depreciation And Amortization" in cashflow.index else None
            
            # Get CapEx
            capex = abs(cashflow.loc["Capital Expenditure", year]) if "Capital Expenditure" in cashflow.index else None
            
            # Get Working Capital Change
            wc_change = cashflow.loc["Change In Working Capital", year] if "Change In Working Capital" in cashflow.index else None
            
            historical_data[year_str] = {
                'ebit': float(ebit) if ebit is not None else None,
                'tax_expense': float(tax) if tax is not None else None,
                'depreciation_amortization': float(da) if da is not None else None,
                'capital_expenditures': float(capex) if capex is not None else None,
                'working_capital_change': float(wc_change) if wc_change is not None else None
            }
            
        return historical_data
        
    except Exception as e:
        print(f"Error fetching historical FCFF data for {ticker}: {e}")
        return None

def calculate_fcff(ebit, tax_expense, da, capex, wc_change):
    """Calculate Free Cash Flow to Firm using the basic formula.
    
    FCFF = EBIT - Taxes + D&A - CapEx - Change in Working Capital
    """
    fcff = ebit - tax_expense + da - capex - wc_change
    return fcff

def calculate_historical_fcff(ticker):
    """Calculate FCFF for all available historical years."""
    historical_data = get_historical_fcff_data(ticker)
    if not historical_data:
        return None
    
    fcff_results = {}
    for year, data in historical_data.items():
        if all(data[key] is not None for key in data.keys()):
            fcff = calculate_fcff(
                data['ebit'],
                data['tax_expense'], 
                data['depreciation_amortization'],
                data['capital_expenditures'],
                data['working_capital_change']
            )
            fcff_results[year] = fcff
    
    return fcff_results

if __name__ == "__main__":
    # Test with Apple
    ticker = input("Enter stock ticker: ").upper()
    
    print("=== Current Year Data ===")
    ebit = get_ebit(ticker)
    tax_expense = get_tax_expense(ticker)
    da = get_depreciation_amortization(ticker)
    capex = get_capital_expenditures(ticker)
    wc_change = get_working_capital_change(ticker)
    
    print(f"EBIT: ${ebit:,.0f}" if ebit else "Could not fetch EBIT")
    print(f"Tax Expense: ${tax_expense:,.0f}" if tax_expense else "Could not fetch tax expense")
    print(f"D&A: ${da:,.0f}" if da else "Could not fetch D&A")
    print(f"CapEx: ${capex:,.0f}" if capex else "Could not fetch CapEx")
    print(f"Working Capital Change: ${wc_change:,.0f}" if wc_change else "Could not fetch WC change")
    
    print("\n=== Historical Data (4 Years) ===")
    historical = get_historical_fcff_data(ticker)
    if historical:
        for year, data in historical.items():
            print(f"\n{year}:")
            for component, value in data.items():
                if value is not None:
                    print(f"  {component}: ${value:,.0f}")
                else:
                    print(f"  {component}: N/A")
    
    print("\n=== Historical FCFF Calculations ===")
    fcff_results = calculate_historical_fcff(ticker)
    if fcff_results:
        for year, fcff in fcff_results.items():
            print(f"{year}: ${fcff:,.0f}")
    else:
        print("Could not calculate FCFF")
