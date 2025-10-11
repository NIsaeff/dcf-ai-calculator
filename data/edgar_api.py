"""SEC EDGAR API integration for detailed financial statement analysis."""

import requests
import json
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

if __name__ == "__main__":
    # Test with Apple
    ticker = input("Enter stock ticker: ").upper()
    
    print(f"Getting CIK for {ticker}...")
    cik = get_company_cik(ticker)
    
    if cik:
        print(f"CIK for {ticker}: {cik}")
        
        print(f"\nGetting 10-K filings...")
        filings = get_company_filings(cik, "10-K")
        
        if filings:
            print(f"Found {len(filings)} recent 10-K filings:")
            for filing in filings:
                print(f"  {filing['filing_date']}: {filing['accession_number']}")
        else:
            print("No 10-K filings found")
    else:
        print(f"Could not find CIK for {ticker}")