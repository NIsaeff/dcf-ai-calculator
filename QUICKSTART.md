# DCF Calculator - Quick Start Guide

## What This Is

A professional DCF (Discounted Cash Flow) valuation dashboard built with **Dash** (Plotly).

**Key Features:**
- Calculate FCFF (Free Cash Flow to Firm) from Yahoo Finance or SEC EDGAR
- WACC (Weighted Average Cost of Capital) analysis
- Multi-stage DCF valuation with terminal value
- Sensitivity analysis
- Interactive charts and tables

---

## Installation & Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or manually
uv add dash dash-bootstrap-components plotly
```

### 2. Run the App

```bash
# Option 1: Direct
python app.py

# Option 2: Using script
./run_dash.sh
```

### 3. Access the App

Open your browser to: **http://localhost:8508**

---

## Quick Usage

1. **Enter a ticker** (e.g., `AAPL`, `MSFT`, `GOOGL`)
2. **Select data source** (Yahoo Finance or SEC EDGAR)
3. **Click "Analyze Company"**
4. **Explore tabs:**
   - Financial Data - Historical FCFF breakdown
   - FCFF Trends - Charts and visualizations
   - Growth Analysis - YoY growth rates
   - WACC Analysis - Cost of capital breakdown
   - DCF Valuation - Complete valuation model

---

## Project Structure

```
dcf-calculator/
├── app.py                    # Main Dash application
├── layouts/                  # UI components
│   ├── sidebar.py           # Input controls
│   └── main_content.py      # Tabs and content area
├── callbacks/                # Event handlers
│   ├── fcff_callbacks.py    # FCFF data loading
│   ├── wacc_callbacks.py    # WACC calculations
│   └── dcf_callbacks.py     # DCF valuation & display
├── core/                     # Business logic
│   ├── fcff.py              # FCFF calculations
│   ├── wacc.py              # WACC calculations
│   ├── dcf_valuation.py     # DCF model
│   ├── growth_rates.py      # Growth forecasting
│   └── formatting.py        # Number formatting
├── data/                     # API integrations
│   ├── yahoofin_api.py      # Yahoo Finance data
│   └── edgar_api.py         # SEC EDGAR data
└── assets/                   # Static files
    └── custom.css           # Styling
```

---

## How It Works (vs Streamlit)

### Streamlit (Old Way - REMOVED)
```python
# Everything reruns on any interaction ❌
wacc = calculate_wacc()  # API call every time!
slider = st.slider()     # Triggers full rerun
result = calculate()     # Recalculates everything
```

### Dash (New Way - CURRENT)
```python
# Only callbacks run ✅
@app.callback(
    Output('result', 'children'),
    Input('slider', 'value')
)
def update(value):
    # Only THIS runs when slider changes
    return calculate(value)
```

**Key Advantages:**
- ✅ No full page reruns
- ✅ Isolated error handling
- ✅ Better debugging
- ✅ Production-ready
- ✅ Proper state management

---

## Development

### Adding a New Feature

1. **Add UI** (in `layouts/`)
2. **Add Callback** (in `callbacks/`)
3. **Test independently**
4. No mystery bugs!

### Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

@app.callback(...)
def my_callback(input_value):
    logger.info(f"Callback triggered: {input_value}")
    # ... your code ...
```

### Running Tests

```bash
# Unit tests (when implemented)
pytest

# Manual testing
python app.py
# Then test in browser
```

---

## Common Issues

### Port Already in Use
```bash
# Kill existing process
lsof -ti:8508 | xargs kill -9

# Or use different port
python app.py --port 8509
```

### Dependencies Missing
```bash
# Sync all dependencies
uv sync

# Or install individually
uv add dash dash-bootstrap-components plotly
```

### API Rate Limits (SEC EDGAR)
- SEC requires 100ms delay between requests (already implemented)
- Use Yahoo Finance for faster testing

---

## Next Steps

### Current Status
- ✅ Basic app structure
- ✅ FCFF data loading
- ✅ Tab navigation
- ✅ WACC display
- 🚧 Full DCF implementation (in progress)
- 🚧 Charts and visualizations
- 🚧 Sensitivity analysis

### To Complete
1. Implement remaining tabs with full data tables
2. Add Plotly charts for trends
3. Complete DCF input controls
4. Add DCF calculation callback
5. Style improvements

---

## Resources

- **README.md** - Full documentation
- **AGENTS.md** - Development guidelines
- **Dash Docs** - https://dash.plotly.com/
- **Plotly Charts** - https://plotly.com/python/

---

## Questions?

Check the main README.md for comprehensive documentation.

Happy valuing! 📊
