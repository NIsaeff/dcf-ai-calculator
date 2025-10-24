"""Main content area layout for DCF Calculator."""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_main_content():
    """Create main content area with tabs.
    
    Returns:
        Dash component with main content layout
    """
    return html.Div([
        # Welcome message (shown initially)
        html.Div(
            id="welcome-message",
            children=[
                dbc.Alert([
                    html.H5("Welcome to DCF Calculator!", className="alert-heading"),
                    html.P("Enter a stock ticker in the sidebar and click 'Analyze Company' to get started."),
                    html.Hr(),
                    html.P([
                        html.Strong("Sample tickers to try: "),
                        "AAPL (Apple), MSFT (Microsoft), GOOGL (Google), TSLA (Tesla)"
                    ], className="mb-0")
                ], color="info")
            ]
        ),
        
        # Tabs (hidden until analysis is run)
        html.Div(
            id="main-tabs-container",
            style={"display": "none"},
            children=[
                dcc.Tabs(
                    id="main-tabs",
                    value="fcff-tab",
                    children=[
                        dcc.Tab(label="FCFF Analysis", value="fcff-tab", className="custom-tab"),
                        dcc.Tab(label="WACC Analysis", value="wacc-tab", className="custom-tab"),
                        dcc.Tab(label="DCF Valuation", value="dcf-tab", className="custom-tab")
                    ]
                ),
                html.Div(id="tab-content", className="mt-3")
            ]
        )
    ])
