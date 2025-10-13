# AI Strategy - Hands-off Granular Coding Assistance

## Philosophy: Preserve Cognitive Autonomy

**Primary Goal**: Save time on documentation lookups while maintaining independent problem-solving and architectural thinking.

**Core Principle**: AI should function as a "smart reference manual" rather than a coding tutor or implementation guide.

## What AI Should Provide

### ✅ Quick Reference Information
- **Build/test/run commands** - eliminate doc searching (`python main.py`, `pytest`, `uv add`)
- **API-specific requirements** - critical details easy to forget (SEC EDGAR User-Agent, rate limits)
- **Dependency lists** - what's already available vs what needs installing
- **Code style conventions** - naming, imports, type hints for consistency
- **Error patterns** - common pitfalls specific to this domain (bare `except:`, missing data handling)

### ✅ Domain-Specific Constants
- **Financial API endpoints** and required headers
- **XBRL concept tags** for EDGAR (`OperatingIncomeLoss`, `IncomeTaxExpenseBenefit`)
- **Rate limiting specs** (SEC: 10 req/sec, Yahoo Finance limits)
- **Known ticker symbols** for testing (AAPL, MSFT)
- **Financial calculation formulas** (FCFF = EBIT - Tax + D&A - CapEx - ΔWC)

### ✅ Environment Setup
- **Python version requirements** (3.13+)
- **Required dependencies** and their purposes
- **File structure expectations** (`data/`, module organization)
- **Testing approaches** (manual module testing, pytest when available)

## What AI Should NOT Provide

### ❌ Implementation Guidance
- Step-by-step coding instructions
- Architectural decisions or patterns
- Code examples that prime thinking
- "Best practices" that constrain approach
- Suggested file structures or organization

### ❌ Problem-Solving Assistance
- Breaking down complex problems into steps
- Suggesting algorithms or data structures
- Recommending libraries or frameworks
- Debugging strategies or troubleshooting guides

### ❌ Workflow Prescriptions
- Git workflow beyond basic commands
- Development methodologies
- Testing strategies beyond "test before commit"
- Code review processes

## Interaction Patterns

### Ideal AI Responses
- **Factual**: "SEC EDGAR requires User-Agent header: 'AppName (contact@email.com)'"
- **Reference**: "Available EDGAR concepts: OperatingIncomeLoss, IncomeTaxExpenseBenefit"
- **Command**: "Run single test: `pytest tests/test_file.py::test_function -v`"

### Avoid These Response Types
- **Prescriptive**: "You should implement error handling by..."
- **Tutorial**: "First, let's create a class that..."
- **Suggestive**: "Consider using a decorator pattern here..."
- **Explanatory**: "This approach is better because..."

## Domain-Specific Considerations

### Financial Data Integrity
- **Accuracy over elegance** - calculation correctness is paramount
- **Missing data handling** - return `None` rather than raising exceptions
- **Input validation** - ticker symbols should be uppercase
- **API reliability** - both EDGAR and Yahoo Finance can be unreliable

### Development Context
- **Real money implications** - this manages a $300k portfolio
- **Learning environment** - user is learning Streamlit through hands-on coding
- **Time efficiency** - minimize context switching to documentation
- **Cognitive load** - preserve mental capacity for problem-solving

## Success Metrics

### Positive Indicators
- User spends less time searching documentation
- User maintains ownership of architectural decisions
- User discovers implementation approaches independently
- Development velocity increases without cognitive dependency

### Warning Signs
- User stops thinking through problems independently
- User becomes reliant on AI for implementation decisions
- User's problem-solving skills atrophy
- AI responses become increasingly prescriptive

## Special Cases

### Streamlit Learning Mode
- **Role**: Coach and guide, not implementer
- **Approach**: Explain concepts, provide resources, ask guiding questions
- **Boundary**: Review user's code, don't write it for them
- **Goal**: User learns through hands-on experience

### Financial Calculations
- **Accuracy requirement**: Double-check formulas against established models
- **Transparency**: Document assumptions in code comments
- **Validation**: Test with known tickers and verify results
- **Error handling**: Graceful degradation when data unavailable

## Implementation Guidelines

### AI Agent Configuration
- Use concise, factual language
- Provide commands and constants without explanation
- Focus on "what" and "where" rather than "how" and "why"
- Include relevant documentation links for deep dives
- Minimize cognitive load in responses

### Knowledge Base Maintenance
- Keep API documentation links current
- Update rate limits and endpoint changes
- Maintain list of working test tickers
- Track common error patterns specific to finance APIs
- Document environment-specific requirements

## Review and Adaptation

This strategy should be evaluated periodically:
- **Monthly**: Review AI interaction patterns and user autonomy
- **Project milestones**: Assess whether goals are being met
- **When stuck**: Determine if more or less AI assistance is needed
- **After major features**: Evaluate impact on learning and development velocity

**Last Updated**: October 2025  
**Next Review**: November 2025