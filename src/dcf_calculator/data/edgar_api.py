"""SEC EDGAR API integration for detailed financial statement analysis."""

import requests
import json
import time
from typing import Dict, Optional, List

# EDGAR API Documentation: https://www.sec.gov/edgar/sec-api-documentation

def get_company_cik(ticker: str) -> Optional[str]:
    """Get CIK (Central Index Key) for a company ticker from SEC EDGAR."""
    try:
        # SEC company tickers endpoint
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {
            "User-Agent": "DCF Calculator Finance Club (contact@example.com)"  # Required by SEC
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Rate limiting: SEC allows 10 requests/second
        time.sleep(0.1)  # 100ms delay between requests
        
        companies = response.json()
        
        # Search for ticker
        for company_data in companies.values():
            if company_data.get("ticker", "").upper() == ticker.upper():
                cik = str(company_data["cik_str"]).zfill(10)  # Pad with zeros to 10 digits
                return cik
                
        return None
        
    except Exception as e:
        print(f"Error fetching CIK for {ticker}: {e}")
        return None

def get_company_filings(cik: str, filing_type: str = "10-K") -> Optional[List[Dict]]:
    """Get list of company filings from SEC EDGAR."""
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        headers = {
            "User-Agent": "DCF Calculator Finance Club (contact@example.com)"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Rate limiting: SEC allows 10 requests/second  
        time.sleep(0.1)  # 100ms delay between requests
        
        data = response.json()
        filings = data.get("filings", {}).get("recent", {})
        
        # Filter for specific filing type
        filing_list = []
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accession_numbers = filings.get("accessionNumber", [])
        
        for i, form in enumerate(forms):
            if form == filing_type:
                filing_list.append({
                    "form": form,
                    "filing_date": dates[i],
                    "accession_number": accession_numbers[i]
                })
                
        return filing_list[:10]  # Return most recent 10 filings
        
    except Exception as e:
        print(f"Error fetching filings for CIK {cik}: {e}")
        return None

def get_financial_concept(cik: str, concept: str) -> Optional[Dict]:
    """Get XBRL financial concept data from SEC EDGAR.
    
    Args:
        cik: Company's Central Index Key (10-digit string)
        concept: XBRL concept tag (e.g., 'OperatingIncomeLoss', 'Assets')
        
    Returns:
        Dictionary with financial data or None if error/not found
        
    Example:
        data = get_financial_concept("0000320193", "OperatingIncomeLoss")
    """
    try:
        # SEC XBRL API endpoint
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
        headers = {
            "User-Agent": "DCF Calculator Finance Club (contact@example.com)"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Rate limiting: SEC allows 10 requests/second
        time.sleep(0.1)  # 100ms delay between requests
        
        return response.json()
        
    except Exception as e:
        print(f"Error fetching {concept} for CIK {cik}: {e}")
        return None

def get_operating_income(cik: str) -> Optional[Dict]:
    """Get Operating Income (EBIT) data from EDGAR."""
    return get_financial_concept(cik, "OperatingIncomeLoss")

def get_tax_expense(cik: str) -> Optional[Dict]:
    """Get Income Tax Expense data from EDGAR."""
    return get_financial_concept(cik, "IncomeTaxExpenseBenefit")

def get_depreciation_amortization(cik: str) -> Optional[Dict]:
    """Get Depreciation and Amortization data from EDGAR.
    
    Tries multiple XBRL tags as companies may use different ones:
    - DepreciationDepletionAndAmortization (most common)
    - Depreciation (alternative)
    """
    # Try primary tag first
    data = get_financial_concept(cik, "DepreciationDepletionAndAmortization")
    if data:
        return data
        
    # Try alternative tag
    print("  Trying alternative D&A tag...")
    return get_financial_concept(cik, "Depreciation")

def get_capital_expenditures(cik: str) -> Optional[Dict]:
    """Get Capital Expenditures data from EDGAR."""
    return get_financial_concept(cik, "PaymentsToAcquirePropertyPlantAndEquipment")

def get_edgar_fcff_dataframe(ticker: str, years: int = 5) -> Optional[Dict]:
    """Get EDGAR FCFF data in format ready for core.fcff DataFrame conversion."""
    return calculate_edgar_fcff(ticker, years)

def calculate_edgar_fcff(ticker: str, years: int = 5) -> Optional[Dict]:
    """Calculate FCFF using EDGAR data for specified number of years.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        years: Number of historical years to calculate (default: 5)
        
    Returns:
        Dictionary with FCFF calculations by year or None if error
        
    FCFF Formula: Operating Income - Tax Expense + D&A - CapEx
    (Note: Working Capital change not included in this simplified version)
    """
    try:
        # Get company CIK
        cik = get_company_cik(ticker)
        if not cik:
            print(f"Could not find CIK for {ticker}")
            return None
            
        print(f"Calculating EDGAR FCFF for {ticker} (CIK: {cik})")
        
        # Get all financial components
        ebit_data = get_operating_income(cik)
        tax_data = get_tax_expense(cik)
        da_data = get_depreciation_amortization(cik)
        capex_data = get_capital_expenditures(cik)
        
        if not all([ebit_data, tax_data, da_data, capex_data]):
            print("Could not retrieve all required financial data")
            return None
            
        # Extract annual data (filter for 10-K filings)
        def extract_annual_values(data, max_years):
            annual_values = {}
            usd_data = data['units']['USD']
            
            # Filter for annual data (typically 10-K filings or end of fiscal year)
            for entry in usd_data:
                if entry.get('form') == '10-K' or entry.get('fp') == 'FY':
                    year = entry['end'][:4]  # Extract year from date
                    if year not in annual_values:  # Take first occurrence for each year
                        annual_values[year] = entry['val']
                        
            # Return most recent years
            sorted_years = sorted(annual_values.keys(), reverse=True)
            return {year: annual_values[year] for year in sorted_years[:max_years]}
        
        ebit_values = extract_annual_values(ebit_data, years)
        tax_values = extract_annual_values(tax_data, years)
        da_values = extract_annual_values(da_data, years)
        capex_values = extract_annual_values(capex_data, years)
        
        # Calculate FCFF for each year
        fcff_results = {}
        common_years = set(ebit_values.keys()) & set(tax_values.keys()) & set(da_values.keys()) & set(capex_values.keys())
        
        for year in sorted(common_years, reverse=True):
            ebit = ebit_values[year]
            tax = tax_values[year] 
            da = da_values[year]
            capex = abs(capex_values[year])  # CapEx is typically negative in cash flow
            
            # FCFF = EBIT - Taxes + D&A - CapEx
            fcff = ebit - tax + da - capex
            fcff_results[year] = {
                'fcff': fcff,
                'ebit': ebit,
                'tax_expense': tax,
                'depreciation_amortization': da,
                'capital_expenditures': capex
            }
            
        return fcff_results
        
    except Exception as e:
        print(f"Error calculating EDGAR FCFF for {ticker}: {e}")
        return None

if __name__ == "__main__":
    # Test with Apple
    ticker = input("Enter stock ticker: ").upper()
    
    print(f"Getting CIK for {ticker}...")
    cik = get_company_cik(ticker)
    
    if cik:
        print(f"CIK for {ticker}: {cik}")
        
        print(f"\n=== Current Year Data (EDGAR) ===")
        ebit_data = get_operating_income(cik)
        tax_data = get_tax_expense(cik)
        da_data = get_depreciation_amortization(cik)
        capex_data = get_capital_expenditures(cik)
        
        # Get most recent values
        if ebit_data:
            recent_ebit = ebit_data['units']['USD'][-1]['val']
            print(f"EBIT: ${recent_ebit:,.0f}")
        else:
            print("Could not fetch EBIT")
            
        if tax_data:
            recent_tax = tax_data['units']['USD'][-1]['val']
            print(f"Tax Expense: ${recent_tax:,.0f}")
        else:
            print("Could not fetch tax expense")
            
        if da_data:
            recent_da = da_data['units']['USD'][-1]['val']
            print(f"D&A: ${recent_da:,.0f}")
        else:
            print("Could not fetch D&A")
            
        if capex_data:
            recent_capex = abs(capex_data['units']['USD'][-1]['val'])
            print(f"CapEx: ${recent_capex:,.0f}")
        else:
            print("Could not fetch CapEx")
        
        print(f"\n=== Historical FCFF Data (EDGAR) ===")
        fcff_results = calculate_edgar_fcff(ticker, years=5)
        
        if fcff_results:
            for year, data in fcff_results.items():
                print(f"\n{year}:")
                print(f"  ebit: ${data['ebit']:,.0f}")
                print(f"  tax_expense: ${data['tax_expense']:,.0f}")
                print(f"  depreciation_amortization: ${data['depreciation_amortization']:,.0f}")
                print(f"  capital_expenditures: ${data['capital_expenditures']:,.0f}")
                
            print(f"\n=== Historical FCFF Calculations (EDGAR) ===")
            for year, data in fcff_results.items():
                print(f"{year}: ${data['fcff']:,.0f}")
        else:
            print("Could not calculate FCFF")
            
        print(f"\n=== Basic Filing Info ===")
        filings = get_company_filings(cik, "10-K")
        if filings:
            print(f"Found {len(filings)} recent 10-K filings:")
            for filing in filings[:3]:  # Show only first 3
                print(f"  {filing['filing_date']}: {filing['accession_number']}")
    else:
        print(f"Could not find CIK for {ticker}")
