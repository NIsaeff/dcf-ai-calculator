# Git Branch Information

## Branches in this Repository

### `main` - Original Streamlit Version
- Legacy Streamlit implementation
- Last updated before migration to Dash
- **Status:** Archived/Reference only
- **Use:** Historical reference

### `stlit` - Enhanced Streamlit Version
- Streamlit with attempted bug fixes
- Added debugging improvements
- Added caching attempts
- Includes comparison documentation (MIGRATION_TO_DASH.md, FRAMEWORK_COMPARISON.md, REACT_VS_PYTHON.md)
- **Status:** Preserved but not recommended for use
- **Use:** Reference for what didn't work

### `dash` - Production Dash Version (CURRENT)
- ✅ **Production-ready** Dash implementation
- Callback-based architecture
- Clean, minimal structure
- No Streamlit dependencies
- **Status:** Active development
- **Use:** Main development branch

---

## Which Branch to Use?

**For Development:** `dash` (this branch)
**For Reference:** `stlit` (to see what we learned)
**For History:** `main` (original version)

---

## Pushing Changes

You'll need to push manually due to authentication:

```bash
# Push current branch
git push origin dash

# Push all branches (if needed)
git push origin --all
```

Your git remote: `https://nateisaeff.com/git/SMC_Finance_Club/DCF_Calculator`

---

## Migration History

1. **main** → Built initial Streamlit version
2. **stlit** → Attempted to fix Streamlit bugs (failed)
3. **dash** → Migrated to Dash (successful!)

Current branch (`dash`) is clean and production-ready.
