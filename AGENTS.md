# AGENTS.md - Development Guidelines

## DCF Calculator - Finance Club ($300k Portfolio)

**Focus**: Functionality first, iterative development, proper git workflow

## Build/Test Commands

- **Run application**: `python main.py`
- **Install dependencies**: `uv add <package_name>`
- **Run tests**: `pytest` (when configured)
- **Test single function**: `pytest tests/test_dcf.py::test_calculate_npv -v`

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

### Naming Conventions

- Functions: snake_case (e.g., `calculate_dcf`)
- Classes: PascalCase (e.g., `DCFCalculator`)
- Constants: UPPER_SNAKE_CASE (e.g., `DISCOUNT_RATE`)
- Variables: snake_case (e.g., `cash_flows`)

### Error Handling

- Use specific exception types rather than bare `except:`
- Include meaningful error messages for financial calculations
- Consider validation for financial inputs (positive numbers, etc.)

### Testing Strategy

- Unit tests for core DCF calculations
- Integration tests for full valuation workflow
- Manual testing: Run with known company data
- Validation: Compare results with established DCF models

**Financial Accuracy Priority**: Given real money management, calculation correctness > code elegance

