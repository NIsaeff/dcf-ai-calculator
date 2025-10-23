# AGENTS.md - Development Guidelines

## Build/Test Commands

- **Run**: `python app.py` or `./run_dash.sh` | **Install**: `uv add <package>` | **Test**: `pytest` or `uv add --dev pytest && pytest`
- **Single test**: `pytest tests/test_file.py::test_function -v` | **Module test**: `python data/edgar_api.py` or `python core/fcff.py`
- **Production**: `gunicorn app:server -b 0.0.0.0:8508 -w 4` | **Port**: 8508 (default)

## Code Style & Conventions

- **Framework**: Dash (not Streamlit) - use callbacks in `callbacks/`, layouts in `layouts/`, business logic in `core/`
- **Naming**: Functions/vars `snake_case`, Classes `PascalCase`, Constants `UPPER_SNAKE_CASE`
- **Imports**: Group stdlib, third-party, local; absolute imports only (`from core.fcff import ...`, never relative)
- **Types**: Use type hints from `typing` (`Optional`, `Dict`, `List`, `Tuple`, `pd.DataFrame`, `pd.Series`). All function signatures must have type hints
- **Docstrings**: Google style with Args/Returns sections for all public functions
- **Errors**: Use specific exceptions (`ValueError`, `KeyError`, `requests.HTTPError`), not bare `except:`. Return `None` for missing financial data
- **Logging**: Use `logging` module with `logger = logging.getLogger(__name__)` for debug/info messages

## Dash-Specific Guidelines

- **Callbacks**: Register in `callbacks/` module, use `prevent_initial_call=True` for button clicks
- **Component IDs**: Use descriptive kebab-case IDs (`ticker-input`, `analyze-button`, `fcff-data-store`)
- **Data Stores**: Use `dcc.Store` for sharing data between callbacks (see `app.py:39-41`)
- **No Comments**: Never add code comments unless specifically requested by the user

## Financial Data Guidelines

- **Tickers**: Always validate and convert to uppercase before API calls (`ticker.upper()`)
- **API Rate Limits**: SEC EDGAR requires 100ms delay (`time.sleep(0.1)`) between requests (10 req/sec limit)
- **User-Agent**: Required for SEC EDGAR: `"DCF Calculator Finance Club (contact@example.com)"`
- **Missing Data**: Handle gracefully with `None` returns and informative error messages
- **Data Validation**: Verify WACC > terminal_growth_rate to avoid division errors in DCF calculations

## Development Workflow

- **Git**: Feature branches only (`git checkout -b feature/name`), test modules independently before commit
- **Testing**: Manual test with known tickers (AAPL, MSFT, GOOGL). Verify financial calculations match expected values
- **Dependencies**: dash, dash-bootstrap-components, plotly, pandas, numpy, yfinance, requests, gunicorn (see pyproject.toml)
- **API Docs**: Include links in comments (e.g., `# EDGAR API: https://www.sec.gov/edgar/sec-api-documentation`)
