# AGENTS.md - Development Guidelines

## DCF Calculator - Finance Club ($300k Portfolio)

**Focus**: Functionality first, iterative development, proper git workflow

## Build/Test Commands

- **Run application**: `python main.py`
- **Install dependencies**: `uv add <package_name>`
- **Run data modules**: `python data/edgar_api.py` or `python data/yahoofin_api.py`
- **Run tests**: `pytest` (when configured)
- **Test single function**: `pytest tests/test_dcf.py::test_calculate_npv -v`
- **Python version**: 3.13+ (see .python-version)

## Iterative Development Workflow

### Git Workflow (Critical for $300k App)

- **Feature branches**: `git checkout -b feature/dcf-core-calculation`
- **Small commits**: One logical change per commit
- **Test before commit**: Always run `python main.py` to verify functionality
- **Commit message format**: `feat: add basic DCF calculation logic`
- **Never commit broken code**: Each commit should be runnable

### AI-Enhanced Development Rules

- **RULE OF THUMB**: Keep things simple, then add complexity as needed
- **MINIMAL CHANGES**: Only implement exactly what's requested, nothing extra
- **ONE FEATURE AT A TIME**: Complete and test before moving to next
- **ASK BEFORE IMPLEMENTING**: Confirm scope and approach before coding
- **NO OVERBUILDING**: Do not create folders, files, or features without explicit request
- **API DOCUMENTATION**: Provide links to relevant API documentation when introducing new API calls
- **VERIFY ASSUMPTIONS**: Ask for clarification on financial formulas
- **DOCUMENT DECISIONS**: Explain DCF assumptions in code comments
- **FAIL FAST**: Simple validation for financial inputs (no negative cash flows)

### Code Style Guidelines

- **Functions**: snake_case (e.g., `calculate_dcf`, `get_ebit`)
- **Classes**: PascalCase (e.g., `DCFCalculator`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DISCOUNT_RATE`)
- **Variables**: snake_case (e.g., `cash_flows`, `ticker`)
- **Imports**: Group stdlib, third-party, local imports with docstrings at top
- **Type hints**: Use `typing` module for Optional, Dict, List types
- **Docstrings**: Use triple quotes with brief function description

### Error Handling & Financial Data

- Use specific exceptions, not bare `except:`
- Print meaningful error messages for API failures
- Return `None` for missing financial data (don't raise)
- Validate ticker inputs (uppercase conversion)
- Handle missing financial statement items gracefully

### Dependencies & APIs

- **Core**: pandas, numpy, matplotlib, requests, streamlit
- **Finance**: yfinance for Yahoo Finance data
- **SEC EDGAR**: Custom API integration with required User-Agent headers
- **API Docs**: Always include API documentation links in code comments

### Testing Strategy

- Manual testing: Run individual modules with ticker input prompts
- Unit tests for core DCF calculations (when added)
- API validation: Test with known tickers (AAPL, MSFT)
- Financial accuracy verification against established models

### Streamlit Learning Mode (IMPORTANT)

**ROLE**: Streamlit Coach & Learning Facilitator - **DO NOT IMPLEMENT FOR USER**

**Teaching Approach**:
- 🎯 **Explain concepts** before suggesting implementation
- 📚 **Provide learning resources** and documentation links  
- 🤔 **Ask guiding questions** to help user discover solutions
- 🔍 **Help debug** when user runs into issues
- ✅ **Review user's code** and suggest improvements
- 🚫 **Don't write the code** - guide user to write it themselves

**Learning Phases**:
1. **Streamlit Basics**: Pages, widgets, layout, data display
2. **DCF Calculator UI**: Input forms, data visualization, interactivity
3. **Advanced Features**: Caching, session state, error handling

**Commands**:
- **Run Streamlit**: `streamlit run app.py`
- **Streamlit docs**: https://docs.streamlit.io/

**Financial Accuracy Priority**: Given real money management, calculation correctness > code elegance

