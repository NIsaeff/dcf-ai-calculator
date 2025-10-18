# Migration Plan: Streamlit → Dash

## Why Dash?
- **No full page reruns** - Only callbacks execute
- **Proper error handling** - Errors are isolated to callbacks
- **Production-ready** - Used by financial institutions
- **Better debugging** - Flask's debugging tools available
- **Clearer state management** - Explicit callbacks vs implicit reruns

## Architecture Comparison

### Streamlit (Current - Problematic)
```python
# ENTIRE function reruns on ANY widget interaction
def show_page():
    wacc = calculate_wacc(ticker)  # ❌ Reruns every time!
    slider_value = st.slider(...)  # ❌ Triggers full rerun
    result = calculate_dcf(...)    # ❌ Recalculates everything
```

### Dash (Recommended - Efficient)
```python
# Only the callback runs, not the entire page
@app.callback(
    Output('result', 'children'),
    Input('slider', 'value')
)
def update_result(slider_value):  # ✅ Only this runs!
    return calculate_dcf(slider_value)
```

## Migration Steps

### Step 1: Install Dash
```bash
cd /home/n8dawg/Projects/Clients/DCF_Calculator
uv add dash plotly pandas
```

### Step 2: Create Basic Dash App Structure
```
DCF_Calculator/
├── app.py                 # Main Dash app (replaces main.py)
├── layouts/              # UI layouts (replaces stlitpages/)
│   ├── __init__.py
│   ├── sidebar.py
│   ├── fcff_tab.py
│   ├── wacc_tab.py
│   └── dcf_tab.py
├── callbacks/            # Event handlers (NEW)
│   ├── __init__.py
│   ├── fcff_callbacks.py
│   ├── wacc_callbacks.py
│   └── dcf_callbacks.py
├── core/                 # Keep as-is (calculation logic)
├── data/                 # Keep as-is (API integrations)
└── assets/              # CSS/JS (NEW)
    └── custom.css
```

### Step 3: Create Main Dash App

**File: `app.py`**
```python
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from layouts import fcff_tab, wacc_tab, dcf_tab
from callbacks import register_callbacks

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = "DCF Calculator - Finance Club"

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("DCF Calculator"),
            html.P("Finance Club - Portfolio Analysis Tool")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            # Sidebar
            html.Div([
                html.H3("Input Parameters"),
                dcc.Input(
                    id='ticker-input',
                    type='text',
                    placeholder='Enter ticker (e.g., AAPL)',
                    value='AAPL',
                    className='form-control mb-3'
                ),
                dcc.RadioItems(
                    id='data-source',
                    options=[
                        {'label': 'Yahoo Finance', 'value': 'yahoo'},
                        {'label': 'SEC EDGAR', 'value': 'edgar'}
                    ],
                    value='yahoo',
                    className='mb-3'
                ),
                html.Button(
                    'Analyze Company',
                    id='analyze-button',
                    className='btn btn-primary w-100'
                ),
                html.Div(id='analysis-status', className='mt-3')
            ])
        ], width=3),
        
        dbc.Col([
            # Main content area with tabs
            dcc.Tabs(id='main-tabs', value='fcff-tab', children=[
                dcc.Tab(label='FCFF Analysis', value='fcff-tab'),
                dcc.Tab(label='WACC Analysis', value='wacc-tab'),
                dcc.Tab(label='DCF Valuation', value='dcf-tab')
            ]),
            html.Div(id='tab-content', className='mt-3')
        ], width=9)
    ])
], fluid=True)

# Register all callbacks
register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True, port=8508)
```

### Step 4: Create DCF Tab Layout

**File: `layouts/dcf_tab.py`**
```python
from dash import dcc, html
import dash_bootstrap_components as dbc

def create_dcf_layout():
    """Create DCF valuation tab layout."""
    return dbc.Container([
        html.H3("DCF Valuation"),
        
        # Assumptions section
        dbc.Row([
            dbc.Col([
                html.Label("Projection Years"),
                dcc.Slider(
                    id='projection-years',
                    min=3,
                    max=10,
                    value=5,
                    marks={i: str(i) for i in range(3, 11)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], width=4),
            
            dbc.Col([
                html.Label("Terminal Growth Rate (%)"),
                dcc.Input(
                    id='terminal-growth',
                    type='number',
                    min=0.0,
                    max=5.0,
                    step=0.1,
                    value=2.5,
                    className='form-control'
                )
            ], width=4),
            
            dbc.Col([
                html.Label("Custom WACC (%)"),
                dcc.Input(
                    id='custom-wacc',
                    type='number',
                    min=1.0,
                    max=30.0,
                    step=0.1,
                    value=10.0,
                    className='form-control'
                )
            ], width=4)
        ], className='mb-4'),
        
        # Validation message area
        html.Div(id='dcf-validation', className='mb-3'),
        
        # Results area
        html.Div(id='dcf-results')
    ])
```

### Step 5: Create DCF Callback

**File: `callbacks/dcf_callbacks.py`**
```python
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from core.wacc import calculate_wacc
from core.dcf_valuation import perform_dcf_valuation
from core.growth_rates import forecast_multi_stage_growth
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def register_dcf_callbacks(app):
    """Register all DCF-related callbacks."""
    
    @app.callback(
        [Output('dcf-validation', 'children'),
         Output('dcf-results', 'children')],
        [Input('projection-years', 'value'),
         Input('terminal-growth', 'value'),
         Input('custom-wacc', 'value')],
        [State('ticker-input', 'value'),
         State('fcff-data-store', 'data')]  # Store from FCFF tab
    )
    def update_dcf_valuation(projection_years, terminal_growth, custom_wacc, 
                            ticker, fcff_data):
        """Calculate and display DCF valuation.
        
        This callback ONLY runs when inputs change.
        No full page reload!
        """
        
        logger.info(f"DCF callback triggered: proj={projection_years}, "
                   f"term={terminal_growth}, wacc={custom_wacc}")
        
        # Validation
        terminal_growth_decimal = terminal_growth / 100
        custom_wacc_decimal = custom_wacc / 100
        
        if custom_wacc_decimal <= terminal_growth_decimal:
            validation_msg = dbc.Alert(
                f"⚠️ WACC ({custom_wacc}%) must be greater than "
                f"Terminal Growth Rate ({terminal_growth}%)",
                color="danger"
            )
            return validation_msg, ""
        
        # Clear validation
        validation_msg = ""
        
        # Perform calculations
        try:
            # Convert stored data back to DataFrame
            if not fcff_data:
                return "", dbc.Alert("Please analyze a company first", color="warning")
            
            df = pd.DataFrame(fcff_data)
            
            # Get WACC
            wacc_data = calculate_wacc(ticker)
            wacc_data['wacc'] = custom_wacc_decimal
            
            # Calculate growth forecast
            fcff_series = pd.Series(df['fcff'].values, index=df.index)
            growth_forecast = forecast_multi_stage_growth(
                historical_fcff=fcff_series,
                industry_sector='Technology',  # Get from dropdown
                high_growth_years=min(projection_years, 5),
                transition_years=max(0, projection_years - 5)
            )
            
            # Create projections
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
            
            projections_df = pd.DataFrame(projected_data).set_index('year')
            
            # Perform DCF valuation
            valuation_results = perform_dcf_valuation(
                projected_fcff=projections_df,
                wacc_data=wacc_data,
                terminal_growth_rate=terminal_growth_decimal,
                shares_outstanding=1_000_000_000  # Get from input
            )
            
            # Create results layout
            results = dbc.Row([
                dbc.Col([
                    html.H5("Enterprise Value"),
                    html.H3(f"${valuation_results['enterprise_value']:,.0f}")
                ], width=3),
                dbc.Col([
                    html.H5("Equity Value"),
                    html.H3(f"${valuation_results['equity_value']:,.0f}")
                ], width=3),
                dbc.Col([
                    html.H5("Value per Share"),
                    html.H3(f"${valuation_results['value_per_share']:.2f}")
                ], width=3),
                dbc.Col([
                    html.H5("Terminal Value %"),
                    html.H3(f"{valuation_results['terminal_value_percentage']:.1%}")
                ], width=3)
            ])
            
            return validation_msg, results
            
        except Exception as e:
            logger.error(f"DCF calculation error: {e}", exc_info=True)
            error_msg = dbc.Alert(
                [html.H5("Calculation Error"),
                 html.P(str(e))],
                color="danger"
            )
            return validation_msg, error_msg
```

### Step 6: Register Callbacks

**File: `callbacks/__init__.py`**
```python
from .dcf_callbacks import register_dcf_callbacks
from .fcff_callbacks import register_fcff_callbacks
from .wacc_callbacks import register_wacc_callbacks

def register_callbacks(app):
    """Register all application callbacks."""
    register_fcff_callbacks(app)
    register_wacc_callbacks(app)
    register_dcf_callbacks(app)
```

## Key Advantages Over Streamlit

### 1. **Isolated Execution**
```python
# Streamlit: Everything reruns
wacc = calculate_wacc()  # ❌ API call on every slider move

# Dash: Only callback runs
@app.callback(...)
def update(value):
    # ✅ Only this code runs when slider changes
```

### 2. **Explicit Error Handling**
```python
# Each callback has its own try/except
# Errors don't crash the entire page
# Full stack traces available in logs
```

### 3. **Better Debugging**
```python
# Flask debug mode shows:
# - Full stack traces
# - Request/response details
# - Timing information
# - Memory usage
```

### 4. **Data Stores**
```python
# Share data between callbacks without recalculation
dcc.Store(id='fcff-data-store'),
dcc.Store(id='wacc-data-store'),
```

### 5. **Professional Deployment**
```python
# Works with:
# - Gunicorn (production WSGI server)
# - Docker
# - Kubernetes
# - AWS/GCP/Azure
# - Heroku
```

## Next Steps

1. Create `app.py` with basic structure
2. Test with one tab (FCFF)
3. Migrate callbacks one at a time
4. Add styling with Bootstrap
5. Deploy to production

## Resources

- [Dash Documentation](https://dash.plotly.com/)
- [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/)
- [Example Financial Dashboards](https://github.com/plotly/dash-sample-apps)
