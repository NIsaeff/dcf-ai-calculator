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
    tab1, tab2, tab3, tab4 = st.tabs([
        "Financial Data", 
        "FCFF Trends", 
        "Growth Analysis", 
        "Projections"
    ])
    
    with tab1:
        show_financial_data_tab(df)
    
    with tab2:
        show_fcff_trends_tab(ticker, df)
    
    with tab3:
        show_growth_analysis_tab(df)
    
    with tab4:
        show_projections_tab(df)

def show_financial_data_tab(df: pd.DataFrame):
    """Show financial data in Excel DCF format (years as columns, line items as rows)."""
    st.subheader("Historical Financial Data")
    
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
    
    # Format all values as currency
    dcf_formatted = dcf_display.copy()
    for col in dcf_formatted.columns:
        dcf_formatted[col] = dcf_formatted[col].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
        )
    
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
    
    # Get most recent year data
    latest_year = df.index[-1] if len(df) > 0 else "N/A"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        latest_fcff = df['fcff'].iloc[-1] if len(df) > 0 else 0
        st.metric(f"FCFF ({latest_year})", f"${latest_fcff:,.0f}")
    
    with col2:
        latest_ebit = df['ebit'].iloc[-1] if len(df) > 0 else 0
        st.metric(f"EBIT ({latest_year})", f"${latest_ebit:,.0f}")
    
    with col3:
        latest_capex = df['capital_expenditures'].iloc[-1] if len(df) > 0 else 0
        st.metric(f"CapEx ({latest_year})", f"${latest_capex:,.0f}")
    
    with col4:
        avg_fcff = df['fcff'].mean() if len(df) > 0 else 0
        st.metric("Avg FCFF", f"${avg_fcff:,.0f}")

def show_fcff_trends_tab(ticker: str, df: pd.DataFrame):
    """Show FCFF trends and charts in Excel DCF format."""
    st.subheader(f"{ticker} Free Cash Flow Analysis")
    
    # Sort by year for proper time series
    df_sorted = df.sort_index()
    
    # FCFF trend line chart
    st.subheader("FCFF Trend Over Time")
    fcff_chart_data = df_sorted[['fcff']].copy()
    fcff_chart_data.index = fcff_chart_data.index.astype(str)
    st.line_chart(fcff_chart_data, height=400)
    
    # Waterfall-style component analysis
    st.subheader("FCFF Build-up Analysis")
    
    # Create waterfall data showing how we get from EBIT to FCFF
    years = df_sorted.index.tolist()
    
    # Show component trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Operating Performance**")
        operating_data = df_sorted[['ebit', 'tax_expense']].copy()
        operating_data.columns = ['EBIT', 'Tax Expense']
        operating_data.index = operating_data.index.astype(str)
        st.bar_chart(operating_data, height=300)
    
    with col2:
        st.write("**Cash Flow Adjustments**")
        adjustments_data = df_sorted[['depreciation_amortization', 'capital_expenditures']].copy()
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
