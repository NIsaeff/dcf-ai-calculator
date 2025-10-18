# DCF Calculator - Dash Version

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv add dash dash-bootstrap-components plotly gunicorn

# Or using pip
pip install -r requirements-dash.txt
```

### 2. Run the Application

```bash
# Development mode (with hot reload)
python app.py

# Or using the existing run script
chmod +x run_dash.sh
./run_dash.sh
```

The app will be available at: http://localhost:8508

## Architecture

```
DCF_Calculator/
├── app.py                 # Main Dash application
├── layouts/              # UI layouts
│   ├── __init__.py
│   ├── sidebar.py        # Input controls
│   └── main_content.py   # Main content area with tabs
├── callbacks/            # Event handlers (THE KEY DIFFERENCE vs Streamlit!)
│   ├── __init__.py
│   ├── fcff_callbacks.py # FCFF analysis callbacks
│   ├── wacc_callbacks.py # WACC calculation callbacks
│   └── dcf_callbacks.py  # DCF valuation callbacks
├── core/                 # Business logic (100% REUSED from Streamlit!)
│   ├── fcff.py
│   ├── wacc.py
│   ├── dcf_valuation.py
│   └── growth_rates.py
├── data/                 # API integrations (100% REUSED!)
│   ├── edgar_api.py
│   └── yahoofin_api.py
└── assets/              # Static files (CSS, images)
    └── custom.css
```

## Key Differences from Streamlit

### Streamlit (Problems)
- ❌ Entire page reruns on any interaction
- ❌ Caching is buggy
- ❌ Mystery blank pages
- ❌ Poor debugging
- ❌ No error isolation

### Dash (Solutions)
- ✅ Only callbacks run, not the whole page
- ✅ No caching needed - callbacks are fast
- ✅ Clear error messages per callback
- ✅ Flask debugging tools available
- ✅ Errors isolated to specific callbacks

## How Callbacks Work

### Example: DCF Slider

**Streamlit (Bad)**:
```python
# ENTIRE function reruns when slider moves
def show_dcf_page():
    wacc_data = calculate_wacc(ticker)  # ❌ API call EVERY TIME
    wacc = st.slider("WACC", 1, 30, 10)  # ❌ Triggers full rerun
    result = calculate_dcf(wacc)         # ❌ Recalculates everything
```

**Dash (Good)**:
```python
# ONLY this callback runs when slider changes
@app.callback(
    Output('dcf-result', 'children'),
    Input('wacc-slider', 'value')
)
def update_dcf(wacc):  # ✅ Only this function runs!
    return calculate_dcf(wacc)
```

## Debugging

### Viewing Logs
```bash
# The app logs everything
python app.py

# Look for lines like:
# INFO - Analyzing AAPL from yahoo
# INFO - Successfully loaded 5 years of data for AAPL
# INFO - DCF callback triggered: proj=5, term=2.5, wacc=10.0
```

### Debug Mode
- Check the "Debug Mode" checkbox in the sidebar
- See detailed execution info
- View session state
- Inspect callback timing

### Browser Console
- Press F12 to open DevTools
- Check Console tab for JavaScript errors
- Check Network tab for failed requests

## Development Workflow

### Adding a New Feature

1. **Create the UI** (in `layouts/`)
   ```python
   # Add new input to sidebar.py
   dbc.Input(id="new-input", type="number", value=100)
   ```

2. **Create the Callback** (in `callbacks/`)
   ```python
   @app.callback(
       Output('result', 'children'),
       Input('new-input', 'value')
   )
   def calculate_something(value):
       # Your logic here
       return result
   ```

3. **Test Independently**
   - Change the input
   - Watch only that callback run
   - Check logs for errors
   - No mystery bugs!

### Common Patterns

#### Pattern 1: User Input → Calculation → Display
```python
@app.callback(
    Output('display', 'children'),
    Input('input-slider', 'value')
)
def update_display(slider_value):
    result = some_calculation(slider_value)
    return html.Div(f"Result: {result}")
```

#### Pattern 2: Button Click → Fetch Data → Store
```python
@app.callback(
    [Output('data-store', 'data'),
     Output('status', 'children')],
    Input('analyze-button', 'n_clicks'),
    State('ticker-input', 'value'),
    prevent_initial_call=True
)
def fetch_data(n_clicks, ticker):
    data = api_call(ticker)
    status = f"Loaded data for {ticker}"
    return data, status
```

#### Pattern 3: Stored Data → Multiple Displays
```python
@app.callback(
    Output('chart', 'figure'),
    Input('data-store', 'data')
)
def update_chart(data):
    return create_chart(data)
```

## Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install
uv add gunicorn

# Run with 4 workers
gunicorn app:server -b 0.0.0.0:8508 -w 4
```

### Docker

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements-dash.txt

EXPOSE 8508

CMD ["gunicorn", "app:server", "-b", "0.0.0.0:8508", "-w", "4"]
```

```bash
docker build -t dcf-calculator .
docker run -p 8508:8508 dcf-calculator
```

### Environment Variables

```bash
# .env file
DASH_DEBUG=False
DASH_HOST=0.0.0.0
DASH_PORT=8508
LOG_LEVEL=INFO
```

## Testing

### Manual Testing
1. Start app: `python app.py`
2. Enter ticker: "AAPL"
3. Click "Analyze Company"
4. Switch between tabs
5. Adjust DCF sliders
6. Watch logs for errors

### What to Test
- ✅ Button clicks work
- ✅ Sliders update results
- ✅ Tab switching works
- ✅ Error messages display properly
- ✅ Data loads correctly
- ✅ Charts render

## Troubleshooting

### App Won't Start
```bash
# Check if Dash is installed
python -c "import dash; print(dash.__version__)"

# Check for port conflicts
lsof -i :8508
```

### Callback Not Firing
1. Check callback decorator has correct Input/Output
2. Verify component IDs match layout
3. Look for errors in terminal
4. Check browser console (F12)

### Data Not Loading
1. Check logs for API errors
2. Verify ticker is valid
3. Test API modules independently:
   ```bash
   python data/yahoofin_api.py
   python data/edgar_api.py
   ```

## Migration Checklist

- [x] Install Dash dependencies
- [x] Create app.py structure
- [x] Create layouts/ directory
- [x] Create callbacks/ directory
- [x] Implement basic FCFF callback
- [ ] Implement all tab renderers
- [ ] Add DCF input controls
- [ ] Add DCF calculation callback
- [ ] Add charts (Plotly)
- [ ] Add DataTables
- [ ] Style with custom CSS
- [ ] Test all features
- [ ] Deploy to production

## Next Steps

1. **Run the app**: `python app.py`
2. **Test basic functionality**: Analyze a company
3. **Implement remaining tabs**: Growth, Trends, full DCF
4. **Add charts**: Use Plotly for visualizations
5. **Polish UI**: Custom CSS and styling
6. **Deploy**: Use Gunicorn + Docker

## Resources

- **Dash Documentation**: https://dash.plotly.com/
- **Dash Bootstrap Components**: https://dash-bootstrap-components.opensource.faculty.ai/
- **Plotly Charts**: https://plotly.com/python/
- **Deployment Guide**: https://dash.plotly.com/deployment

## Questions?

Check the migration guides:
- `MIGRATION_TO_DASH.md` - Detailed migration steps
- `FRAMEWORK_COMPARISON.md` - Why Dash vs alternatives
- `REACT_VS_PYTHON.md` - Dash vs React comparison
