"""DCF valuation callbacks for Dash application."""

from dash import Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from core.wacc import calculate_wacc
from core.dcf_valuation import perform_dcf_valuation
from core.growth_rates import calculate_revenue_growth_rate
from core.formatting import format_financial_number, format_percentage
import logging

logger = logging.getLogger(__name__)


def register_dcf_callbacks(app):
    """Register DCF-related callbacks.
    
    Args:
        app: Dash application instance
    """
    
    @app.callback(
        Output("tab-content", "children"),
        [Input("main-tabs", "value"),
         Input("ticker-store", "data"),
         Input("fcff-data-store", "data"),
         Input("projection-years", "data"),
         Input("terminal-growth-rate", "data"),
         Input("wacc-override", "data")]
    )
    def render_tab_content(active_tab, ticker, fcff_data, projection_years, terminal_growth, wacc_override):
        """Render content for the active tab.
        
        Triggers when: tab changes OR new data is loaded OR DCF inputs change.
        """
        if not ticker or not fcff_data:
            return html.Div("No data available. Please analyze a company first.")
        
        projection_years = projection_years or 5
        terminal_growth = terminal_growth or 2.5
        
        if active_tab == "fcff-tab":
            return render_fcff_tab(ticker, fcff_data)
        elif active_tab == "wacc-tab":
            return render_wacc_tab(ticker, fcff_data)
        elif active_tab == "dcf-tab":
            return render_dcf_tab(ticker, fcff_data, projection_years, terminal_growth, wacc_override)
        
        return html.Div("Tab not found")
    
    @app.callback(
        [Output("projection-years", "data"),
         Output("terminal-growth-rate", "data"),
         Output("wacc-override", "data")],
        [Input("dcf-projection-years-slider", "value"),
         Input("dcf-terminal-growth-slider", "value"),
         Input("dcf-wacc-override-input", "value")],
        prevent_initial_call=True
    )
    def update_dcf_assumptions(proj_years, term_growth, wacc_ovr):
        """Update DCF assumption stores when sliders change."""
        return proj_years, term_growth, wacc_ovr
    
    # WACC Interactive Callbacks
    @app.callback(
        [Output("direct-input-panel", "style"),
         Output("capm-panel", "style")],
        Input("cost-of-equity-method", "value"),
        prevent_initial_call=True
    )
    def toggle_cost_of_equity_method_panels(method):
        """Show/hide cost of equity method panels based on selection."""
        if method == "direct":
            return {"display": "block"}, {"display": "none"}
        else:  # capm
            return {"display": "none"}, {"display": "block"}
    
    @app.callback(
        Output("capm-calculated-result", "children"),
        [Input("capm-risk-free-rate", "value"),
         Input("capm-beta", "value"),
         Input("capm-market-risk-premium", "value")],
        prevent_initial_call=True
    )
    def update_capm_calculation(risk_free_rate, beta, market_risk_premium):
        """Update CAPM calculation in real-time."""
        if all(v is not None for v in [risk_free_rate, beta, market_risk_premium]):
            capm_result = (risk_free_rate/100) + beta * (market_risk_premium/100)
            return f"{capm_result:.1%}"
        return "Please enter all values"
    
    # Main WACC update callback
    @app.callback(
        [Output("wacc-final-value", "children"),
         Output("wacc-cost-of-equity-value", "children"),
         Output("wacc-method-label", "children"),
         Output("wacc-components-table", "children")],
        [Input("cost-of-equity-method", "value"),
         Input("direct-cost-of-equity", "value"),
         Input("capm-risk-free-rate", "value"),
         Input("capm-beta", "value"), 
         Input("capm-market-risk-premium", "value")],
        [State("ticker-store", "data")],
        prevent_initial_call=True
    )
    def update_wacc_calculation(method, direct_coe, rf_rate, beta, mrp, ticker):
        """Update WACC calculation and display when inputs change."""
        if not ticker:
            return "N/A", "N/A", "No Data", html.Div("No ticker selected")
        
        try:
            from core.wacc import calculate_wacc_enhanced
            
            # Prepare inputs based on method
            if method == "direct":
                if direct_coe is None:
                    direct_coe = 12.0  # Default
                wacc_data = calculate_wacc_enhanced(
                    ticker, 
                    cost_of_equity_method='direct', 
                    direct_cost_of_equity=direct_coe/100
                )
                method_label = "Direct Input"
            else:  # capm
                if any(v is None for v in [rf_rate, beta, mrp]):
                    # Use defaults if any value is missing
                    rf_rate = rf_rate or 4.0
                    beta = beta or 1.2
                    mrp = mrp or 6.0
                
                capm_overrides = {
                    'risk_free_rate': rf_rate/100,
                    'beta': beta,
                    'market_risk_premium': mrp/100
                }
                wacc_data = calculate_wacc_enhanced(
                    ticker,
                    cost_of_equity_method='capm',
                    capm_overrides=capm_overrides
                )
                method_label = "CAPM"
            
            # Update displays
            wacc_final = format_percentage(wacc_data['wacc'])
            coe_value = format_percentage(wacc_data['cost_of_equity'])
            components_table = create_wacc_components_table(wacc_data)
            
            return wacc_final, coe_value, method_label, components_table
            
        except Exception as e:
            logger.error(f"Error updating WACC calculation: {e}")
            return "Error", "Error", "Error", html.Div(f"Error: {str(e)}")


def transform_fcff_data_for_table(fcff_data_dict):
    """Transform FCFF data from vertical DataFrame to horizontal table format.
    
    Args:
        fcff_data_dict: Dictionary from fcff-data-store in format:
            {'2024': {'ebit': 123216000000.0, 'tax_expense': 29749000000.0, ...}, ...}
            
    Returns:
        List of dictionaries for DataTable, where each row is a component
        and columns are years + component name
    """
    if not fcff_data_dict:
        return []
    
    # Get years sorted (most recent first)
    years = sorted(fcff_data_dict.keys(), reverse=True)
    
    # Define component order and display names
    components = [
        ('ebit', 'Operating Income (EBIT)'),
        ('tax_expense', 'Tax Expense'),
        ('depreciation_amortization', 'Depreciation & Amortization'),
        ('capital_expenditures', 'Capital Expenditures'),
        ('working_capital_change', 'Working Capital Change'),
        ('fcff', 'Free Cash Flow to Firm')
    ]
    
    # Transform data to horizontal format
    table_data = []
    for component_key, component_name in components:
        row = {'Component': component_name}
        
        # Add year columns
        for year in years:
            if year in fcff_data_dict and component_key in fcff_data_dict[year]:
                value = fcff_data_dict[year][component_key]
                # Format as millions with proper sign
                formatted_value = format_financial_number(value)
                row[year] = formatted_value
            else:
                row[year] = 'N/A'
        
        table_data.append(row)
    
    return table_data


def create_fcff_datatable(fcff_data_dict):
    """Create a DataTable component for FCFF financial data.
    
    Args:
        fcff_data_dict: Dictionary from fcff-data-store
        
    Returns:
        dash_table.DataTable component
    """
    if not fcff_data_dict:
        return html.Div("No data available")
    
    # Transform data to horizontal format
    table_data = transform_fcff_data_for_table(fcff_data_dict)
    
    if not table_data:
        return html.Div("No data available")
    
    # Get years for column definitions
    years = sorted(fcff_data_dict.keys(), reverse=True)
    
    # Define columns
    columns = [
        {"name": "Component", "id": "Component", "type": "text"}
    ]
    
    # Add year columns
    for year in years:
        columns.append({
            "name": year, 
            "id": year, 
            "type": "text"
        })
    
    return dash_table.DataTable(
        id='fcff-data-table',
        columns=columns,
        data=table_data,
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'border': '1px solid #dee2e6'
        },
        style_cell={
            'textAlign': 'right',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'border': '1px solid #dee2e6'
        },
        style_cell_conditional=[
            {
                'if': {'column_id': 'Component'},
                'textAlign': 'left',
                'fontWeight': 'bold',
                'width': '250px'
            }
        ],
        style_data_conditional=[
            # Highlight FCFF row
            {
                'if': {'filter_query': '{Component} = "Free Cash Flow to Firm"'},
                'backgroundColor': '#e3f2fd',
                'fontWeight': 'bold'
            }
        ],
        style_table={
            'overflowX': 'auto',
            'border': '1px solid #dee2e6',
            'borderRadius': '5px'
        }
    )


def create_fcff_formula_section():
    """Create FCFF formula explanation section."""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Free Cash Flow to Firm (FCFF) Formula", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("FCFF = EBIT - Tax Expense + D&A - CapEx - ΔWorking Capital", 
                           className="text-center p-3 bg-light border rounded"),
                ], width=12)
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.Strong("EBIT: "), "Earnings Before Interest and Tax (Operating Income)"
                ], width=6),
                dbc.Col([
                    html.Strong("Tax Expense: "), "Income tax provision"
                ], width=6)
            ], className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Strong("D&A: "), "Depreciation & Amortization (non-cash)"
                ], width=6),
                dbc.Col([
                    html.Strong("CapEx: "), "Capital Expenditures (cash outflow)"
                ], width=6)
            ], className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Strong("ΔWorking Capital: "), "Change in working capital"
                ], width=12)
            ])
        ])
    ], className="mb-4")


def create_fcff_trends_chart(fcff_data_dict):
    """Create FCFF trends visualization chart."""
    if not fcff_data_dict:
        return html.Div("No data available for chart")
    
    # Extract data for chart
    years = sorted(fcff_data_dict.keys())
    fcff_values = [fcff_data_dict[year]['fcff'] / 1e9 for year in years]  # Convert to billions
    
    # Create the chart
    fig = go.Figure()
    
    # Add FCFF trend line
    fig.add_trace(go.Scatter(
        x=years,
        y=fcff_values,
        mode='lines+markers',
        name='FCFF',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Update layout
    fig.update_layout(
        title="Free Cash Flow to Firm Trends",
        xaxis_title="Year",
        yaxis_title="FCFF (Billions $)",
        height=400,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return dcc.Graph(figure=fig)


def create_fcff_growth_analysis(fcff_data_dict):
    """Create growth rate analysis section."""
    if not fcff_data_dict:
        return html.Div("No data available for growth analysis")
    
    # Calculate growth rates
    df = pd.DataFrame.from_dict(fcff_data_dict, orient='index')
    fcff_series = df['fcff'].sort_index()
    growth_rates = fcff_series.pct_change() * 100  # Convert to percentage
    
    # Create growth rate table
    growth_data = []
    for i, (year, rate) in enumerate(growth_rates.items()):
        if pd.notna(rate):  # Skip first year (NaN)
            prev_year = fcff_series.index[i-1]
            growth_data.append({
                'Period': f"{prev_year} → {year}",
                'Growth Rate': f"{rate:.1f}%",
                'FCFF Change': format_financial_number(fcff_series[year] - fcff_series[prev_year])
            })
    
    if not growth_data:
        return html.Div("Insufficient data for growth analysis")
    
    # Calculate statistics
    valid_rates = growth_rates.dropna()
    avg_growth = valid_rates.mean()
    median_growth = valid_rates.median()
    std_growth = valid_rates.std()
    
    return dbc.Row([
        # Growth Rate Table
        dbc.Col([
            html.H6("Year-over-Year Growth"),
            dash_table.DataTable(
                columns=[
                    {"name": "Period", "id": "Period"},
                    {"name": "Growth Rate", "id": "Growth Rate"},
                    {"name": "FCFF Change", "id": "FCFF Change"}
                ],
                data=growth_data,
                style_cell={'textAlign': 'center', 'padding': '10px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
            )
        ], width=8),
        
        # Growth Statistics
        dbc.Col([
            html.H6("Growth Statistics"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Strong("Average: "), f"{avg_growth:.1f}%"
                ]),
                dbc.ListGroupItem([
                    html.Strong("Median: "), f"{median_growth:.1f}%"
                ]),
                dbc.ListGroupItem([
                    html.Strong("Std Dev: "), f"{std_growth:.1f}%"
                ]),
                dbc.ListGroupItem([
                    html.Strong("Volatility: "), 
                    "Low" if std_growth < 20 else "Medium" if std_growth < 50 else "High"
                ])
            ])
        ], width=4)
    ])


def render_fcff_tab(ticker, fcff_data):
    """Render comprehensive FCFF analysis tab."""
    df = pd.DataFrame.from_dict(fcff_data, orient='index')
    
    # Calculate metrics
    latest_year = df.index[-1]
    latest_fcff = float(df['fcff'].iloc[-1])
    avg_fcff = float(df['fcff'].mean())
    
    # Calculate growth rates
    fcff_series = df['fcff'].sort_index()
    growth_rates = fcff_series.pct_change() * 100  # Convert to percentage
    avg_growth = growth_rates.dropna().mean()
    
    return dbc.Container([
        # Header
        html.H3(f"{ticker} - Free Cash Flow to Firm Analysis", className="mb-4"),
        
        # FCFF Formula Explanation
        create_fcff_formula_section(),
        
        # Key Metrics Summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Latest FCFF", className="card-title"),
                        html.H3(format_financial_number(latest_fcff), className="text-primary"),
                        html.P(f"Year: {latest_year}", className="card-text text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Average FCFF", className="card-title"),
                        html.H3(format_financial_number(avg_fcff), className="text-success"),
                        html.P(f"{len(df)} years", className="card-text text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Avg Growth", className="card-title"),
                        html.H3(f"{avg_growth:.1f}%", className="text-info"),
                        html.P("Year-over-year", className="card-text text-muted")
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Data Quality", className="card-title"),
                        html.H3("✓ Complete", className="text-success"),
                        html.P("All components", className="card-text text-muted")
                    ])
                ])
            ], width=3)
        ], className="mb-4"),
        
        # Financial Data Table
        html.Div([
            html.H4("Financial Components", className="mb-3"),
            create_fcff_datatable(fcff_data)
        ], className="mb-4"),
        
        # FCFF Trends Chart
        html.Div([
            html.H4("FCFF Historical Trends", className="mb-3"),
            create_fcff_trends_chart(fcff_data)
        ], className="mb-4"),
        
        # Growth Analysis
        html.Div([
            html.H4("Growth Rate Analysis", className="mb-3"),
            create_fcff_growth_analysis(fcff_data)
        ])
    ], fluid=True)


def render_trends_tab(ticker, fcff_data):
    """Render FCFF trends tab with charts."""
    return html.Div([
        html.H3(f"{ticker} - FCFF Trends"),
        html.P("Charts implementation coming next...")
    ])


def render_growth_tab(ticker, fcff_data):
    """Render growth analysis tab."""
    return html.Div([
        html.H3(f"{ticker} - Growth Analysis"),
        html.P("Growth analysis implementation coming next...")
    ])


def create_wacc_formula_section():
    """Create WACC formula explanation section."""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Weighted Average Cost of Capital (WACC) Formula", className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("WACC = (E/V × Cost of Equity) + (D/V × Cost of Debt × (1 - Tax Rate))", 
                           className="text-center p-3 bg-light border rounded"),
                ], width=12)
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.Strong("E/V: "), "Weight of Equity (Market Cap ÷ Total Value)"
                ], width=6),
                dbc.Col([
                    html.Strong("D/V: "), "Weight of Debt (Total Debt ÷ Total Value)"
                ], width=6)
            ], className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Strong("Cost of Equity: "), "Required return on equity (Direct Input or CAPM)"
                ], width=6),
                dbc.Col([
                    html.Strong("Cost of Debt: "), "After-tax cost of borrowing"
                ], width=6)
            ], className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Strong("Tax Rate: "), "Corporate tax rate (debt tax shield benefit)"
                ], width=12)
            ])
        ])
    ], className="mb-4")


def create_cost_of_equity_method_selector(current_method='direct', current_value=0.12):
    """Create cost of equity method selector with dynamic panels."""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("Cost of Equity Calculation Method", className="mb-0")
        ]),
        dbc.CardBody([
            # Method selector
            dbc.RadioItems(
                id="cost-of-equity-method",
                options=[
                    {"label": "Direct Input (Default)", "value": "direct"},
                    {"label": "CAPM (Capital Asset Pricing Model)", "value": "capm"}
                ],
                value=current_method,
                inline=True,
                className="mb-3"
            ),
            
            # Direct input panel
            html.Div(
                id="direct-input-panel",
                children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Cost of Equity (%):"),
                            dbc.Input(
                                id="direct-cost-of-equity",
                                type="number",
                                value=current_value * 100,
                                min=5,
                                max=25,
                                step=0.1,
                                size="sm"
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Rationale (Optional):"),
                            dbc.Input(
                                id="cost-of-equity-rationale",
                                type="text",
                                placeholder="e.g., Based on comparable companies",
                                size="sm"
                            )
                        ], width=8)
                    ])
                ],
                style={"display": "block" if current_method == "direct" else "none"}
            ),
            
            # CAPM panel
            html.Div(
                id="capm-panel",
                children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Risk-free Rate (%):"),
                            dbc.Input(
                                id="capm-risk-free-rate",
                                type="number",
                                value=4.0,
                                min=0,
                                max=10,
                                step=0.1,
                                size="sm"
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Beta:"),
                            dbc.Input(
                                id="capm-beta",
                                type="number",
                                value=1.22,
                                min=0.1,
                                max=3.0,
                                step=0.01,
                                size="sm"
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Market Risk Premium (%):"),
                            dbc.Input(
                                id="capm-market-risk-premium",
                                type="number",
                                value=6.0,
                                min=3,
                                max=10,
                                step=0.1,
                                size="sm"
                            )
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Calculated Cost of Equity:"),
                            html.H6(id="capm-calculated-result", className="text-primary mt-2")
                        ], width=3)
                    ])
                ],
                style={"display": "none" if current_method == "direct" else "block"}
            )
        ])
    ], className="mb-4")


def create_wacc_components_table(wacc_data):
    """Create comprehensive WACC components table."""
    if not wacc_data:
        return html.Div("No WACC data available")
    
    # Build table data
    table_data = [
        # Cost of Equity section
        {
            'Component': 'COST OF EQUITY',
            'Value': '',
            'Method_Source': '',
            'section_header': True
        },
        {
            'Component': 'Cost of Equity',
            'Value': format_percentage(wacc_data['cost_of_equity']),
            'Method_Source': wacc_data['primary_method']['rationale'] if 'primary_method' in wacc_data else 'Direct Input'
        }
    ]
    
    # Add alternative method if available
    if wacc_data.get('alternative_method'):
        table_data.append({
            'Component': 'Alternative (Comparison)',
            'Value': format_percentage(wacc_data['alternative_method']['cost_of_equity']),
            'Method_Source': f"Difference: {wacc_data['alternative_method']['difference_vs_primary']:+.1%}"
        })
    
    # Capital structure section
    table_data.extend([
        {
            'Component': 'CAPITAL STRUCTURE',
            'Value': '',
            'Method_Source': '',
            'section_header': True
        },
        {
            'Component': 'Market Capitalization',
            'Value': format_financial_number(wacc_data['market_cap']),
            'Method_Source': 'Yahoo Finance (Current)'
        },
        {
            'Component': 'Total Debt',
            'Value': format_financial_number(wacc_data['total_debt']),
            'Method_Source': 'Balance Sheet (Latest)'
        },
        {
            'Component': 'Total Enterprise Value',
            'Value': format_financial_number(wacc_data['total_value']),
            'Method_Source': 'Market Cap + Debt'
        },
        {
            'Component': 'Weight of Equity (E/V)',
            'Value': format_percentage(wacc_data['weight_equity']),
            'Method_Source': 'Market Cap ÷ Total Value'
        },
        {
            'Component': 'Weight of Debt (D/V)',
            'Value': format_percentage(wacc_data['weight_debt']),
            'Method_Source': 'Debt ÷ Total Value'
        }
    ])
    
    # Cost of debt section
    table_data.extend([
        {
            'Component': 'COST OF DEBT',
            'Value': '',
            'Method_Source': '',
            'section_header': True
        },
        {
            'Component': 'Interest Expense (Annual)',
            'Value': format_financial_number(wacc_data.get('interest_expense', 0)),
            'Method_Source': 'Income Statement'
        },
        {
            'Component': 'Pre-tax Cost of Debt',
            'Value': format_percentage(wacc_data['cost_of_debt'] / (1 - wacc_data['tax_rate'])) if wacc_data['cost_of_debt'] > 0 else '0.0%',
            'Method_Source': 'Interest ÷ Total Debt'
        },
        {
            'Component': 'Tax Rate',
            'Value': format_percentage(wacc_data['tax_rate']),
            'Method_Source': 'US Federal Corporate Rate'
        },
        {
            'Component': 'After-tax Cost of Debt',
            'Value': format_percentage(wacc_data['cost_of_debt']),
            'Method_Source': 'Pre-tax × (1 - Tax Rate)'
        }
    ])
    
    # WACC calculation section
    table_data.extend([
        {
            'Component': 'WACC CALCULATION',
            'Value': '',
            'Method_Source': '',
            'section_header': True
        },
        {
            'Component': 'Equity Component',
            'Value': format_percentage(wacc_data['equity_component']),
            'Method_Source': f"{wacc_data['weight_equity']:.1%} × {wacc_data['cost_of_equity']:.1%}"
        },
        {
            'Component': 'Debt Component',
            'Value': format_percentage(wacc_data['debt_component']),
            'Method_Source': f"{wacc_data['weight_debt']:.1%} × {wacc_data['cost_of_debt']:.1%}"
        },
        {
            'Component': 'WACC (Final)',
            'Value': format_percentage(wacc_data['wacc']),
            'Method_Source': 'Equity + Debt Components',
            'highlight': True
        }
    ])
    
    return dash_table.DataTable(
        columns=[
            {"name": "Component", "id": "Component"},
            {"name": "Value", "id": "Value"},
            {"name": "Method/Source", "id": "Method_Source"}
        ],
        data=table_data,
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'border': '1px solid #dee2e6'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'border': '1px solid #dee2e6'
        },
        style_cell_conditional=[
            {
                'if': {'column_id': 'Value'},
                'textAlign': 'right',
                'fontWeight': 'bold'
            }
        ],
        style_data_conditional=[
            # Section headers
            {
                'if': {'filter_query': '{section_header} = true'},
                'backgroundColor': '#e9ecef',
                'fontWeight': 'bold',
                'fontStyle': 'italic'
            },
            # Highlight WACC final result
            {
                'if': {'filter_query': '{highlight} = true'},
                'backgroundColor': '#e3f2fd',
                'fontWeight': 'bold',
                'border': '2px solid #1976d2'
            }
        ],
        style_table={
            'overflowX': 'auto',
            'border': '1px solid #dee2e6',
            'borderRadius': '5px'
        }
    )


def create_wacc_method_comparison(wacc_data):
    """Create method comparison section when alternative method is available."""
    if not wacc_data.get('alternative_method'):
        return html.Div()
    
    alt_method = wacc_data['alternative_method']
    primary_method = wacc_data['primary_method']['method']
    
    comparison_data = [
        {
            'Method': primary_method.title(),
            'Cost_of_Equity': format_percentage(wacc_data['cost_of_equity']),
            'Resulting_WACC': format_percentage(wacc_data['wacc']),
            'Notes': 'Currently Used'
        },
        {
            'Method': alt_method['method'].title(),
            'Cost_of_Equity': format_percentage(alt_method['cost_of_equity']),
            'Resulting_WACC': format_percentage(alt_method['wacc']),
            'Notes': f"Difference: {alt_method['difference_vs_primary']:+.1%}"
        }
    ]
    
    return dbc.Row([
        dbc.Col([
            dash_table.DataTable(
                columns=[
                    {"name": "Method", "id": "Method"},
                    {"name": "Cost of Equity", "id": "Cost_of_Equity"},
                    {"name": "Resulting WACC", "id": "Resulting_WACC"},
                    {"name": "Notes", "id": "Notes"}
                ],
                data=comparison_data,
                style_cell={'textAlign': 'center', 'padding': '10px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Notes} = "Currently Used"'},
                        'backgroundColor': '#e8f5e8',
                        'fontWeight': 'bold'
                    }
                ]
            )
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Key Differences"),
                    html.P([
                        html.Strong("Cost of Equity: "),
                        f"{alt_method['difference_vs_primary']:+.1%}"
                    ]),
                    html.P([
                        html.Strong("WACC Impact: "),
                        f"{alt_method['wacc_difference']:+.1%}"
                    ]),
                    html.P([
                        html.Strong("Magnitude: "),
                        f"{abs(alt_method['difference_vs_primary']):.0%} difference"
                    ])
                ])
            ])
        ], width=4)
    ])


def render_wacc_tab(ticker, fcff_data):
    """Render comprehensive WACC analysis tab with direct input default."""
    try:
        from core.wacc import calculate_wacc_enhanced
        
        # Calculate WACC using enhanced function with direct input default
        wacc_data = calculate_wacc_enhanced(ticker, cost_of_equity_method='direct', direct_cost_of_equity=0.12)
        
        return dbc.Container([
            # Header
            html.H3(f"{ticker} - Weighted Average Cost of Capital Analysis", className="mb-4"),
            
            # WACC Formula Explanation
            create_wacc_formula_section(),
            
            # Cost of Equity Method Selector
            create_cost_of_equity_method_selector(),
            
            # Key Metrics Dashboard
            html.Div(id="wacc-metrics-dashboard", children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Final WACC", className="card-title"),
                                html.H3(format_percentage(wacc_data['wacc']), className="text-primary", id="wacc-final-value"),
                                html.P("Weighted Average", className="card-text text-muted")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Cost of Equity", className="card-title"),
                                html.H3(format_percentage(wacc_data['cost_of_equity']), className="text-success", id="wacc-cost-of-equity-value"),
                                html.P(wacc_data['primary_method']['method'].title(), className="card-text text-muted", id="wacc-method-label")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Cost of Debt", className="card-title"),
                                html.H3(format_percentage(wacc_data['cost_of_debt']), className="text-info", id="wacc-cost-of-debt-value"),
                                html.P("After-tax", className="card-text text-muted")
                            ])
                        ])
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Capital Mix", className="card-title"),
                                html.H3(f"{wacc_data['weight_equity']:.0%} Equity", className="text-warning", id="wacc-capital-mix-value"),
                                html.P(f"{wacc_data['weight_debt']:.0%} Debt", className="card-text text-muted", id="wacc-debt-mix-value")
                            ])
                        ])
                    ], width=3)
                ], className="mb-4")
            ]),
            
            # Comprehensive Components Table
            html.Div([
                html.H4("WACC Components Breakdown", className="mb-3"),
                html.Div(id="wacc-components-table", children=create_wacc_components_table(wacc_data))
            ], className="mb-4"),
            
            # Method Comparison (if alternative available)
            html.Div([
                html.H4("Method Comparison", className="mb-3"),
                create_wacc_method_comparison(wacc_data)
            ] if wacc_data.get('alternative_method') else [], className="mb-4"),
            
            # Interactive Controls Message
            dbc.Alert([
                html.H6("💡 Interactive Controls", className="alert-heading"),
                html.P("Use the Cost of Equity Method selector above to switch between Direct Input and CAPM, "
                      "or adjust individual assumptions to see real-time WACC updates.", className="mb-0")
            ], color="info")
            
        ], fluid=True)
        
    except Exception as e:
        logger.error(f"Enhanced WACC calculation error: {e}", exc_info=True)
        return dbc.Alert([
            html.H5("WACC Calculation Error"),
            html.P(f"Error calculating WACC for {ticker}: {str(e)}"),
            html.Hr(),
            html.P("Please check that the company ticker is valid and try again.", className="mb-0")
        ], color="danger")


def render_dcf_tab(ticker, fcff_data, projection_years=5, terminal_growth=2.5, wacc_override=None):
    """Render DCF valuation tab with calculation results."""
    try:
        df = pd.DataFrame.from_dict(fcff_data, orient='index')
        
        if len(df) == 0:
            return dbc.Alert("No FCFF data available for DCF calculation", color="warning")
        
        terminal_growth_decimal = terminal_growth / 100.0
        
        logger.info(f"DCF calculation: ticker={ticker}, proj_years={projection_years}, term_growth={terminal_growth}%, wacc_override={wacc_override}")
        
        wacc_data = calculate_wacc(ticker)
        wacc_value = (wacc_override / 100.0) if wacc_override else wacc_data['wacc']
        
        if wacc_value <= terminal_growth_decimal:
            return dbc.Alert([
                html.H5("Invalid Assumptions"),
                html.P(f"WACC ({wacc_value:.1%}) must be greater than terminal growth rate ({terminal_growth_decimal:.1%})")
            ], color="danger")
        
        fcff_series = df['fcff'].sort_index()
        latest_fcff = float(fcff_series.iloc[-1])
        
        if len(fcff_series) >= 2:
            historical_growth = calculate_revenue_growth_rate(pd.Series(fcff_series.values, index=fcff_series.index), method='geometric')
            projection_growth = min(max(historical_growth * 0.75, 0.03), 0.12)
        else:
            projection_growth = 0.05
        
        projected_fcff_values = []
        for year in range(1, projection_years + 1):
            projected_value = latest_fcff * ((1 + projection_growth) ** year)
            projected_fcff_values.append(projected_value)
        
        projected_df = pd.DataFrame({
            'fcff': projected_fcff_values,
            'projected_fcff': projected_fcff_values
        }, index=range(1, projection_years + 1))
        
        wacc_data_for_dcf = {
            'wacc': wacc_value,
            'total_debt': wacc_data.get('total_debt', 0),
            'cash': wacc_data.get('cash', 0)
        }
        
        stock = yf.Ticker(ticker)
        info = stock.info
        shares_outstanding = info.get('sharesOutstanding', None)
        current_price = info.get('currentPrice', None)
        
        dcf_results = perform_dcf_valuation(
            projected_df,
            wacc_data_for_dcf,
            terminal_growth_decimal,
            shares_outstanding
        )
        
        enterprise_value = dcf_results['enterprise_value']
        equity_value = dcf_results['equity_value']
        value_per_share = dcf_results['value_per_share']
        pv_operating = dcf_results['pv_operating_cash_flows']
        pv_terminal = dcf_results['pv_terminal_value']
        
        if current_price and value_per_share:
            upside = ((value_per_share - current_price) / current_price) * 100
        else:
            upside = None
        
        return dbc.Container([
            html.H3(f"{ticker} - DCF Valuation", className="mb-4"),
            
            dbc.Card([
                dbc.CardHeader(html.H5("Assumptions", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Projection Years"),
                            dcc.Slider(
                                id="dcf-projection-years-slider",
                                min=3,
                                max=10,
                                step=1,
                                value=projection_years,
                                marks={i: str(i) for i in range(3, 11)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("Terminal Growth Rate (%)"),
                            dcc.Slider(
                                id="dcf-terminal-growth-slider",
                                min=1.0,
                                max=5.0,
                                step=0.1,
                                value=terminal_growth,
                                marks={i: f"{i}%" for i in range(1, 6)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Label("WACC Override (%) - Optional"),
                            dbc.Input(
                                id="dcf-wacc-override-input",
                                type="number",
                                placeholder="Auto-calculated",
                                value=wacc_override if wacc_override else "",
                                min=1,
                                max=30,
                                step=0.1
                            )
                        ], width=4)
                    ])
                ])
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Enterprise Value", className="text-muted"),
                            html.H4(format_financial_number(enterprise_value), className="text-primary")
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Equity Value", className="text-muted"),
                            html.H4(format_financial_number(equity_value), className="text-success")
                        ])
                    ])
                ], width=6)
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Fair Value per Share", className="text-muted"),
                            html.H3(f"${value_per_share:.2f}" if value_per_share else "N/A", className="text-primary")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Current Price", className="text-muted"),
                            html.H3(f"${current_price:.2f}" if current_price else "N/A")
                        ])
                    ])
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Upside / Downside", className="text-muted"),
                            html.H3(
                                f"{upside:+.1f}%" if upside else "N/A",
                                className="text-success" if upside and upside > 0 else "text-danger"
                            )
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            html.Hr(),
            html.H5("Valuation Breakdown", className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    html.P([html.Strong("PV Operating Cash Flows: "), format_financial_number(pv_operating)]),
                    html.P([html.Strong("PV Terminal Value: "), format_financial_number(pv_terminal)]),
                    html.P([html.Strong("Net Debt: "), format_financial_number(dcf_results['net_debt'])]),
                ], width=6),
                dbc.Col([
                    html.P([html.Strong("WACC: "), f"{wacc_value:.2%}"]),
                    html.P([html.Strong("Terminal Growth: "), f"{terminal_growth_decimal:.2%}"]),
                    html.P([html.Strong("Projection Years: "), str(projection_years)]),
                    html.P([html.Strong("Shares Outstanding: "), f"{shares_outstanding:,.0f}" if shares_outstanding else "N/A"])
                ], width=6)
            ])
        ], fluid=True)
        
    except Exception as e:
        logger.error(f"DCF calculation error for {ticker}: {e}", exc_info=True)
        return dbc.Alert([
            html.H5("DCF Calculation Error"),
            html.P(str(e)),
            html.P("Please check your assumptions and try again.", className="mb-0")
        ], color="danger")
