"""DCF valuation callbacks for Dash application."""

from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
import pandas as pd
from core.wacc import calculate_wacc
from core.dcf_valuation import perform_dcf_valuation
from core.growth_rates import forecast_multi_stage_growth
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
        [Input("main-tabs", "value")],
        [State("ticker-store", "data"),
         State("fcff-data-store", "data")]
    )
    def render_tab_content(active_tab, ticker, fcff_data):
        """Render content for the active tab.
        
        This callback ONLY runs when switching tabs.
        """
        if not ticker or not fcff_data:
            return html.Div("No data available. Please analyze a company first.")
        
        if active_tab == "fcff-tab":
            return render_fcff_tab(ticker, fcff_data)
        elif active_tab == "trends-tab":
            return render_trends_tab(ticker, fcff_data)
        elif active_tab == "growth-tab":
            return render_growth_tab(ticker, fcff_data)
        elif active_tab == "wacc-tab":
            return render_wacc_tab(ticker, fcff_data)
        elif active_tab == "dcf-tab":
            return render_dcf_tab(ticker, fcff_data)
        
        return html.Div("Tab not found")


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


def render_dcf_tab(ticker, fcff_data):
    """Render DCF valuation tab with inputs."""
    return html.Div([
        html.H3(f"{ticker} - DCF Valuation"),
        dbc.Alert("DCF tab implementation coming next - this is where the magic happens!", color="info")
    ])
