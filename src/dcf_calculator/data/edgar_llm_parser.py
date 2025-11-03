"""LLM-based SEC EDGAR XBRL parser using LangChain and Claude.

This module uses LLM to intelligently map non-standard XBRL tags to required financial metrics.
Primary approach: Parse structured XBRL JSON (not HTML).
"""

import os
import time
import requests
import json
from typing import Optional, Dict, List, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_anthropic import ChatAnthropic

from dcf_calculator.data.models import FinancialMetric, FCFFComponents
from dcf_calculator.data.edgar_api import get_company_cik


# SEC EDGAR API base URLs
EDGAR_API_BASE = "https://data.sec.gov/api/xbrl"


def get_company_facts(cik: str) -> Optional[Dict[str, Any]]:
    """Fetch complete XBRL company facts from SEC API.

    This returns ALL XBRL concepts reported by the company, including custom taxonomies.

    Args:
        cik: Company CIK (10-digit)

    Returns:
        Dictionary with all XBRL facts or None if error

    Example structure:
    {
        "entityName": "Apple Inc.",
        "cik": "0000320193",
        "facts": {
            "us-gaap": {
                "OperatingIncomeLoss": { "units": { "USD": [...] } },
                "Assets": { "units": { "USD": [...] } },
                ...
            },
            "dei": {...},
            "aapl": {...}  # Custom taxonomy
        }
    }
    """
    try:
        # Use companyfacts endpoint which has full XBRL data
        facts_url = f"{EDGAR_API_BASE}/companyfacts/CIK{cik}.json"

        headers = {
            "User-Agent": "DCF Calculator Finance Club (contact@example.com)"
        }

        response = requests.get(facts_url, headers=headers)
        response.raise_for_status()

        # Rate limiting: SEC allows 10 requests/second
        time.sleep(0.1)

        return response.json()

    except Exception as e:
        print(f"Error fetching company facts for CIK {cik}: {e}")
        return None


def get_available_concepts(company_facts: Dict[str, Any], taxonomy: str = "us-gaap") -> List[str]:
    """Extract list of available XBRL concepts for a company.

    Args:
        company_facts: Company facts dictionary from get_company_facts()
        taxonomy: Taxonomy to extract (default: 'us-gaap')

    Returns:
        List of concept names
    """
    try:
        if not company_facts or 'facts' not in company_facts:
            return []

        facts = company_facts.get('facts', {})

        # Get concepts from specified taxonomy
        taxonomy_facts = facts.get(taxonomy, {})

        return list(taxonomy_facts.keys())

    except Exception as e:
        print(f"Error extracting concepts: {e}")
        return []


def get_llm_client(model: str = "claude-3-5-sonnet-20241022", temperature: float = 0.0) -> ChatAnthropic:
    """Initialize LangChain Claude client.

    Args:
        model: Claude model name
        temperature: Sampling temperature (0.0 = deterministic)

    Returns:
        ChatAnthropic instance
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    return ChatAnthropic(
        model=model,
        temperature=temperature,
        anthropic_api_key=api_key,
        max_tokens=4096
    )


def map_concepts_to_metrics_llm(available_concepts: List[str]) -> Optional[Dict[str, str]]:
    """Use LLM to map available XBRL concepts to required financial metrics.

    Args:
        available_concepts: List of XBRL concept names available for company

    Returns:
        Dictionary mapping metric names to XBRL concept names
        Example: {"ebit": "OperatingIncomeLoss", "tax_expense": "IncomeTaxExpenseBenefit"}
    """
    try:
        # Filter to likely income/cash flow statement concepts
        relevant_keywords = [
            'income', 'revenue', 'operating', 'tax', 'depreciation', 'amortization',
            'capital', 'expenditure', 'cash', 'flow', 'working', 'ebit', 'assets',
            'liabilities', 'equity', 'debt', 'interest', 'payment', 'property', 'plant'
        ]

        filtered_concepts = [
            c for c in available_concepts
            if any(keyword.lower() in c.lower() for keyword in relevant_keywords)
        ]

        # Limit to 100 most relevant concepts
        concepts_str = '\n'.join(sorted(filtered_concepts[:100]))

        # Create parser for JSON output
        parser = JsonOutputParser()

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in XBRL financial taxonomies.

Given a list of XBRL concept names, map them to the following required financial metrics:

Required Metrics:
- ebit: Operating Income / Earnings Before Interest and Tax
- tax_expense: Income Tax Expense / Tax Provision
- depreciation_amortization: Depreciation and Amortization expense
- capital_expenditures: Capital Expenditures (payments for PP&E)
- working_capital_change: Change in Working Capital (optional)
- revenue: Total Revenue / Net Sales (optional)
- net_income: Net Income (optional)

Return a JSON object mapping metric names to the BEST matching XBRL concept name.
If no good match exists for a metric, omit it from the response.

Example output:
{{
  "ebit": "OperatingIncomeLoss",
  "tax_expense": "IncomeTaxExpenseBenefit",
  "depreciation_amortization": "DepreciationDepletionAndAmortization",
  "capital_expenditures": "PaymentsToAcquirePropertyPlantAndEquipment"
}}

Only return valid JSON. Be precise - choose the concept that EXACTLY matches the metric definition."""),
            ("user", "Available XBRL concepts:\n\n{concepts}")
        ])

        # Format prompt
        formatted_prompt = prompt.format_messages(concepts=concepts_str)

        # Get LLM client
        llm = get_llm_client()

        # Invoke chain
        result = llm.invoke(formatted_prompt)

        # Parse JSON response
        parsed = parser.parse(result.content)

        print(f"[LLM] Mapped {len(parsed)} metrics to XBRL concepts")

        return parsed

    except Exception as e:
        print(f"Error mapping concepts with LLM: {e}")
        return None


def extract_annual_values(concept_data: Dict, years: int = 5) -> Dict[str, float]:
    """Extract annual values from XBRL concept data.

    Args:
        concept_data: XBRL concept data from company facts
        years: Number of years to extract

    Returns:
        Dictionary mapping fiscal year to value
    """
    try:
        annual_values = {}

        # Get USD units
        if 'units' not in concept_data or 'USD' not in concept_data['units']:
            return {}

        usd_data = concept_data['units']['USD']

        # Filter for annual data (10-K filings or full year)
        for entry in usd_data:
            # Look for annual filings (form=10-K or fp=FY)
            if entry.get('form') == '10-K' or entry.get('fp') == 'FY':
                year = entry['end'][:4]  # Extract year from date
                value = entry['val']

                # Take first occurrence for each year (most detailed)
                if year not in annual_values:
                    annual_values[year] = value

        # Return most recent years
        sorted_years = sorted(annual_values.keys(), reverse=True)
        return {year: annual_values[year] for year in sorted_years[:years]}

    except Exception as e:
        print(f"Error extracting annual values: {e}")
        return {}


def get_concept_value(company_facts: Dict, concept_name: str, taxonomy: str = "us-gaap") -> Dict[str, float]:
    """Get values for a specific XBRL concept.

    Args:
        company_facts: Company facts dictionary
        concept_name: XBRL concept name
        taxonomy: Taxonomy (default: 'us-gaap')

    Returns:
        Dictionary mapping fiscal year to value
    """
    try:
        facts = company_facts.get('facts', {})
        taxonomy_facts = facts.get(taxonomy, {})

        if concept_name not in taxonomy_facts:
            return {}

        concept_data = taxonomy_facts[concept_name]
        return extract_annual_values(concept_data)

    except Exception as e:
        print(f"Error getting concept value for {concept_name}: {e}")
        return {}


def extract_fcff_with_llm(ticker: str, years: int = 5) -> Optional[Dict]:
    """Extract FCFF data using LLM to map XBRL concepts.

    This is the smart fallback when standard XBRL tags aren't available.

    Args:
        ticker: Stock ticker symbol
        years: Number of years to extract

    Returns:
        Dictionary with FCFF components by year, or None if failed
    """
    try:
        # Get company CIK
        cik = get_company_cik(ticker)
        if not cik:
            print(f"Could not find CIK for {ticker}")
            return None

        print(f"[LLM] Fetching XBRL company facts for {ticker}...")

        # Get all company facts
        company_facts = get_company_facts(cik)
        if not company_facts:
            return None

        # Get available concepts
        concepts = get_available_concepts(company_facts)
        print(f"[LLM] Found {len(concepts)} XBRL concepts")

        if not concepts:
            return None

        # Use LLM to map concepts to metrics
        concept_mapping = map_concepts_to_metrics_llm(concepts)

        if not concept_mapping:
            print("[LLM] Failed to map concepts")
            return None

        print(f"[LLM] Concept mapping: {json.dumps(concept_mapping, indent=2)}")

        # Extract values for mapped concepts
        fcff_data = {}
        common_years = None

        metrics_data = {}
        for metric, concept in concept_mapping.items():
            values = get_concept_value(company_facts, concept)
            if values:
                metrics_data[metric] = values
                years_set = set(values.keys())
                if common_years is None:
                    common_years = years_set
                else:
                    common_years &= years_set

        if not common_years:
            print("[LLM] No common years found across metrics")
            return None

        # Build FCFF data structure
        for year in sorted(common_years, reverse=True)[:years]:
            year_data = {}

            if 'ebit' in metrics_data and year in metrics_data['ebit']:
                year_data['ebit'] = metrics_data['ebit'][year]

            if 'tax_expense' in metrics_data and year in metrics_data['tax_expense']:
                year_data['tax_expense'] = metrics_data['tax_expense'][year]

            if 'depreciation_amortization' in metrics_data and year in metrics_data['depreciation_amortization']:
                year_data['depreciation_amortization'] = metrics_data['depreciation_amortization'][year]

            if 'capital_expenditures' in metrics_data and year in metrics_data['capital_expenditures']:
                # CapEx is usually negative in cash flow statement, make absolute
                year_data['capital_expenditures'] = abs(metrics_data['capital_expenditures'][year])

            if 'working_capital_change' in metrics_data and year in metrics_data['working_capital_change']:
                year_data['working_capital_change'] = metrics_data['working_capital_change'][year]

            # Only add year if we have core metrics
            if all(k in year_data for k in ['ebit', 'tax_expense', 'depreciation_amortization', 'capital_expenditures']):
                # Calculate FCFF
                fcff = (year_data['ebit'] -
                       year_data['tax_expense'] +
                       year_data['depreciation_amortization'] -
                       year_data['capital_expenditures'])

                if 'working_capital_change' in year_data:
                    fcff -= year_data['working_capital_change']

                year_data['fcff'] = fcff
                fcff_data[year] = year_data

        if not fcff_data:
            print("[LLM] No complete FCFF data extracted")
            return None

        print(f"[LLM] Successfully extracted {len(fcff_data)} years of FCFF data")
        return fcff_data

    except Exception as e:
        print(f"Error in LLM-based FCFF extraction for {ticker}: {e}")
        return None


if __name__ == "__main__":
    # Test LLM-based XBRL extraction
    print("Testing LLM-based XBRL concept mapping...")

    ticker = input("Enter stock ticker: ").upper()

    print(f"\nExtracting FCFF data for {ticker} using LLM...")
    fcff_data = extract_fcff_with_llm(ticker, years=5)

    if fcff_data:
        print(f"\n✓ Successfully extracted {len(fcff_data)} years of data")

        for year, data in sorted(fcff_data.items(), reverse=True):
            print(f"\n{year}:")
            for metric, value in data.items():
                print(f"  {metric}: ${value:,.0f}")
    else:
        print(f"\n✗ Failed to extract FCFF data for {ticker}")
