# AGENTS.md - Development Guidelines

## Build/Test Commands
- **Run**: `python main.py` | **Install**: `uv add <package>` | **Test**: `pytest` | **Single test**: `pytest tests/test_file.py::test_function -v`
- **Module test**: `python data/edgar_api.py` or `python data/yahoofin_api.py` | **Streamlit**: `streamlit run app.py`

## Code Style
- **Naming**: Functions/vars `snake_case`, Classes `PascalCase`, Constants `UPPER_SNAKE_CASE`
- **Imports**: Group stdlib, third-party, local. Include docstrings at module top
- **Types**: Use `typing` module (`Optional`, `Dict`, `List`). Prefer type hints
- **Errors**: Specific exceptions, not bare `except:`. Return `None` for missing financial data

## Development Rules
- **Git**: Feature branches, small commits, test before commit (`git checkout -b feature/name`)
- **API Integration**: Include API docs links in comments. Required User-Agent for SEC EDGAR
- **Financial Data**: Validate ticker inputs (uppercase). Handle missing items gracefully
- **Dependencies**: pandas, numpy, matplotlib, requests, streamlit, yfinance
- **Testing**: Manual test with known tickers (AAPL, MSFT). Verify financial accuracy

## Streamlit Learning Mode
**ROLE**: Coach only - explain concepts, provide resources, guide debugging, review code. **DO NOT IMPLEMENT**

