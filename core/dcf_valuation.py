"""Complete DCF valuation with terminal value and present value calculations."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

def calculate_terminal_value(final_year_fcff: float,
                           terminal_growth_rate: float,
                           wacc: float,
                           method: str = 'gordon') -> float:
    """Calculate terminal value using Gordon Growth Model or Exit Multiple.
    
    Args:
        final_year_fcff: FCFF in the final projection year
        terminal_growth_rate: Long-term growth rate
        wacc: Weighted Average Cost of Capital
        method: 'gordon' for Gordon Growth Model, 'multiple' for exit multiple
        
    Returns:
        Terminal value
    """
    if method == 'gordon':
        # Gordon Growth Model: TV = FCF(n+1) / (WACC - g)
        if wacc <= terminal_growth_rate:
            raise ValueError("WACC must be greater than terminal growth rate")
        
        # FCF in year n+1
        fcf_next_year = final_year_fcff * (1 + terminal_growth_rate)
        terminal_value = fcf_next_year / (wacc - terminal_growth_rate)
        
        return terminal_value
    
    elif method == 'multiple':
        # Exit Multiple Method (typically 10-15x final year FCFF)
        exit_multiple = 12.0  # Conservative 12x multiple
        return final_year_fcff * exit_multiple
    
    else:
        raise ValueError("Method must be 'gordon' or 'multiple'")

def calculate_present_value(cash_flows: List[float],
                           discount_rate: float,
                           periods: Optional[List[int]] = None) -> List[float]:
    """Calculate present value of cash flows.
    
    Args:
        cash_flows: List of future cash flows
        discount_rate: Discount rate (WACC)
        periods: List of periods (default: 1, 2, 3, ...)
        
    Returns:
        List of present values
    """
    if periods is None:
        periods = list(range(1, len(cash_flows) + 1))
    
    if len(cash_flows) != len(periods):
        raise ValueError("Cash flows and periods must have same length")
    
    present_values = []
    for cf, period in zip(cash_flows, periods):
        pv = cf / ((1 + discount_rate) ** period)
        present_values.append(pv)
    
    return present_values

def perform_dcf_valuation(projected_fcff: pd.DataFrame,
                         wacc_data: Dict[str, float],
                         terminal_growth_rate: float = 0.025,
                         shares_outstanding: Optional[float] = None) -> Dict[str, float]:
    """Perform complete DCF valuation.
    
    Args:
        projected_fcff: DataFrame with projected FCFF values
        wacc_data: Dictionary with WACC calculation results
        terminal_growth_rate: Long-term growth rate for terminal value
        shares_outstanding: Number of shares outstanding
        
    Returns:
        Dictionary with DCF valuation results
    """
    wacc = wacc_data['wacc']
    
    # Extract projected cash flows
    if 'projected_fcff' in projected_fcff.columns:
        cash_flows = projected_fcff['projected_fcff'].tolist()
    elif 'fcff' in projected_fcff.columns:
        cash_flows = projected_fcff['fcff'].tolist()
    else:
        raise ValueError("No FCFF column found in projected data")
    
    # Calculate terminal value
    final_year_fcff = cash_flows[-1]
    terminal_value = calculate_terminal_value(
        final_year_fcff,
        terminal_growth_rate,
        wacc
    )
    
    # Create cash flow schedule including terminal value
    projection_years = len(cash_flows)
    all_cash_flows = cash_flows + [terminal_value]
    periods = list(range(1, projection_years + 1)) + [projection_years]
    
    # Calculate present values
    present_values = calculate_present_value(all_cash_flows, wacc, periods)
    
    # Separate operating and terminal value PVs
    pv_operating_cash_flows = sum(present_values[:-1])
    pv_terminal_value = present_values[-1]
    
    # Total enterprise value
    enterprise_value = pv_operating_cash_flows + pv_terminal_value
    
    # Calculate equity value (EV - Net Debt)
    net_debt = wacc_data.get('total_debt', 0) - wacc_data.get('cash', 0)
    equity_value = enterprise_value - net_debt
    
    # Calculate per-share value
    if shares_outstanding and shares_outstanding > 0:
        value_per_share = equity_value / shares_outstanding
    else:
        value_per_share = None
    
    return {
        'enterprise_value': enterprise_value,
        'pv_operating_cash_flows': pv_operating_cash_flows,
        'pv_terminal_value': pv_terminal_value,
        'terminal_value': terminal_value,
        'equity_value': equity_value,
        'net_debt': net_debt,
        'value_per_share': value_per_share,
        'wacc': wacc,
        'terminal_growth_rate': terminal_growth_rate,
        'terminal_value_percentage': pv_terminal_value / enterprise_value if enterprise_value > 0 else 0
    }

def create_dcf_summary_table(historical_fcff: pd.DataFrame,
                           projected_fcff: pd.DataFrame,
                           valuation_results: Dict[str, float],
                           wacc_data: Dict[str, float]) -> pd.DataFrame:
    """Create comprehensive DCF summary table.
    
    Args:
        historical_fcff: Historical FCFF data
        projected_fcff: Projected FCFF data
        valuation_results: DCF valuation results
        wacc_data: WACC calculation data
        
    Returns:
        DataFrame with complete DCF model summary
    """
    # Combine historical and projected years
    hist_years = list(historical_fcff.index.astype(str))
    proj_years = list(projected_fcff.index.astype(str))
    all_years = hist_years + proj_years
    
    # Initialize summary data
    metrics = [
        'FCFF (Historical)',
        'FCFF (Projected)', 
        'Present Value of FCFF',
        'Terminal Value',
        'Present Value of Terminal Value',
        'Enterprise Value',
        'Less: Net Debt',
        'Equity Value',
        'WACC',
        'Terminal Growth Rate'
    ]
    
    summary_data = {'Metric': metrics}
    
    # Add historical FCFF
    for year in hist_years:
        hist_fcff = historical_fcff.loc[year, 'fcff'] if year in historical_fcff.index else None
        summary_data[year] = [
            f"${hist_fcff:,.0f}" if hist_fcff else "-",
            "-", "-", "-", "-", "-", "-", "-", "-", "-"
        ]
    
    # Add projected FCFF and calculations
    discount_rate = valuation_results['wacc']
    
    for i, year in enumerate(proj_years):
        proj_fcff = projected_fcff.loc[year, 'projected_fcff'] if 'projected_fcff' in projected_fcff.columns else projected_fcff.loc[year, 'fcff']
        
        # Calculate present value of this year's FCFF
        period = i + 1
        pv_fcff = proj_fcff / ((1 + discount_rate) ** period)
        
        year_data = [
            "-",  # Historical FCFF
            f"${proj_fcff:,.0f}",  # Projected FCFF
            f"${pv_fcff:,.0f}",  # Present Value
            "-", "-", "-", "-", "-", "-", "-"
        ]
        
        # Add terminal value in final year
        if i == len(proj_years) - 1:
            terminal_value = valuation_results['terminal_value']
            pv_terminal = valuation_results['pv_terminal_value']
            enterprise_value = valuation_results['enterprise_value']
            net_debt = valuation_results['net_debt']
            equity_value = valuation_results['equity_value']
            wacc = valuation_results['wacc']
            terminal_growth = valuation_results['terminal_growth_rate']
            
            year_data[3] = f"${terminal_value:,.0f}"  # Terminal Value
            year_data[4] = f"${pv_terminal:,.0f}"     # PV Terminal Value
            year_data[5] = f"${enterprise_value:,.0f}"  # Enterprise Value
            year_data[6] = f"${net_debt:,.0f}"        # Net Debt
            year_data[7] = f"${equity_value:,.0f}"    # Equity Value
            year_data[8] = f"{wacc:.2%}"              # WACC
            year_data[9] = f"{terminal_growth:.2%}"   # Terminal Growth
        
        summary_data[year] = year_data
    
    # Create DataFrame and set index
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.set_index('Metric')
    
    return summary_df

def dcf_sensitivity_analysis(projected_fcff: pd.DataFrame,
                           wacc_base: float,
                           terminal_growth_base: float,
                           shares_outstanding: float,
                           wacc_range: Tuple[float, float] = (0.06, 0.12),
                           growth_range: Tuple[float, float] = (0.01, 0.04),
                           steps: int = 5) -> pd.DataFrame:
    """Perform DCF sensitivity analysis on WACC and terminal growth rate.
    
    Args:
        projected_fcff: DataFrame with projected FCFF
        wacc_base: Base case WACC
        terminal_growth_base: Base case terminal growth rate
        shares_outstanding: Number of shares outstanding
        wacc_range: Range of WACC values to test
        growth_range: Range of terminal growth rates to test
        steps: Number of steps in each range
        
    Returns:
        DataFrame with sensitivity analysis results
    """
    # Create ranges
    wacc_values = np.linspace(wacc_range[0], wacc_range[1], steps)
    growth_values = np.linspace(growth_range[0], growth_range[1], steps)
    
    # Initialize results matrix
    wacc_labels = [f"{w:.1%}" for w in wacc_values]
    growth_labels = [f"{g:.1%}" for g in growth_values]
    sensitivity_results = pd.DataFrame(
        index=pd.Index(wacc_labels),
        columns=pd.Index(growth_labels)
    )
    
    # Calculate value per share for each combination
    cash_flows = projected_fcff['projected_fcff'].tolist() if 'projected_fcff' in projected_fcff.columns else projected_fcff['fcff'].tolist()
    
    for i, wacc in enumerate(wacc_values):
        for j, terminal_growth in enumerate(growth_values):
            try:
                # Calculate terminal value
                final_fcff = cash_flows[-1]
                terminal_value = calculate_terminal_value(final_fcff, terminal_growth, wacc)
                
                # Calculate present values
                all_cash_flows = cash_flows + [terminal_value]
                periods = list(range(1, len(cash_flows) + 1)) + [len(cash_flows)]
                present_values = calculate_present_value(all_cash_flows, wacc, periods)
                
                # Enterprise and equity value
                enterprise_value = sum(present_values)
                equity_value = enterprise_value  # Simplified (no debt adjustment)
                value_per_share = equity_value / shares_outstanding
                
                sensitivity_results.iloc[i, j] = f"${value_per_share:.2f}"
                
            except (ValueError, ZeroDivisionError):
                sensitivity_results.iloc[i, j] = "N/A"
    
    return sensitivity_results

if __name__ == "__main__":
    # Test DCF valuation
    print("Testing DCF valuation calculations...")
    
    # Sample projected FCFF
    projected_data = pd.DataFrame({
        'projected_fcff': [30_000_000, 35_000_000, 40_000_000, 45_000_000, 50_000_000]
    }, index=['2025', '2026', '2027', '2028', '2029'])
    
    # Sample WACC data
    wacc_data = {
        'wacc': 0.10,
        'total_debt': 100_000_000,
        'cash': 20_000_000
    }
    
    # Perform DCF valuation
    valuation = perform_dcf_valuation(
        projected_fcff=projected_data,
        wacc_data=wacc_data,
        terminal_growth_rate=0.025,
        shares_outstanding=100_000_000
    )
    
    print(f"\nDCF Valuation Results:")
    print(f"Enterprise Value: ${valuation['enterprise_value']:,.0f}")
    print(f"PV Operating Cash Flows: ${valuation['pv_operating_cash_flows']:,.0f}")
    print(f"PV Terminal Value: ${valuation['pv_terminal_value']:,.0f}")
    print(f"Terminal Value %: {valuation['terminal_value_percentage']:.1%}")
    print(f"Equity Value: ${valuation['equity_value']:,.0f}")
    print(f"Value per Share: ${valuation['value_per_share']:.2f}")
    
    # Test sensitivity analysis
    print(f"\nSensitivity Analysis:")
    sensitivity = dcf_sensitivity_analysis(
        projected_data,
        wacc_data['wacc'],
        0.025,
        100_000_000,
        wacc_range=(0.08, 0.12),
        growth_range=(0.015, 0.035),
        steps=3
    )
    print(sensitivity)