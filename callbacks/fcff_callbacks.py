"""FCFF analysis callbacks for Dash application."""

from dash import Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from core.fcff import convert_api_data_to_dataframe
from core.formatting import format_financial_number
from data.yahoofin_api import get_fcff_dataframe
from data.edgar_api import get_edgar_fcff_dataframe
import logging

logger = logging.getLogger(__name__)


def register_fcff_callbacks(app):
    """Register FCFF-related callbacks.
    
    Args:
        app: Dash application instance
    """
    
    @app.callback(
        [Output("fcff-data-store", "data"),
         Output("ticker-store", "data"),
         Output("sidebar-status", "children"),
         Output("welcome-message", "style"),
         Output("main-tabs-container", "style")],
        Input("analyze-button", "n_clicks"),
        [State("ticker-input", "value"),
         State("data-source", "value"),
         State("historical-years", "value")],
        prevent_initial_call=True
    )
    def analyze_company(n_clicks, ticker, data_source, years):
        """Analyze company and fetch FCFF data.
        
        Only runs when the Analyze button is clicked.
        No mystery reruns!
        """
        if not ticker:
            return None, None, dbc.Alert("Please enter a ticker", color="warning"), {}, {"display": "none"}
        
        ticker = ticker.upper()
        logger.info(f"Analyzing {ticker} from {data_source}")
        
        try:
            # Fetch data based on source
            if data_source == "yahoo":
                raw_data = get_fcff_dataframe(ticker)
                df = convert_api_data_to_dataframe(raw_data, source='yahoo')
            else:  # edgar
                raw_data = get_edgar_fcff_dataframe(ticker, years)
                df = convert_api_data_to_dataframe(raw_data, source='edgar')
            
            if df is None or len(df) == 0:
                return (None, None,
                        dbc.Alert(f"No data found for {ticker}", color="danger"),
                        {}, {"display": "none"})
            
            # Convert DataFrame to dict for storage
            data_dict = df.to_dict('index')
            
            logger.info(f"Successfully loaded {len(df)} years of data for {ticker}")
            
            return (data_dict, ticker,
                    dbc.Alert(f"✓ Loaded {len(df)} years of data for {ticker}", color="success"),
                    {"display": "none"},  # Hide welcome
                    {"display": "block"})  # Show tabs
                    
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}", exc_info=True)
            return (None, None,
                    dbc.Alert([
                        html.H6("Error loading data"),
                        html.P(str(e))
                    ], color="danger"),
                    {}, {"display": "none"})
