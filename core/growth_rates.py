"""Growth rate forecasting for DCF projections."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

def calculate_revenue_growth_rate(revenue_series: pd.Series, method: str = 'geometric') -> float:
    """Calculate revenue growth rate from historical data.
    
    Args:
        revenue_series: Series of revenue values indexed by year
        method: 'arithmetic', 'geometric', or 'regression'
        
    Returns:
        Average annual growth rate as decimal
    """
    if len(revenue_series) < 2:
        return 0.0
    
    sorted_series = revenue_series.sort_index()
    growth_rates = sorted_series.pct_change().dropna()
    
    if len(growth_rates) == 0:
        return 0.0
    
    if method == 'geometric':
        # CAGR calculation
        years = len(sorted_series) - 1
        if years <= 0:
            return 0.0
        cagr = (sorted_series.iloc[-1] / sorted_series.iloc[0]) ** (1/years) - 1
        return float(cagr)
    
    elif method == 'regression':
        # Linear regression on log values
        years = np.arange(len(sorted_series))
        log_values = np.log(sorted_series.values)
        
        # Remove any infinite or NaN values
        valid_mask = np.isfinite(log_values)
        if np.sum(valid_mask) < 2:
            return 0.0
            
        years_valid = years[valid_mask]
        log_values_valid = log_values[valid_mask]
        
        slope = np.polyfit(years_valid, log_values_valid, 1)[0]
        return float(np.exp(slope) - 1)
    
    else:  # arithmetic
        return float(growth_rates.mean())

def estimate_industry_growth_rate(industry_sector: str = 'Technology') -> float:
    """Estimate industry growth rate based on sector.
    
    Args:
        industry_sector: Industry sector name
        
    Returns:
        Estimated long-term growth rate
    """
    # Conservative industry growth estimates (annual)
    industry_rates = {
        'Technology': 0.08,        # 8%
        'Healthcare': 0.06,        # 6%
        'Consumer Discretionary': 0.05,  # 5%
        'Financials': 0.04,        # 4%
        'Consumer Staples': 0.03,  # 3%
        'Utilities': 0.025,        # 2.5%
        'Energy': 0.02,            # 2%
        'Materials': 0.03,         # 3%
        'Industrials': 0.04,       # 4%
        'Communication Services': 0.05,  # 5%
        'Real Estate': 0.03        # 3%
    }
    
    return industry_rates.get(industry_sector, 0.03)  # Default 3%

def calculate_gdp_plus_growth() -> float:
    """Calculate GDP+ growth rate for terminal value.
    
    Returns:
        Conservative long-term GDP+ growth rate
    """
    # US long-term GDP growth + inflation expectation
    gdp_growth = 0.02      # 2% real GDP growth
    inflation = 0.025      # 2.5% inflation target
    return gdp_growth + inflation

def forecast_multi_stage_growth(historical_fcff: pd.Series,
                               revenue_series: Optional[pd.Series] = None,
                               industry_sector: str = 'Technology',
                               high_growth_years: int = 5,
                               transition_years: int = 5) -> Dict[str, List[float]]:
    """Create multi-stage growth forecast for DCF.
    
    Args:
        historical_fcff: Historical FCFF data
        revenue_series: Historical revenue data (optional)
        industry_sector: Company's industry sector
        high_growth_years: Years of high growth phase
        transition_years: Years of transition to terminal growth
        
    Returns:
        Dictionary with growth rates by phase
    """
    # Phase 1: High Growth (based on historical performance)
    if revenue_series is not None and len(revenue_series) >= 3:
        historical_growth = calculate_revenue_growth_rate(revenue_series, method='geometric')
        # Cap at reasonable maximum and apply conservatism
        phase1_growth = min(max(historical_growth * 0.8, 0.02), 0.15)  # 2-15% range
    else:
        # Fallback to FCFF growth if no revenue data
        from core.fcff import calculate_average_fcff_growth
        fcff_growth = calculate_average_fcff_growth(historical_fcff, method='geometric')
        phase1_growth = min(max(fcff_growth * 0.7, 0.02), 0.12)  # More conservative
    
    # Phase 2: Transition (gradual decline to terminal)
    terminal_growth = calculate_gdp_plus_growth()
    industry_growth = estimate_industry_growth_rate(industry_sector)
    
    # Create growth rate schedule
    growth_schedule = {
        'years': list(range(1, high_growth_years + transition_years + 1)),
        'growth_rates': [],
        'phase': []
    }
    
    # High growth phase
    for year in range(1, high_growth_years + 1):
        growth_schedule['growth_rates'].append(phase1_growth)
        growth_schedule['phase'].append('High Growth')
    
    # Transition phase (linear decline to terminal)
    if transition_years > 0:
        decline_per_year = (phase1_growth - terminal_growth) / transition_years
        for year in range(transition_years):
            transition_rate = phase1_growth - (decline_per_year * (year + 1))
            growth_schedule['growth_rates'].append(max(transition_rate, terminal_growth))
            growth_schedule['phase'].append('Transition')
    
    return growth_schedule

def apply_growth_scenarios(base_growth_schedule: Dict[str, List[float]],
                          scenario_adjustments: Dict[str, float]) -> Dict[str, Dict[str, List[float]]]:
    """Apply different growth scenarios for sensitivity analysis.
    
    Args:
        base_growth_schedule: Base case growth rates
        scenario_adjustments: Multipliers for each scenario
        
    Returns:
        Dictionary of growth schedules by scenario
    """
    scenarios = {}
    
    for scenario_name, multiplier in scenario_adjustments.items():
        scenario_schedule = {
            'years': base_growth_schedule['years'].copy(),
            'growth_rates': [rate * multiplier for rate in base_growth_schedule['growth_rates']],
            'phase': base_growth_schedule['phase'].copy()
        }
        scenarios[scenario_name] = scenario_schedule
    
    return scenarios

def validate_growth_assumptions(growth_rates: List[float], 
                              industry_sector: str = 'Technology') -> Tuple[bool, List[str]]:
    """Validate growth rate assumptions for reasonableness.
    
    Args:
        growth_rates: List of projected growth rates
        industry_sector: Industry sector for benchmarking
        
    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []
    is_valid = True
    
    # Check for negative terminal growth
    if growth_rates[-1] < 0:
        warnings.append("Terminal growth rate is negative")
        is_valid = False
    
    # Check for excessive growth rates
    max_reasonable = 0.25  # 25%
    if any(rate > max_reasonable for rate in growth_rates):
        warnings.append(f"Growth rates exceed {max_reasonable:.0%} threshold")
    
    # Check terminal growth vs GDP
    terminal_rate = growth_rates[-1]
    gdp_growth = calculate_gdp_plus_growth()
    if terminal_rate > gdp_growth * 1.5:
        warnings.append(f"Terminal growth ({terminal_rate:.1%}) significantly exceeds GDP+ growth")
    
    # Industry-specific checks
    industry_benchmark = estimate_industry_growth_rate(industry_sector)
    avg_growth = np.mean(growth_rates)
    if avg_growth > industry_benchmark * 2:
        warnings.append(f"Average growth rate exceeds industry benchmark by 2x")
    
    return is_valid, warnings

if __name__ == "__main__":
    # Test growth rate calculations
    print("Testing growth rate forecasting...")
    
    # Sample revenue data
    revenue_data = pd.Series({
        '2020': 100_000_000,
        '2021': 115_000_000,
        '2022': 135_000_000,
        '2023': 150_000_000,
        '2024': 175_000_000
    })
    
    # Test revenue growth calculation
    revenue_growth = calculate_revenue_growth_rate(revenue_data, method='geometric')
    print(f"Revenue CAGR: {revenue_growth:.2%}")
    
    # Sample FCFF data
    fcff_data = pd.Series({
        '2020': 15_000_000,
        '2021': 18_000_000,
        '2022': 22_000_000,
        '2023': 25_000_000,
        '2024': 30_000_000
    })
    
    # Test multi-stage growth forecast
    growth_forecast = forecast_multi_stage_growth(
        historical_fcff=fcff_data,
        revenue_series=revenue_data,
        industry_sector='Technology',
        high_growth_years=5,
        transition_years=5
    )
    
    print(f"\nMulti-stage Growth Forecast:")
    for i, (year, rate, phase) in enumerate(zip(
        growth_forecast['years'], 
        growth_forecast['growth_rates'],
        growth_forecast['phase']
    )):
        print(f"Year {year}: {rate:.2%} ({phase})")
    
    # Test scenarios
    scenarios = apply_growth_scenarios(growth_forecast, {
        'Bull Case': 1.25,
        'Bear Case': 0.75,
        'Base Case': 1.0
    })
    
    print(f"\nScenario Analysis:")
    for scenario, schedule in scenarios.items():
        avg_rate = np.mean(schedule['growth_rates'])
        print(f"{scenario}: Avg {avg_rate:.2%}")
    
    # Test validation
    is_valid, warnings = validate_growth_assumptions(
        growth_forecast['growth_rates'],
        'Technology'
    )
    
    print(f"\nValidation: {'PASS' if is_valid else 'WARNINGS'}")
    for warning in warnings:
        print(f"  - {warning}")