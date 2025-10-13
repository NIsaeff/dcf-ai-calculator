"""Main page for DCF Calculator Streamlit interface."""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional

def show_main_page():
    """Display the main FCFF calculation interface."""
    
    # Sidebar for inputs
    st.sidebar.header("Input Parameters")
    
    # Ticker input
    ticker = st.sidebar.text_input(
        "Stock Ticker Symbol",
        value="AAPL",
        help="Enter a stock ticker (e.g., AAPL, MSFT, GOOGL)"
    ).upper()
    
    # Data source selection
    data_source = st.sidebar.radio(
        "Data Source",
        options=["Yahoo Finance", "SEC EDGAR"],
        index=0,
        help="Choose your preferred data source"
    )
    
    # Number of years for analysis
    years = st.sidebar.slider(
        "Historical Years",
        min_value=3,
        max_value=10,
        value=5,
        help="Number of historical years to analyze"
    )
    
    # Main content area
    if st.sidebar.button("Analyze Company", type="primary"):
        if ticker:
            analyze_company(ticker, data_source, years)
        else:
            st.warning("Please enter a stock ticker symbol.")
    
    # Show sample data initially
    if 'analysis_done' not in st.session_state:
        show_sample_data()

def analyze_company(ticker: str, data_source: str, years: int):
    """Analyze company FCFF data."""
    
    st.session_state.analysis_done = True
    
    with st.spinner(f"Fetching {ticker} data from {data_source}..."):
        
        if data_source == "Yahoo Finance":
            fcff_data = get_yahoo_data(ticker, years)
        else:
            fcff_data = get_edgar_data(ticker, years)
        
        if fcff_data is not None:
            display_fcff_analysis(ticker, fcff_data, data_source)
        else:
            st.error(f"Could not retrieve data for {ticker} from {data_source}")

def get_yahoo_data(ticker: str, years: int) -> Optional[pd.DataFrame]:
    """Get Yahoo Finance data and convert to DataFrame."""
    try:
        from data.yahoofin_api import get_fcff_dataframe
        from core.fcff import convert_api_data_to_dataframe
        
        # Get raw data from Yahoo Finance
        raw_data = get_fcff_dataframe(ticker)
        if raw_data:
            # Convert to DataFrame using core module
            df = convert_api_data_to_dataframe(raw_data, source='yahoo')
            return df
        return None
    except Exception as e:
        st.error(f"Error fetching Yahoo Finance data: {e}")
        return None

def get_edgar_data(ticker: str, years: int) -> Optional[pd.DataFrame]:
    """Get EDGAR data and convert to DataFrame."""
    try:
        from data.edgar_api import get_edgar_fcff_dataframe
        from core.fcff import convert_api_data_to_dataframe
        
        # Get raw data from EDGAR
        raw_data = get_edgar_fcff_dataframe(ticker, years)
        if raw_data:
            # Convert to DataFrame using core module
            df = convert_api_data_to_dataframe(raw_data, source='edgar')
            return df
        return None
    except Exception as e:
        st.error(f"Error fetching EDGAR data: {e}")
        return None

def display_fcff_analysis(ticker: str, df: pd.DataFrame, data_source: str):
    """Display comprehensive FCFF analysis."""
    
    st.header(f"{ticker} - Free Cash Flow Analysis")
    st.caption(f"Data Source: {data_source}")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Financial Data", 
        "FCFF Trends", 
        "Growth Analysis", 
        "WACC Analysis",
        "DCF Valuation"
    ])
    
    with tab1:
        show_financial_data_tab(df)
    
    with tab2:
        show_fcff_trends_tab(ticker, df)
    
    with tab3:
        show_growth_analysis_tab(df)
    
    with tab4:
        show_wacc_analysis_tab(ticker, df)
    
    with tab5:
        show_dcf_valuation_tab(ticker, df)

def show_financial_data_tab(df: pd.DataFrame):
    """Show financial data in Excel DCF format (years as columns, line items as rows)."""
    st.subheader("Historical Financial Data")
    
    from core.formatting import format_financial_number
    
    # Transpose data to Excel DCF format: line items as rows, years as columns
    dcf_df = df.transpose()
    
    # Reorder rows to match typical DCF layout
    dcf_row_order = [
        'ebit',
        'tax_expense', 
        'depreciation_amortization',
        'capital_expenditures',
        'working_capital_change',
        'fcff'
    ]
    
    # Filter to only include available columns and reorder
    available_rows = [row for row in dcf_row_order if row in dcf_df.index]
    dcf_display = dcf_df.loc[available_rows]
    
    # Create proper DCF line item labels
    dcf_labels = {
        'ebit': 'EBIT (Operating Income)',
        'tax_expense': 'Less: Income Tax Expense',
        'depreciation_amortization': 'Add: Depreciation & Amortization', 
        'capital_expenditures': 'Less: Capital Expenditures',
        'working_capital_change': 'Less: Change in Working Capital',
        'fcff': 'Free Cash Flow to Firm (FCFF)'
    }
    
    # Rename index with proper labels
    dcf_display.index = [dcf_labels.get(idx, idx) for idx in dcf_display.index]
    
    # Determine appropriate scale for the data
    max_value = 0
    for col in dcf_display.columns:
        col_max = dcf_display[col].abs().max()
        if pd.notna(col_max):
            max_value = max(max_value, float(col_max))
    
    # Determine scale and format accordingly
    if max_value >= 1e9:  # Billions
        scale_factor = 1e9
        scale_label = "Billions"
        decimal_places = 2
    elif max_value >= 1e6:  # Millions  
        scale_factor = 1e6
        scale_label = "Millions"
        decimal_places = 1
    else:
        scale_factor = 1e3
        scale_label = "Thousands"
        decimal_places = 0
    
    # Scale the data and format
    dcf_scaled = dcf_display / scale_factor
    dcf_formatted = dcf_scaled.round(decimal_places)
    
    # Update column headers to show scale
    new_columns = {}
    for col in dcf_formatted.columns:
        new_columns[col] = f"{col} ($ {scale_label})"
    dcf_formatted = dcf_formatted.rename(columns=new_columns)
    
    # Display in Excel-like format
    st.dataframe(dcf_formatted, use_container_width=True)
    
    # Add calculation explanation
    with st.expander("FCFF Calculation Formula"):
        st.markdown("""
        **Free Cash Flow to Firm (FCFF) = EBIT - Tax Expense + D&A - CapEx - ΔWorking Capital**
        
        - **EBIT**: Earnings Before Interest and Tax (Operating Income)
        - **Tax Expense**: Corporate income tax payments
        - **D&A**: Non-cash Depreciation & Amortization (added back)
        - **CapEx**: Capital Expenditures (cash outflow for assets)
        - **ΔWC**: Change in Working Capital (increase reduces cash flow)
        """)
    
    # Key metrics summary - ordered by most recent year
    st.subheader("Key Financial Metrics")
    
    from core.formatting import format_financial_number
    
    # Get most recent year data
    latest_year = df.index[-1] if len(df) > 0 else "N/A"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        latest_fcff = df['fcff'].iloc[-1] if len(df) > 0 else 0
        st.metric(f"FCFF ({latest_year})", format_financial_number(latest_fcff))
    
    with col2:
        latest_ebit = df['ebit'].iloc[-1] if len(df) > 0 else 0
        st.metric(f"EBIT ({latest_year})", format_financial_number(latest_ebit))
    
    with col3:
        latest_capex = df['capital_expenditures'].iloc[-1] if len(df) > 0 else 0
        st.metric(f"CapEx ({latest_year})", format_financial_number(latest_capex))
    
    with col4:
        avg_fcff = df['fcff'].mean() if len(df) > 0 else 0
        st.metric("Avg FCFF", format_financial_number(avg_fcff))

def show_fcff_trends_tab(ticker: str, df: pd.DataFrame):
    """Show FCFF trends and charts in Excel DCF format."""
    st.subheader(f"{ticker} Free Cash Flow Analysis")
    
    # Sort by year for proper time series
    df_sorted = df.sort_index()
    
    # Determine scale for charts
    max_fcff = df_sorted['fcff'].abs().max()
    if max_fcff >= 1e9:
        chart_scale = 1e9
        scale_label = "Billions"
    elif max_fcff >= 1e6:
        chart_scale = 1e6
        scale_label = "Millions"
    else:
        chart_scale = 1e3
        scale_label = "Thousands"
    
    # FCFF trend line chart
    st.subheader(f"FCFF Trend Over Time ($ {scale_label})")
    fcff_chart_data = (df_sorted[['fcff']] / chart_scale).copy()
    fcff_chart_data.columns = [f'FCFF ($ {scale_label})']
    fcff_chart_data.index = fcff_chart_data.index.astype(str)
    st.line_chart(fcff_chart_data, height=400)
    
    # Waterfall-style component analysis
    st.subheader("FCFF Build-up Analysis")
    
    # Create waterfall data showing how we get from EBIT to FCFF
    years = df_sorted.index.tolist()
    
    # Show component trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Operating Performance ($ {scale_label})**")
        operating_data = (df_sorted[['ebit', 'tax_expense']] / chart_scale).copy()
        operating_data.columns = ['EBIT', 'Tax Expense']
        operating_data.index = operating_data.index.astype(str)
        st.bar_chart(operating_data, height=300)
    
    with col2:
        st.write(f"**Cash Flow Adjustments ($ {scale_label})**")
        adjustments_data = (df_sorted[['depreciation_amortization', 'capital_expenditures']] / chart_scale).copy()
        adjustments_data.columns = ['D&A (Add)', 'CapEx (Subtract)']
        # Make CapEx negative for visual clarity
        adjustments_data['CapEx (Subtract)'] = -adjustments_data['CapEx (Subtract)']
        adjustments_data.index = adjustments_data.index.astype(str)
        st.bar_chart(adjustments_data, height=300)
    
    # Year-over-year change analysis
    st.subheader("Year-over-Year Changes")
    
    if len(df_sorted) > 1:
        # Calculate YoY changes
        yoy_changes = df_sorted.pct_change().dropna()
        
        # Format as percentages
        yoy_display = yoy_changes[['ebit', 'fcff']].copy()
        yoy_display.columns = ['EBIT Change', 'FCFF Change']
        
        # Format each column properly
        for col in yoy_display.columns:
            yoy_display[col] = [f"{x:.1%}" if pd.notna(x) else "N/A" for x in yoy_display[col]]
        
        yoy_display.index = yoy_display.index.astype(str)
        st.dataframe(yoy_display, use_container_width=True)
    else:
        st.info("Need at least 2 years of data for year-over-year analysis.")

def show_growth_analysis_tab(df: pd.DataFrame):
    """Show growth rate analysis."""
    st.subheader("FCFF Growth Analysis")
    
    try:
        from core.fcff import calculate_fcff_growth_rates, calculate_average_fcff_growth
        
        fcff_series = pd.Series(df['fcff'].values, index=df.index)
        growth_rates = calculate_fcff_growth_rates(fcff_series)
        avg_growth = calculate_average_fcff_growth(fcff_series)
        
        # Display growth metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Average Growth Rate", f"{avg_growth:.2%}")
        
        with col2:
            latest_growth = growth_rates.iloc[-1] if len(growth_rates) > 1 else 0
            st.metric("Latest YoY Growth", f"{latest_growth:.2%}")
        
        # Growth rates table
        st.subheader("Year-over-Year Growth Rates")
        growth_df = pd.DataFrame({
            'Year': growth_rates.index,
            'FCFF Growth Rate': growth_rates.values
        })
        growth_df = growth_df.dropna()
        growth_df['FCFF Growth Rate'] = growth_df['FCFF Growth Rate'].apply(lambda x: f"{x:.2%}")
        
        st.dataframe(growth_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error calculating growth rates: {e}")

def show_projections_tab(df: pd.DataFrame):
    """Show future FCFF projections."""
    st.subheader("Future FCFF Projections")
    
    try:
        from core.fcff import project_future_fcff
        
        # User inputs for projections
        col1, col2 = st.columns(2)
        
        with col1:
            projection_years = st.slider("Projection Years", 3, 10, 5)
        
        with col2:
            custom_growth = st.number_input(
                "Custom Growth Rate (%)", 
                value=None, 
                format="%.2f",
                help="Leave empty to use calculated average growth"
            )
        
        # Calculate projections
        fcff_series = pd.Series(df['fcff'].values, index=df.index)
        growth_rate = custom_growth / 100 if custom_growth is not None else None
        
        projections_df = project_future_fcff(
            fcff_series, 
            projection_years=projection_years,
            growth_rate=growth_rate
        )
        
        # Display projections
        st.subheader("Projected FCFF Values")
        
        # Format for display
        display_projections = projections_df.copy()
        display_projections['projected_fcff'] = display_projections['projected_fcff'].apply(
            lambda x: f"${x:,.0f}"
        )
        display_projections['growth_rate'] = display_projections['growth_rate'].apply(
            lambda x: f"{x:.2%}"
        )
        
        st.dataframe(display_projections, use_container_width=True)
        
        # Create Excel-style projection table with historical + projected
        st.subheader("Excel DCF Model - Historical & Projected")
        
        # Combine historical and projected for Excel-style view
        all_years = list(df.index.astype(str)) + list(projections_df.index.astype(str))
        
        # Create comprehensive projection table
        projection_data = {
            'Metric': ['FCFF (Historical)', 'FCFF (Projected)', 'Growth Rate']
        }
        
        # Add historical years
        for year in df.index.astype(str):
            projection_data[year] = [
                f"${df.loc[year, 'fcff']:,.0f}",
                "-",
                "-"
            ]
        
        # Add projected years
        for year in projections_df.index.astype(str):
            projection_data[year] = [
                "-",
                f"${projections_df.loc[year, 'projected_fcff']:,.0f}",
                f"{projections_df.loc[year, 'growth_rate']:.1%}"
            ]
        
        projection_table = pd.DataFrame(projection_data)
        projection_table = projection_table.set_index('Metric')
        
        st.dataframe(projection_table, use_container_width=True)
        
        # Combined time series chart
        st.subheader("Complete FCFF Timeline")
        
        # Create combined dataset for seamless chart
        historical_data = df[['fcff']].copy()
        historical_data.columns = ['FCFF']
        
        projected_data = projections_df[['projected_fcff']].copy()
        projected_data.columns = ['FCFF']
        
        combined_data = pd.concat([historical_data, projected_data])
        combined_data.index = combined_data.index.astype(str)
        
        st.line_chart(combined_data, height=400)
        
    except Exception as e:
        st.error(f"Error generating projections: {e}")

def show_wacc_analysis_tab(ticker: str, df: pd.DataFrame):
    """Show WACC calculation and analysis."""
    st.subheader(f"{ticker} WACC Analysis")
    
    try:
        from core.wacc import calculate_wacc, wacc_sensitivity_analysis
        
        # Calculate WACC
        with st.spinner("Calculating WACC..."):
            wacc_data = calculate_wacc(ticker)
        
        # Display WACC results
        col1, col2 = st.columns(2)
        
        from core.formatting import format_percentage, format_financial_number
        
        with col1:
            st.subheader("WACC Components")
            st.metric("WACC", format_percentage(wacc_data['wacc']))
            st.metric("Cost of Equity", format_percentage(wacc_data['cost_of_equity']))
            st.metric("Cost of Debt", format_percentage(wacc_data['cost_of_debt']))
            st.metric("Beta", f"{wacc_data['beta']:.2f}")
        
        with col2:
            st.subheader("Capital Structure")
            st.metric("Equity Weight", format_percentage(wacc_data['weight_equity']))
            st.metric("Debt Weight", format_percentage(wacc_data['weight_debt']))
            st.metric("Risk-free Rate", format_percentage(wacc_data['risk_free_rate']))
            st.metric("Market Risk Premium", format_percentage(wacc_data['market_risk_premium']))
            st.metric("Market Cap", format_financial_number(wacc_data['market_cap']))
            st.metric("Total Debt", format_financial_number(wacc_data['total_debt']))
        
        # WACC breakdown chart
        st.subheader("WACC Composition")
        wacc_components = pd.DataFrame({
            'Component': ['Cost of Equity', 'Cost of Debt'],
            'Weight': [wacc_data['weight_equity'], wacc_data['weight_debt']],
            'Rate': [wacc_data['cost_of_equity'], wacc_data['cost_of_debt']],
            'Contribution': [
                wacc_data['weight_equity'] * wacc_data['cost_of_equity'],
                wacc_data['weight_debt'] * wacc_data['cost_of_debt']
            ]
        })
        
        # Format percentages for table display (not abbreviated)
        for col in ['Weight', 'Rate', 'Contribution']:
            wacc_components[col] = wacc_components[col].apply(lambda x: f"{x:.2%}")
        
        st.dataframe(wacc_components, use_container_width=True, hide_index=True)
        
        # Sensitivity analysis
        st.subheader("WACC Sensitivity Analysis")
        sensitivity_df = wacc_sensitivity_analysis(ticker, wacc_data)
        
        # Group by parameter for better display
        for param in sensitivity_df['Parameter'].unique():
            param_data = sensitivity_df[sensitivity_df['Parameter'] == param]
            st.write(f"**{param.replace('_', ' ').title()}:**")
            
            cols = st.columns(3)
            for i, (_, row) in enumerate(param_data.iterrows()):
                with cols[i]:
                    change_str = f"({row['Change_from_Base']:+.2%})" if row['Change_from_Base'] != 0 else ""
                    st.metric(
                        row['Scenario'], 
                        f"{row['WACC']:.2%}",
                        delta=change_str
                    )
        
    except Exception as e:
        st.error(f"Error calculating WACC: {e}")

def show_dcf_valuation_tab(ticker: str, df: pd.DataFrame):
    """Show complete DCF valuation with terminal value."""
    st.subheader(f"{ticker} DCF Valuation")
    
    try:
        from core.wacc import calculate_wacc
        from core.growth_rates import forecast_multi_stage_growth
        from core.dcf_valuation import perform_dcf_valuation, dcf_sensitivity_analysis
        from core.fcff import project_future_fcff
        
        # Get WACC
        wacc_data = calculate_wacc(ticker)
        
        # User inputs for DCF
        st.subheader("DCF Assumptions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            projection_years = st.slider("Projection Years", 3, 10, 5)
            terminal_growth = st.number_input(
                "Terminal Growth Rate (%)",
                min_value=0.0,
                max_value=5.0,
                value=2.5,
                step=0.1,
                format="%.1f"
            ) / 100
        
        with col2:
            custom_wacc = st.number_input(
                "Custom WACC (%)", 
                min_value=5.0,
                max_value=20.0,
                value=wacc_data['wacc'] * 100,
                step=0.1,
                format="%.1f"
            ) / 100
            
            shares_outstanding = st.number_input(
                "Shares Outstanding (millions)",
                min_value=1.0,
                value=1000.0,
                step=1.0,
                format="%.0f"
            ) * 1_000_000
        
        with col3:
            industry_sector = st.selectbox(
                "Industry Sector",
                ['Technology', 'Healthcare', 'Consumer Discretionary', 
                 'Financials', 'Consumer Staples', 'Utilities', 
                 'Energy', 'Materials', 'Industrials', 
                 'Communication Services', 'Real Estate']
            )
        
        # Calculate projections with advanced growth model
        fcff_series = pd.Series(df['fcff'].values, index=df.index)
        
        # Use multi-stage growth forecast
        growth_forecast = forecast_multi_stage_growth(
            historical_fcff=fcff_series,
            industry_sector=industry_sector,
            high_growth_years=min(projection_years, 5),
            transition_years=max(0, projection_years - 5)
        )
        
        # Create projected FCFF using growth rates
        latest_year = max(fcff_series.index)
        latest_fcff = fcff_series[latest_year]
        
        projected_data = []
        current_fcff = latest_fcff
        
        for i, growth_rate in enumerate(growth_forecast['growth_rates']):
            year = int(latest_year) + i + 1
            current_fcff = current_fcff * (1 + growth_rate)
            projected_data.append({
                'year': str(year),
                'projected_fcff': current_fcff,
                'growth_rate': growth_rate
            })
        
        projections_df = pd.DataFrame(projected_data)
        projections_df = projections_df.set_index('year')
        
        # Update WACC in wacc_data
        wacc_data['wacc'] = custom_wacc
        
        # Perform DCF valuation
        valuation_results = perform_dcf_valuation(
            projected_fcff=projections_df,
            wacc_data=wacc_data,
            terminal_growth_rate=terminal_growth,
            shares_outstanding=shares_outstanding
        )
        
        from core.formatting import format_financial_number, format_percentage
        
        # Display valuation results
        st.subheader("Valuation Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Enterprise Value", format_financial_number(valuation_results['enterprise_value']))
        
        with col2:
            st.metric("Equity Value", format_financial_number(valuation_results['equity_value']))
        
        with col3:
            st.metric("Value per Share", format_financial_number(valuation_results['value_per_share']))
        
        with col4:
            st.metric("Terminal Value %", format_percentage(valuation_results['terminal_value_percentage']))
        
        # DCF breakdown
        st.subheader("DCF Value Breakdown")
        
        breakdown_data = pd.DataFrame({
            'Component': ['Operating Cash Flows (PV)', 'Terminal Value (PV)', 'Enterprise Value', 'Less: Net Debt', 'Equity Value'],
            'Value': [
                valuation_results['pv_operating_cash_flows'],
                valuation_results['pv_terminal_value'],
                valuation_results['enterprise_value'],
                -valuation_results['net_debt'],
                valuation_results['equity_value']
            ]
        })
        
        # Determine scale for breakdown table
        max_breakdown_value = max([abs(x) for x in breakdown_data['Value']])
        if max_breakdown_value >= 1e9:
            breakdown_scale = 1e9
            breakdown_scale_label = "Billions"
        elif max_breakdown_value >= 1e6:
            breakdown_scale = 1e6
            breakdown_scale_label = "Millions"
        else:
            breakdown_scale = 1e3
            breakdown_scale_label = "Thousands"
        
        # Scale the breakdown values
        breakdown_data['Value ($ ' + breakdown_scale_label + ')'] = (breakdown_data['Value'] / breakdown_scale).round(2)
        breakdown_display = breakdown_data[['Component', 'Value ($ ' + breakdown_scale_label + ')']].copy()
        
        st.dataframe(breakdown_display, use_container_width=True, hide_index=True)
        
        # Sensitivity analysis
        st.subheader("DCF Sensitivity Analysis")
        st.write("Value per Share sensitivity to WACC and Terminal Growth Rate")
        
        sensitivity_matrix = dcf_sensitivity_analysis(
            projected_fcff=projections_df,
            wacc_base=custom_wacc,
            terminal_growth_base=terminal_growth,
            shares_outstanding=shares_outstanding,
            wacc_range=(custom_wacc * 0.8, custom_wacc * 1.2),
            growth_range=(terminal_growth * 0.5, terminal_growth * 1.5),
            steps=5
        )
        
        st.dataframe(sensitivity_matrix, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error performing DCF valuation: {e}")

def show_sample_data():
    """Show sample data when no analysis has been run."""
    st.info("Enter a stock ticker in the sidebar and click 'Analyze Company' to get started!")
    
    st.subheader("About This Tool")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Features:**
        - Historical FCFF calculation
        - Trend analysis and visualization
        - Growth rate calculations
        - Future cash flow projections
        - Data from Yahoo Finance & SEC EDGAR
        """)
    
    with col2:
        st.markdown("""
        **FCFF Formula:**
        ```
        FCFF = EBIT - Tax Expense + D&A - CapEx - ΔWC
        ```
        
        **Sample Tickers to Try:**
        - AAPL (Apple)
        - MSFT (Microsoft) 
        - GOOGL (Google)
        - TSLA (Tesla)
        """)
