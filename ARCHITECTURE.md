# DCF Calculator Architecture Plan

## Project Overview
DCF Calculator for Finance Club managing $300k portfolio. Focus: functionality first, iterative development.

## Target Features
1. **Web Interface**: Basic web app for easy access
2. **Data Sources**: Yahoo Finance (primary), Alpha Vantage, EDGAR APIs for evaluation
3. **Output**: Excel export for finance students to analyze and modify
4. **Core DCF**: Cash flow projections, discount rate calculation, terminal value, NPV

## Folder Structure

```
DCF_Calculator/
├── dcf/                          # Main package
│   ├── __init__.py
│   ├── core/                     # Core DCF logic (build first)
│   │   ├── __init__.py
│   │   ├── cash_flows.py         # Free cash flow calculations
│   │   ├── discount_rate.py      # WACC, cost of equity
│   │   ├── terminal_value.py     # Terminal value methods
│   │   └── dcf_engine.py         # Main DCF calculation
│   ├── data/                     # Data handling (build second)
│   │   ├── __init__.py
│   │   ├── yahoo_finance.py      # Yahoo Finance API
│   │   ├── alpha_vantage.py      # Alpha Vantage API
│   │   ├── edgar.py              # SEC EDGAR API
│   │   ├── validators.py         # Input validation
│   │   └── exporters.py          # Excel export functionality
│   ├── analysis/                 # Advanced features (build later)
│   │   ├── __init__.py
│   │   ├── sensitivity.py        # Scenario analysis
│   │   ├── comparables.py        # Peer comparison
│   │   └── risk_assessment.py    # Risk metrics
│   └── web/                      # Web interface
│       ├── __init__.py
│       ├── app.py                # Main Flask/FastAPI app
│       ├── routes.py             # API endpoints
│       └── templates/            # HTML templates
├── tests/                        # Testing structure
│   ├── __init__.py
│   ├── test_core/
│   │   ├── test_cash_flows.py
│   │   ├── test_discount_rate.py
│   │   └── test_dcf_engine.py
│   ├── test_data/
│   └── fixtures/                 # Test data files
├── examples/                     # Sample calculations
│   ├── sample_company.py
│   └── validation_cases.py
├── docs/                         # Documentation
│   ├── methodology.md            # DCF assumptions
│   └── user_guide.md
├── data/                         # External data files
│   ├── risk_free_rates.csv
│   └── industry_multiples.csv
├── static/                       # Web assets
│   ├── css/
│   ├── js/
│   └── images/
├── main.py                       # Entry point
├── pyproject.toml
├── AGENTS.md
└── README.md
```

## Development Phases

### Phase 1: Core Engine + Basic Web
- `dcf/core/cash_flows.py` - Basic FCF calculations
- `dcf/core/dcf_engine.py` - Simple NPV calculation
- `dcf/web/app.py` - Basic web interface
- Basic Yahoo Finance integration

### Phase 2: Data Integration
- `dcf/data/yahoo_finance.py` - Yahoo Finance API
- `dcf/data/alpha_vantage.py` - Alpha Vantage API  
- `dcf/data/edgar.py` - SEC EDGAR API
- Compare API quality and reliability

### Phase 3: Excel Export
- `dcf/data/exporters.py` - Excel export with formulas
- Template creation for finance students
- Validation and formatting

### Phase 4: Enhanced Features
- `dcf/core/discount_rate.py` - WACC calculations
- `dcf/core/terminal_value.py` - Terminal value methods
- `dcf/analysis/sensitivity.py` - Scenario analysis

## Technical Decisions

### Web Framework
- **Flask** for simplicity and quick iteration
- Templates for basic UI
- REST API for data endpoints

### Data Sources Priority
1. **Yahoo Finance** - Primary, free, reliable
2. **Alpha Vantage** - Backup, free tier evaluation
3. **EDGAR** - SEC filings for fundamental data

### Excel Export Strategy
- **openpyxl** for Excel file creation
- Include formulas for student learning
- Formatted templates with charts

## Success Metrics
- Accurate DCF calculations vs manual Excel models
- Successful data retrieval from multiple APIs
- Clean Excel exports usable by finance students
- Web interface accessible to finance club members