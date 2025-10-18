"""Sidebar layout for DCF Calculator."""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_sidebar():
    """Create sidebar with input controls.
    
    Returns:
        Dash component with sidebar layout
    """
    return html.Div([
        html.H4("Input Parameters", className="mb-3"),
        
        # Ticker Input
        dbc.Label("Stock Ticker", html_for="ticker-input"),
        dbc.Input(
            id="ticker-input",
            type="text",
            placeholder="e.g., AAPL",
            value="AAPL",
            className="mb-3"
        ),
        
        # Data Source Selection
        dbc.Label("Data Source", className="mt-2"),
        dbc.RadioItems(
            id="data-source",
            options=[
                {"label": "Yahoo Finance", "value": "yahoo"},
                {"label": "SEC EDGAR", "value": "edgar"}
            ],
            value="yahoo",
            className="mb-3"
        ),
        
        # Historical Years Slider
        dbc.Label("Historical Years", className="mt-2"),
        dcc.Slider(
            id="historical-years",
            min=3,
            max=10,
            value=5,
            marks={i: str(i) for i in range(3, 11)},
            tooltip={"placement": "bottom", "always_visible": True},
            className="mb-4"
        ),
        
        # Analyze Button
        dbc.Button(
            "Analyze Company",
            id="analyze-button",
            color="primary",
            className="w-100 mb-3"
        ),
        
        # Status Messages
        html.Div(id="sidebar-status"),
        
        # Debug Toggle (optional)
        html.Hr(),
        dbc.Checklist(
            id="debug-mode",
            options=[{"label": " Debug Mode", "value": "debug"}],
            value=[],
            className="small text-muted"
        )
    ])
