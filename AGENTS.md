# AGENTS.md - Development Guidelines

## Build/Test Commands
- **Run**: `streamlit run main.py --server.port 8508` or `./run.sh` | **Install**: `uv add <package>` | **Test**: `pytest` (no tests yet)
- **Single test**: `pytest tests/test_file.py::test_function -v` | **Module test**: `python data/edgar_api.py` or `python core/dcf_valuation.py`

## Code Style & Conventions
- **Naming**: Functions/vars `snake_case`, Classes `PascalCase`, Constants `UPPER_SNAKE_CASE`
- **Imports**: Group stdlib, third-party, local; always use absolute imports (`from core.fcff import ...`)
- **Types**: Use type hints from `typing` (`Optional`, `Dict`, `List`, `Tuple`). All function signatures should have type hints
- **Docstrings**: Google style with Args/Returns sections for all public functions
- **Errors**: Use specific exceptions (ValueError, KeyError), not bare `except:`. Return `None` for missing financial data

## Financial Data Guidelines
- **Tickers**: Always validate and convert to uppercase before API calls
- **API Rate Limits**: SEC EDGAR requires 100ms delay (`time.sleep(0.1)`) between requests
- **User-Agent**: Required for SEC EDGAR: `"DCF Calculator Finance Club (contact@example.com)"`
- **Missing Data**: Handle gracefully with `None` returns and informative error messages
- **Data Validation**: Verify WACC > terminal_growth_rate to avoid division errors

## Development Workflow
- **Git**: Feature branches only (`git checkout -b feature/name`), test modules before commit
- **Testing**: Manual test with known tickers (AAPL, MSFT, GOOGL). Verify financial calculations
- **Dependencies**: pandas, numpy, matplotlib, requests, streamlit, yfinance (see pyproject.toml)
- **API Docs**: Include links in comments (e.g., `# EDGAR API: https://www.sec.gov/edgar/sec-api-documentation`)

## Streamlit Learning Mode
**ROLE**: Coach only - explain concepts, provide resources, guide debugging, review code. **DO NOT IMPLEMENT**

