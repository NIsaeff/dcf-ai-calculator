"""DCF Calculator - Main Dash Application."""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from layouts.sidebar import create_sidebar
from layouts.main_content import create_main_content
from callbacks import register_callbacks


# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="DCF Calculator - Finance Club"
)

# Main layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("DCF Calculator", className="text-primary mt-3"),
            html.P("Finance Club - Portfolio Analysis Tool", className="text-muted mb-4")
        ])
    ]),
    
    # Main content area
    dbc.Row([
        # Sidebar (inputs)
        dbc.Col(create_sidebar(), width=3, className="bg-light p-3"),
        
        # Main content (tabs and results)
        dbc.Col(create_main_content(), width=9, className="p-3")
    ]),
    
    # Data stores for sharing between callbacks
    dcc.Store(id='fcff-data-store'),
    dcc.Store(id='wacc-data-store'),
    dcc.Store(id='ticker-store'),
    
], fluid=True, className="px-4")

# Register all callbacks
register_callbacks(app)

# Server for deployment
server = app.server

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8508
    )
