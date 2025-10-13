"""Weighted Average Cost of Capital (WACC) calculations for DCF valuation."""

import pandas as pd
import numpy as np
import requests
from typing import Dict, Optional, Tuple
import yfinance as yf

def get_risk_free_rate() -> float:
    """Get current 10-year Treasury rate as risk-free rate.
    
    Returns:
        10-year Treasury yield as decimal
    """
    try:
        # Use Federal Reserve Economic Data (FRED) for 10-year Treasury
        # Alternative: yfinance for ^TNX (10-year Treasury yield)
        treasury = yf.Ticker("^TNX")
        hist = treasury.history(period="5d")
        if not hist.empty:
            latest_yield = hist['Close'].iloc[-1] / 100  # Convert percentage to decimal
            return float(latest_yield)
    except:
        pass
    
    # Fallback to reasonable estimate
    return 0.045  # 4.5% default assumption

def get_market_risk_premium() -> float:
    """Get equity market risk premium.
    
    Returns:
        Market risk premium as decimal (typically 5-7%)
    """
    # Historical equity risk premium (market return - risk-free rate)
    # Conservative estimate based on long-term historical data
    return 0.06  # 6% market risk premium

def calculate_beta(ticker: str, market_ticker: str = "^GSPC", period: str = "2y") -> float:
    """Calculate stock beta against market index.
    
    Args:
        ticker: Stock ticker symbol
        market_ticker: Market index ticker (default S&P 500)
        period: Period for beta calculation
        
    Returns:
        Beta coefficient
    """
    try:
        # Get stock and market data
        stock = yf.Ticker(ticker)
        market = yf.Ticker(market_ticker)
        
        # Get historical returns
        stock_hist = stock.history(period=period)
        market_hist = market.history(period=period)
        
        if stock_hist.empty or market_hist.empty:
            return 1.0  # Default beta
        
        # Calculate daily returns
        stock_returns = stock_hist['Close'].pct_change().dropna()
        market_returns = market_hist['Close'].pct_change().dropna()
        
        # Align dates
        common_dates = stock_returns.index.intersection(market_returns.index)
        if len(common_dates) < 50:  # Need sufficient data points
            return 1.0
        
        stock_aligned = stock_returns.loc[common_dates]
        market_aligned = market_returns.loc[common_dates]
        
        # Calculate beta using covariance/variance
        covariance = np.cov(stock_aligned, market_aligned)[0, 1]
        market_variance = np.var(market_aligned)
        
        if market_variance == 0:
            return 1.0
        
        beta = covariance / market_variance
        
        # Cap beta at reasonable bounds
        return float(max(0.1, min(beta, 3.0)))
        
    except Exception as e:
        print(f"Error calculating beta for {ticker}: {e}")
        return 1.0  # Default beta

def calculate_cost_of_equity(ticker: str, 
                           risk_free_rate: Optional[float] = None,
                           market_risk_premium: Optional[float] = None,
                           beta: Optional[float] = None) -> Dict[str, float]:
    """Calculate cost of equity using CAPM model.
    
    Args:
        ticker: Stock ticker symbol
        risk_free_rate: Risk-free rate (if None, fetched automatically)
        market_risk_premium: Market risk premium (if None, uses default)
        beta: Stock beta (if None, calculated automatically)
        
    Returns:
        Dictionary with cost of equity components and result
    """
    # Get or calculate components
    if risk_free_rate is None:
        risk_free_rate = get_risk_free_rate()
    
    if market_risk_premium is None:
        market_risk_premium = get_market_risk_premium()
    
    if beta is None:
        beta = calculate_beta(ticker)
    
    # CAPM: Cost of Equity = Risk-free Rate + Beta × Market Risk Premium
    cost_of_equity = risk_free_rate + (beta * market_risk_premium)
    
    return {
        'risk_free_rate': risk_free_rate,
        'beta': beta,
        'market_risk_premium': market_risk_premium,
        'cost_of_equity': cost_of_equity
    }

def get_financial_data_for_wacc(ticker: str) -> Dict[str, float]:
    """Get financial data needed for WACC calculation.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with market cap, debt, cash, interest expense
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get basic info
        info = stock.info
        
        # Get balance sheet
        balance_sheet = stock.balance_sheet
        
        # Get income statement for interest expense
        income_stmt = stock.financials
        
        result = {}
        
        # Market capitalization
        result['market_cap'] = info.get('marketCap', 0)
        
        # Total debt (if available)
        if not balance_sheet.empty:
            # Try different debt line items
            debt_items = ['Total Debt', 'Long Term Debt', 'Short Long Term Debt', 'Net Debt']
            total_debt = 0
            
            for item in debt_items:
                if item in balance_sheet.index:
                    debt_value = balance_sheet.loc[item].iloc[0]  # Most recent
                    if pd.notna(debt_value):
                        total_debt += abs(debt_value)
                        break
            
            result['total_debt'] = total_debt
            
            # Cash and equivalents
            cash_items = ['Cash And Cash Equivalents', 'Cash', 'Cash And Short Term Investments']
            cash = 0
            for item in cash_items:
                if item in balance_sheet.index:
                    cash_value = balance_sheet.loc[item].iloc[0]
                    if pd.notna(cash_value):
                        cash = abs(cash_value)
                        break
            
            result['cash'] = cash
        else:
            result['total_debt'] = 0
            result['cash'] = 0
        
        # Interest expense
        if not income_stmt.empty:
            interest_items = ['Interest Expense', 'Interest Expense Non Operating', 'Net Interest Income']
            interest_expense = 0
            
            for item in interest_items:
                if item in income_stmt.index:
                    interest_value = income_stmt.loc[item].iloc[0]
                    if pd.notna(interest_value):
                        interest_expense = abs(interest_value)
                        break
            
            result['interest_expense'] = interest_expense
        else:
            result['interest_expense'] = 0
        
        return result
        
    except Exception as e:
        print(f"Error getting financial data for {ticker}: {e}")
        return {
            'market_cap': 0,
            'total_debt': 0,
            'cash': 0,
            'interest_expense': 0
        }

def calculate_cost_of_debt(ticker: str, 
                          total_debt: float,
                          interest_expense: float,
                          tax_rate: float = 0.21) -> float:
    """Calculate after-tax cost of debt.
    
    Args:
        ticker: Stock ticker symbol
        total_debt: Total debt amount
        interest_expense: Annual interest expense
        tax_rate: Corporate tax rate
        
    Returns:
        After-tax cost of debt as decimal
    """
    if total_debt <= 0:
        return 0.0
    
    # Pre-tax cost of debt = Interest Expense / Total Debt
    pre_tax_cost = interest_expense / total_debt
    
    # After-tax cost of debt = Pre-tax cost × (1 - Tax Rate)
    after_tax_cost = pre_tax_cost * (1 - tax_rate)
    
    # Cap at reasonable bounds
    return max(0.0, min(after_tax_cost, 0.15))  # 0-15% range

def calculate_wacc(ticker: str,
                  tax_rate: float = 0.21,
                  custom_inputs: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Calculate Weighted Average Cost of Capital (WACC).
    
    Args:
        ticker: Stock ticker symbol
        tax_rate: Corporate tax rate (default 21% US federal rate)
        custom_inputs: Optional dictionary to override calculated values
        
    Returns:
        Dictionary with WACC calculation components and result
    """
    # Get cost of equity
    equity_data = calculate_cost_of_equity(ticker)
    cost_of_equity = equity_data['cost_of_equity']
    
    # Get financial data
    financial_data = get_financial_data_for_wacc(ticker)
    
    # Apply custom inputs if provided
    if custom_inputs:
        financial_data.update(custom_inputs)
    
    # Calculate cost of debt
    cost_of_debt = calculate_cost_of_debt(
        ticker,
        financial_data['total_debt'],
        financial_data['interest_expense'],
        tax_rate
    )
    
    # Calculate weights
    market_value_equity = financial_data['market_cap']
    market_value_debt = financial_data['total_debt']  # Approximate with book value
    total_value = market_value_equity + market_value_debt
    
    if total_value <= 0:
        # All equity company
        weight_equity = 1.0
        weight_debt = 0.0
    else:
        weight_equity = market_value_equity / total_value
        weight_debt = market_value_debt / total_value
    
    # WACC = (E/V × Cost of Equity) + (D/V × Cost of Debt × (1 - Tax Rate))
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt)
    
    return {
        'wacc': wacc,
        'cost_of_equity': cost_of_equity,
        'cost_of_debt': cost_of_debt,
        'weight_equity': weight_equity,
        'weight_debt': weight_debt,
        'market_cap': market_value_equity,
        'total_debt': market_value_debt,
        'tax_rate': tax_rate,
        'beta': equity_data['beta'],
        'risk_free_rate': equity_data['risk_free_rate'],
        'market_risk_premium': equity_data['market_risk_premium']
    }

def wacc_sensitivity_analysis(ticker: str,
                            wacc_base: Dict[str, float],
                            sensitivity_ranges: Optional[Dict[str, Tuple[float, float]]] = None) -> pd.DataFrame:
    """Perform sensitivity analysis on WACC calculation.
    
    Args:
        ticker: Stock ticker symbol
        wacc_base: Base WACC calculation result
        sensitivity_ranges: Ranges for sensitivity analysis
        
    Returns:
        DataFrame with sensitivity analysis results
    """
    if sensitivity_ranges is None:
        sensitivity_ranges = {
            'beta': (0.8, 1.2),
            'risk_free_rate': (0.03, 0.06),
            'market_risk_premium': (0.05, 0.08),
            'cost_of_debt': (0.02, 0.08)
        }
    
    results = []
    
    for parameter, (low, high) in sensitivity_ranges.items():
        for scenario, value in [('Low', low), ('Base', wacc_base.get(parameter, 0)), ('High', high)]:
            # Create modified inputs
            modified_inputs = wacc_base.copy()
            modified_inputs[parameter] = value
            
            # Recalculate WACC with modified parameter
            if parameter in ['beta', 'risk_free_rate', 'market_risk_premium']:
                # Recalculate cost of equity
                cost_of_equity = modified_inputs['risk_free_rate'] + (
                    modified_inputs['beta'] * modified_inputs['market_risk_premium']
                )
                modified_inputs['cost_of_equity'] = cost_of_equity
            
            # Recalculate WACC
            wacc_new = (
                modified_inputs['weight_equity'] * modified_inputs['cost_of_equity'] +
                modified_inputs['weight_debt'] * modified_inputs['cost_of_debt']
            )
            
            results.append({
                'Parameter': parameter,
                'Scenario': scenario,
                'Value': value,
                'WACC': wacc_new,
                'Change_from_Base': wacc_new - wacc_base['wacc']
            })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Test WACC calculations
    ticker = "AAPL"
    print(f"Testing WACC calculation for {ticker}...")
    
    # Calculate WACC
    wacc_result = calculate_wacc(ticker)
    
    from core.formatting import format_percentage, format_financial_number
    
    print(f"\nWACC Components:")
    print(f"Risk-free Rate: {format_percentage(wacc_result['risk_free_rate'])}")
    print(f"Beta: {wacc_result['beta']:.2f}")
    print(f"Market Risk Premium: {format_percentage(wacc_result['market_risk_premium'])}")
    print(f"Cost of Equity: {format_percentage(wacc_result['cost_of_equity'])}")
    print(f"Cost of Debt: {format_percentage(wacc_result['cost_of_debt'])}")
    print(f"Weight Equity: {format_percentage(wacc_result['weight_equity'])}")
    print(f"Weight Debt: {format_percentage(wacc_result['weight_debt'])}")
    print(f"Market Cap: {format_financial_number(wacc_result['market_cap'])}")
    print(f"Total Debt: {format_financial_number(wacc_result['total_debt'])}")
    print(f"WACC: {format_percentage(wacc_result['wacc'])}")
    
    # Test sensitivity analysis
    print(f"\nSensitivity Analysis:")
    sensitivity_df = wacc_sensitivity_analysis(ticker, wacc_result)
    for param in sensitivity_df['Parameter'].unique():
        param_data = sensitivity_df[sensitivity_df['Parameter'] == param]
        print(f"\n{param}:")
        for _, row in param_data.iterrows():
            print(f"  {row['Scenario']}: {format_percentage(row['WACC'])} (Δ{format_percentage(row['Change_from_Base'], decimal_places=2)})")