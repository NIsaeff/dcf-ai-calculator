"""Financial number formatting utilities for DCF Calculator."""

import pandas as pd
import numpy as np
from typing import Union, Optional

def format_financial_number(value: Union[float, int], 
                           currency: bool = True,
                           significant_figures: int = 3) -> str:
    """Format financial numbers with M, B, T notation and 3 significant figures.
    
    Args:
        value: Number to format
        currency: Whether to include $ symbol
        significant_figures: Number of significant figures to display
        
    Returns:
        Formatted string (e.g., "$1.23B", "456M", "7.89T")
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    currency_symbol = "$" if currency else ""
    
    # Handle zero and very small numbers
    if abs_value == 0:
        return f"{sign}{currency_symbol}0"
    
    if abs_value < 1000:
        if abs_value >= 100:
            formatted = f"{value:.0f}"
        elif abs_value >= 10:
            formatted = f"{value:.1f}"
        else:
            formatted = f"{value:.2f}"
        return f"{sign}{currency_symbol}{formatted}"
    
    # Determine scale and suffix
    if abs_value >= 1e12:  # Trillions
        scaled_value = value / 1e12
        suffix = "T"
    elif abs_value >= 1e9:  # Billions
        scaled_value = value / 1e9
        suffix = "B"
    elif abs_value >= 1e6:  # Millions
        scaled_value = value / 1e6
        suffix = "M"
    elif abs_value >= 1e3:  # Thousands
        scaled_value = value / 1e3
        suffix = "K"
    else:
        scaled_value = value
        suffix = ""
    
    # Format to 3 significant figures
    abs_scaled = abs(scaled_value)
    
    if abs_scaled >= 100:
        formatted_number = f"{scaled_value:.0f}"
    elif abs_scaled >= 10:
        formatted_number = f"{scaled_value:.1f}"
    else:
        formatted_number = f"{scaled_value:.2f}"
    
    return f"{currency_symbol}{formatted_number}{suffix}"

def format_percentage(value: Union[float, int], 
                     decimal_places: int = 1) -> str:
    """Format percentage values.
    
    Args:
        value: Decimal value (e.g., 0.1523 for 15.23%)
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    percentage = value * 100
    return f"{percentage:.{decimal_places}f}%"

def format_multiple(value: Union[float, int], 
                   decimal_places: int = 1,
                   suffix: str = "x") -> str:
    """Format multiple values (e.g., P/E ratios, EV/EBITDA).
    
    Args:
        value: Multiple value
        decimal_places: Number of decimal places
        suffix: Suffix to append (default "x")
        
    Returns:
        Formatted multiple string
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    return f"{value:.{decimal_places}f}{suffix}"

def determine_scale_and_format_dataframe(df: pd.DataFrame, 
                                       currency_columns: Optional[list] = None) -> tuple[pd.DataFrame, str]:
    """Determine appropriate scale for DataFrame and format accordingly.
    
    Args:
        df: DataFrame to analyze and format
        currency_columns: Columns containing currency values
        
    Returns:
        Tuple of (formatted_dataframe, scale_description)
    """
    if currency_columns is None:
        currency_columns = [
            'ebit', 'tax_expense', 'depreciation_amortization', 
            'capital_expenditures', 'working_capital_change', 'fcff',
            'projected_fcff'
        ]
    
    # Find maximum absolute value across all currency columns
    max_value = 0
    for col in currency_columns:
        if col in df.columns and len(df[col]) > 0:
            try:
                col_max = df[col].abs().max()
                if pd.notna(col_max) and col_max > 0:
                    max_value = max(max_value, float(col_max))
            except:
                continue
    
    # Determine appropriate scale
    if max_value >= 1e9:  # Billions
        scale_factor = 1e9
        scale_label = "$ Billions"
        decimal_places = 2
    elif max_value >= 1e6:  # Millions  
        scale_factor = 1e6
        scale_label = "$ Millions"
        decimal_places = 1
    elif max_value >= 1e3:  # Thousands
        scale_factor = 1e3
        scale_label = "$ Thousands"
        decimal_places = 0
    else:
        scale_factor = 1
        scale_label = "$"
        decimal_places = 0
    
    # Format DataFrame
    formatted_df = df.copy()
    for col in currency_columns:
        if col in formatted_df.columns:
            formatted_df[col] = (formatted_df[col] / scale_factor).round(decimal_places)
    
    return formatted_df, scale_label

def format_financial_dataframe(df: pd.DataFrame, 
                              currency_columns: Optional[list] = None,
                              percentage_columns: Optional[list] = None,
                              multiple_columns: Optional[list] = None,
                              use_abbreviated: bool = False) -> pd.DataFrame:
    """Format entire DataFrame with financial number formatting.
    
    Args:
        df: DataFrame to format
        currency_columns: List of columns to format as currency
        percentage_columns: List of columns to format as percentages
        multiple_columns: List of columns to format as multiples
        
    Returns:
        DataFrame with formatted values
    """
    formatted_df = df.copy()
    
    # Default financial columns if not specified
    if currency_columns is None:
        currency_columns = [
            'ebit', 'tax_expense', 'depreciation_amortization', 
            'capital_expenditures', 'working_capital_change', 'fcff',
            'projected_fcff', 'enterprise_value', 'equity_value',
            'market_cap', 'total_debt', 'cash', 'net_debt',
            'pv_operating_cash_flows', 'pv_terminal_value', 'terminal_value'
        ]
    
    if percentage_columns is None:
        percentage_columns = [
            'growth_rate', 'wacc', 'cost_of_equity', 'cost_of_debt',
            'weight_equity', 'weight_debt', 'risk_free_rate', 
            'market_risk_premium', 'terminal_growth_rate'
        ]
    
    # Format currency columns
    for col in currency_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(
                lambda x: format_financial_number(x) if pd.notna(x) else "N/A"
            )
    
    # Format percentage columns
    for col in percentage_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(
                lambda x: format_percentage(x) if pd.notna(x) else "N/A"
            )
    
    # Format multiple columns
    if multiple_columns:
        for col in multiple_columns:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: format_multiple(x) if pd.notna(x) else "N/A"
                )
    
    return formatted_df

def format_dcf_summary_row(label: str, value: Union[float, int, str]) -> dict:
    """Format a single row for DCF summary display.
    
    Args:
        label: Row label
        value: Value to format
        
    Returns:
        Dictionary with label and formatted value
    """
    if isinstance(value, str):
        formatted_value = value
    elif 'percentage' in label.lower() or 'rate' in label.lower() or 'wacc' in label.lower():
        formatted_value = format_percentage(value)
    elif 'multiple' in label.lower() or 'ratio' in label.lower():
        formatted_value = format_multiple(value)
    else:
        formatted_value = format_financial_number(value)
    
    return {
        'Metric': label,
        'Value': formatted_value
    }

def create_financial_metrics_display(metrics_dict: dict) -> pd.DataFrame:
    """Create formatted display DataFrame from metrics dictionary.
    
    Args:
        metrics_dict: Dictionary of metric names and values
        
    Returns:
        Formatted DataFrame for display
    """
    rows = []
    for label, value in metrics_dict.items():
        rows.append(format_dcf_summary_row(label, value))
    
    return pd.DataFrame(rows)

if __name__ == "__main__":
    # Test formatting functions
    print("Testing financial number formatting...")
    
    test_values = [
        1234567890,      # Billions
        123456789,       # Hundreds of millions
        12345678,        # Tens of millions
        1234567,         # Millions
        123456,          # Hundreds of thousands
        12345,           # Tens of thousands
        1234,            # Thousands
        123,             # Hundreds
        12.34,           # Tens
        1.234,           # Units
        0.1234,          # Decimals
        0,               # Zero
        -1234567890      # Negative
    ]
    
    print("\nCurrency formatting:")
    for value in test_values:
        formatted = format_financial_number(value, currency=True)
        print(f"{value:>12} -> {formatted}")
    
    print("\nPercentage formatting:")
    percentage_values = [0.1523, 0.0234, 0.001, 0.9876, 1.234, -0.0567]
    for value in percentage_values:
        formatted = format_percentage(value)
        print(f"{value:>8} -> {formatted}")
    
    print("\nDataFrame formatting test:")
    test_df = pd.DataFrame({
        'ebit': [100_000_000, 250_000_000, 500_000_000],
        'fcff': [50_000_000, 125_000_000, 300_000_000],
        'growth_rate': [0.15, 0.12, 0.08],
        'wacc': [0.10, 0.095, 0.11]
    }, index=['2023', '2024', '2025'])
    
    formatted_df = format_financial_dataframe(test_df)
    print(formatted_df)