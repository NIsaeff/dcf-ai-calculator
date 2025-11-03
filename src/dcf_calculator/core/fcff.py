"""Free Cash Flow to Firm (FCFF) calculations using pandas and numpy."""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Union, List

def calculate_fcff_single_year(ebit: float, tax_expense: float, 
                              depreciation_amortization: float, 
                              capital_expenditures: float,
                              working_capital_change: Optional[float] = 0.0) -> float:
    """Calculate FCFF for a single year.
    
    FCFF = EBIT - Tax Expense + D&A - CapEx - Change in Working Capital
    
    Args:
        ebit: Earnings Before Interest and Tax
        tax_expense: Income tax expense
        depreciation_amortization: Depreciation and amortization
        capital_expenditures: Capital expenditures (positive value)
        working_capital_change: Change in working capital (optional, default 0)
        
    Returns:
        Free Cash Flow to Firm
    """
    wc_change = working_capital_change if working_capital_change is not None else 0.0
    return ebit - tax_expense + depreciation_amortization - capital_expenditures - wc_change

def calculate_fcff_series(financial_data: pd.DataFrame) -> pd.Series:
    """Calculate FCFF for multiple years using pandas DataFrame.
    
    Args:
        financial_data: DataFrame with columns:
            - ebit
            - tax_expense
            - depreciation_amortization
            - capital_expenditures
            - working_capital_change (optional)
            
    Returns:
        Series with FCFF values indexed by original DataFrame index
    """
    # Handle missing working capital change
    if 'working_capital_change' not in financial_data.columns:
        financial_data = financial_data.copy()
        financial_data['working_capital_change'] = 0.0
    
    # Fill NaN values with 0 for working capital change only
    wc_change = financial_data['working_capital_change'].fillna(0.0)
    
    fcff = (financial_data['ebit'] - 
            financial_data['tax_expense'] + 
            financial_data['depreciation_amortization'] - 
            financial_data['capital_expenditures'] - 
            wc_change)
    
    return fcff

def create_fcff_dataframe(years: List[str], 
                         ebit_values: List[float],
                         tax_values: List[float],
                         da_values: List[float],
                         capex_values: List[float],
                         wc_change_values: Optional[List[float]] = None) -> pd.DataFrame:
    """Create a DataFrame with financial data and calculate FCFF.
    
    Args:
        years: List of year strings
        ebit_values: List of EBIT values
        tax_values: List of tax expense values
        da_values: List of depreciation & amortization values
        capex_values: List of capital expenditure values
        wc_change_values: Optional list of working capital change values
        
    Returns:
        DataFrame with financial components and calculated FCFF
    """
    if wc_change_values is None:
        wc_change_values = [0.0] * len(years)
    
    df = pd.DataFrame({
        'year': years,
        'ebit': ebit_values,
        'tax_expense': tax_values,
        'depreciation_amortization': da_values,
        'capital_expenditures': capex_values,
        'working_capital_change': wc_change_values
    })
    
    df.set_index('year', inplace=True)
    df['fcff'] = calculate_fcff_series(df)
    
    return df

def convert_api_data_to_dataframe(api_data: Dict, source: str = 'yahoo') -> Optional[pd.DataFrame]:
    """Convert API data dictionary to standardized DataFrame format.
    
    Args:
        api_data: Dictionary from Yahoo Finance or EDGAR API
        source: Data source ('yahoo' or 'edgar')
        
    Returns:
        DataFrame with standardized column names or None if conversion fails
    """
    try:
        if source == 'yahoo' and api_data:
            # Convert Yahoo Finance historical data format
            years = list(api_data.keys())
            
            ebit_vals = []
            tax_vals = []
            da_vals = []
            capex_vals = []
            wc_vals = []
            
            for year in years:
                year_data = api_data[year]
                ebit_vals.append(year_data.get('ebit'))
                tax_vals.append(year_data.get('tax_expense'))
                da_vals.append(year_data.get('depreciation_amortization'))
                capex_vals.append(year_data.get('capital_expenditures'))
                wc_vals.append(year_data.get('working_capital_change', 0.0))
            
            # Filter out years with missing critical data
            valid_data = []
            for i, year in enumerate(years):
                if all(val is not None for val in [ebit_vals[i], tax_vals[i], da_vals[i], capex_vals[i]]):
                    valid_data.append({
                        'year': year,
                        'ebit': ebit_vals[i],
                        'tax_expense': tax_vals[i],
                        'depreciation_amortization': da_vals[i],
                        'capital_expenditures': capex_vals[i],
                        'working_capital_change': wc_vals[i] if wc_vals[i] is not None else 0.0
                    })
            
            if valid_data:
                df = pd.DataFrame(valid_data)
                df.set_index('year', inplace=True)
                df['fcff'] = calculate_fcff_series(df)
                return df
                
        elif source == 'edgar' and api_data:
            # Convert EDGAR data format
            years = list(api_data.keys())
            
            data_rows = []
            for year in years:
                year_data = api_data[year]
                if all(key in year_data for key in ['ebit', 'tax_expense', 'depreciation_amortization', 'capital_expenditures']):
                    data_rows.append({
                        'year': year,
                        'ebit': year_data['ebit'],
                        'tax_expense': year_data['tax_expense'],
                        'depreciation_amortization': year_data['depreciation_amortization'],
                        'capital_expenditures': year_data['capital_expenditures'],
                        'working_capital_change': 0.0  # EDGAR simple version doesn't include WC
                    })
            
            if data_rows:
                df = pd.DataFrame(data_rows)
                df.set_index('year', inplace=True)
                df['fcff'] = calculate_fcff_series(df)
                return df
        
        return None
        
    except Exception as e:
        print(f"Error converting {source} API data: {e}")
        return None

def calculate_fcff_growth_rates(fcff_series: pd.Series) -> pd.Series:
    """Calculate year-over-year growth rates for FCFF.
    
    Args:
        fcff_series: Series of FCFF values indexed by year
        
    Returns:
        Series of growth rates (as decimals, e.g. 0.15 = 15%)
    """
    # Sort by year to ensure proper order
    sorted_series = fcff_series.sort_index()
    growth_rates = sorted_series.pct_change()
    return growth_rates

def calculate_average_fcff_growth(fcff_series: pd.Series, method: str = 'arithmetic') -> float:
    """Calculate average FCFF growth rate.
    
    Args:
        fcff_series: Series of FCFF values indexed by year
        method: 'arithmetic' or 'geometric' mean
        
    Returns:
        Average growth rate as decimal
    """
    growth_rates = calculate_fcff_growth_rates(fcff_series)
    # Remove first year (NaN) and any infinite values
    valid_growth = growth_rates.dropna().replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(valid_growth) == 0:
        return 0.0
    
    if method == 'geometric':
        # Geometric mean: (1 + r1) * (1 + r2) * ... * (1 + rn) ^ (1/n) - 1
        product = np.prod(1 + valid_growth)
        return float(np.power(product, 1/len(valid_growth)) - 1)
    else:
        # Arithmetic mean
        return float(valid_growth.mean())

def project_future_fcff(historical_fcff: pd.Series, 
                       projection_years: int = 5,
                       growth_rate: Optional[float] = None,
                       terminal_growth_rate: float = 0.025) -> pd.DataFrame:
    """Project future FCFF based on historical data.
    
    Args:
        historical_fcff: Series of historical FCFF values
        projection_years: Number of years to project
        growth_rate: Custom growth rate (if None, calculated from historical data)
        terminal_growth_rate: Long-term growth rate for terminal value
        
    Returns:
        DataFrame with projected FCFF values
    """
    if growth_rate is None:
        growth_rate = calculate_average_fcff_growth(historical_fcff, method='arithmetic')
    
    # Get the most recent FCFF value
    latest_year = max(historical_fcff.index)
    latest_fcff = historical_fcff[latest_year]
    
    # Create projection years
    start_year = int(latest_year) + 1
    projection_data = []
    
    current_fcff = latest_fcff
    for i in range(projection_years):
        year = start_year + i
        current_fcff = current_fcff * (1 + growth_rate)
        projection_data.append({
            'year': str(year),
            'projected_fcff': current_fcff,
            'growth_rate': growth_rate if i < projection_years - 1 else terminal_growth_rate
        })
    
    df = pd.DataFrame(projection_data)
    df.set_index('year', inplace=True)
    
    return df

if __name__ == "__main__":
    # Test the FCFF calculations
    print("Testing FCFF calculations...")
    
    # Test single year calculation
    fcff_2023 = calculate_fcff_single_year(
        ebit=50000,
        tax_expense=12000,
        depreciation_amortization=8000,
        capital_expenditures=15000,
        working_capital_change=2000
    )
    print(f"Single year FCFF: ${fcff_2023:,.0f}")
    
    # Test DataFrame creation
    test_data = create_fcff_dataframe(
        years=['2021', '2022', '2023'],
        ebit_values=[45000, 48000, 50000],
        tax_values=[10000, 11000, 12000],
        da_values=[7000, 7500, 8000],
        capex_values=[12000, 14000, 15000],
        wc_change_values=[1000, 1500, 2000]
    )
    
    print("\nDataFrame with FCFF calculations:")
    print(test_data)
    
    # Test growth rate calculations
    fcff_series = pd.Series(test_data['fcff'])
    growth_rates = calculate_fcff_growth_rates(fcff_series)
    avg_growth = calculate_average_fcff_growth(fcff_series)
    
    print(f"\nGrowth rates:\n{growth_rates}")
    print(f"Average growth rate: {avg_growth:.2%}")
    
    # Test projections
    projections = project_future_fcff(fcff_series, projection_years=3)
    print(f"\nProjected FCFF:\n{projections}")