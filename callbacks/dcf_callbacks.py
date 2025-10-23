"""DCF valuation callbacks for Dash application."""

from dash import Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import yfinance as yf
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
        elif active_tab == "trends-tab":
            return render_trends_tab(ticker, fcff_data)
        elif active_tab == "growth-tab":
            return render_growth_tab(ticker, fcff_data)
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


def render_fcff_tab(ticker, fcff_data):
    """Render FCFF financial data tab."""
    df = pd.DataFrame.from_dict(fcff_data, orient='index')
    
    # Create metrics
    latest_year = df.index[-1]
    latest_fcff = float(df['fcff'].iloc[-1])
    avg_fcff = float(df['fcff'].mean())
    
    return dbc.Container([
        html.H3(f"{ticker} - Financial Data"),
        dbc.Row([
            dbc.Col([
                html.H5("FCFF (Latest)"),
                html.H3(format_financial_number(latest_fcff))
            ], width=4),
            dbc.Col([
                html.H5("Average FCFF"),
                html.H3(format_financial_number(avg_fcff))
            ], width=4),
            dbc.Col([
                html.H5("Years of Data"),
                html.H3(str(len(df)))
            ], width=4)
        ], className="mb-4"),
        
        # TODO: Add DataTable with formatted data
        html.P("Full table implementation coming next...")
    ])


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


def render_wacc_tab(ticker, fcff_data):
    """Render WACC analysis tab."""
    try:
        wacc_data = calculate_wacc(ticker)
        
        return dbc.Container([
            html.H3(f"{ticker} - WACC Analysis"),
            dbc.Row([
                dbc.Col([
                    html.H5("WACC"),
                    html.H3(format_percentage(wacc_data['wacc']))
                ], width=3),
                dbc.Col([
                    html.H5("Cost of Equity"),
                    html.H3(format_percentage(wacc_data['cost_of_equity']))
                ], width=3),
                dbc.Col([
                    html.H5("Cost of Debt"),
                    html.H3(format_percentage(wacc_data['cost_of_debt']))
                ], width=3),
                dbc.Col([
                    html.H5("Beta"),
                    html.H3(f"{wacc_data['beta']:.2f}")
                ], width=3)
            ])
        ])
    except Exception as e:
        logger.error(f"WACC calculation error: {e}", exc_info=True)
        return dbc.Alert([
            html.H5("WACC Calculation Error"),
            html.P(str(e))
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
