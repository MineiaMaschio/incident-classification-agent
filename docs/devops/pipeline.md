# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions to automate code quality checks, testing, and configuration validation. The pipeline runs automatically on every push and pull request to ensure code quality and system integrity.

---

## Pipeline Stages

### 1. **Lint** 🔍

**Purpose:** Enforce code style and detect common errors using Ruff.

**What it checks:**
- **E**: PEP 8 errors (whitespace, indentation, naming)
- **W**: PEP 8 warnings
- **F**: Pyflakes errors (undefined names, unused imports)
- **I**: isort errors (import sorting)

**Configuration:**
- Line length: 100 characters
- Target Python version: 3.12
- Ignored: E501 (line too long - handled by formatter)
- Excluded directories: tests, .venv, __pycache__, .pytest_cache

**Directories checked:**
- `src/` - Main source code
- `tests/` - Test files
- `api/` - API endpoints

**Command to run locally:**
```bash
ruff check src/ tests/ api/
```

**Output example:**
```
src/incident_classification_agent/main.py:10:1: F401 Unused import: os
error: 1 error
```

**How to fix lint errors:**
- Use `ruff check --fix` to auto-fix issues
- Manually resolve issues that require refactoring
- Ensure imports are organized (alphabetically sorted)

---

### 2. **Test** ✅

**Purpose:** Execute the test suite to validate functionality and catch regressions.

**What it checks:**
- All unit tests in `tests/` directory
- Test coverage and assertion failures
- Integration tests (if present)

**Configuration:**
- Test runner: pytest 9.1.1+
- Verbosity: verbose (-v flag)
- Traceback format: short (--tb=short)

**Command to run locally:**
```bash
python -m pytest tests/ -v --tb=short
```

**Expected output:**
```
tests/test_classify_incident.py::test_classify_incident PASSED
tests/test_save_occurrence.py::test_save_occurrence PASSED
...
79 passed, 1 skipped in 2.34s
```

**Interpreting test results:**
- **PASSED**: Test executed successfully
- **FAILED**: Test assertion failed or exception raised
- **SKIPPED**: Test was skipped (usually due to missing dependencies or markers)
- **XFAIL**: Expected failure (test marked as expected to fail)
- **ERROR**: Test setup/teardown failed

**Common failure causes:**
- Missing `.env` file or required environment variables
- Database connection issues
- External API unavailability
- Missing test fixtures

**How to debug test failures:**
```bash
# Run specific test
python -m pytest tests/test_classify_incident.py::test_classify_incident -v

# Run with full traceback
python -m pytest tests/ -v --tb=long

# Run with print statements
python -m pytest tests/ -v -s
```

---

### 3. **Validate Configuration** ⚙️

**Purpose:** Ensure required environment variables and configuration files are present.

**What it checks:**
1. `.env.example` file exists
2. `OLLAMA_MODEL` variable is defined in `.env.example`
3. `RESIDENTS_API_URL` variable is defined in `.env.example`

**Why these variables matter:**
- **OLLAMA_MODEL**: Specifies which LLM model to use (e.g., `qwen2.5:7b`)
- **RESIDENTS_API_URL**: Points to the residents API server (default: `http://localhost:8000`)

**Commands to check locally:**
```bash
# Check if file exists
test -f .env.example && echo "✓ .env.example found" || echo "✗ Missing .env.example"

# Check for variables
grep "OLLAMA_MODEL" .env.example && echo "✓ OLLAMA_MODEL found"
grep "RESIDENTS_API_URL" .env.example && echo "✓ RESIDENTS_API_URL found"
```

**How to fix validation errors:**
- Ensure `.env.example` exists in the project root
- Add missing environment variable definitions with placeholder values:
  ```
  OLLAMA_MODEL=
  RESIDENTS_API_URL=http://localhost:8000
  ```

---

## Pipeline Triggers

The pipeline runs automatically in these scenarios:

### Push Events
- **Branches:** `main`, `develop`, `feature/*`, `bugfix/*`
- **Trigger:** Any commit pushed to these branches

### Pull Requests
- **Target branches:** `main`, `develop`
- **Trigger:** Any PR opened or updated targeting these branches

---

## Workflow Status

View pipeline status:
1. Go to the repository on GitHub
2. Click "Actions" tab
3. Select the latest workflow run
4. View individual job results (lint, test, validate-config)

### Green ✓
All jobs passed. Safe to merge.

### Red ✗
At least one job failed. Check logs and fix issues before merging.

### Yellow ⏳
Pipeline is running. Wait for completion.

---

## Replicating Locally

To replicate the entire pipeline locally before pushing:

```bash
# 1. Set up environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 2. Run lint check
ruff check src/ tests/ api/

# 3. Run tests
python -m pytest tests/ -v --tb=short

# 4. Validate configuration
test -f .env.example && grep -q "OLLAMA_MODEL" .env.example && grep -q "RESIDENTS_API_URL" .env.example && echo "✓ Config valid" || echo "✗ Config invalid"
```

Or run all at once:
```bash
ruff check src/ tests/ api/ && \
python -m pytest tests/ -v --tb=short && \
echo "✓ All checks passed!"
```

---

## Environment Setup

### Required Python Version
- Python 3.12 or higher

### Installing Development Dependencies
```bash
pip install -e ".[dev]"
```

This installs:
- pytest (testing framework)
- ruff (code linter)
- All project dependencies

### Environment Variables
Create a `.env` file in the project root (use `.env.example` as template):
```bash
cp .env.example .env
```

Edit `.env` with your values:
```
OLLAMA_MODEL=qwen2.5:7b
RESIDENTS_API_URL=http://localhost:8000
```

---

## Troubleshooting

### Pipeline Fails with "ruff: command not found"
**Solution:** Install ruff or ensure it's in the Python environment
```bash
pip install ruff>=0.8.0
```

### Tests Fail with "pytest: command not found"
**Solution:** Install development dependencies
```bash
pip install -e ".[dev]"
```

### Config Validation Fails
**Solution:** Verify `.env.example` exists and contains required variables
```bash
cat .env.example | grep -E "OLLAMA_MODEL|RESIDENTS_API_URL"
```

### Import errors in tests
**Solution:** Ensure the package is installed in editable mode
```bash
pip install -e .
```

---

## Best Practices

1. **Run locally before pushing:** Use the replication commands above
2. **Fix lint issues immediately:** Don't ignore code style warnings
3. **Write tests for new features:** Maintain >80% code coverage
4. **Keep `.env.example` updated:** Add new environment variables here
5. **Review GitHub Actions logs:** Understand what failed and why
6. **Branch naming:** Use `feature/` or `bugfix/` prefixes for automatic CI

---

## CI/CD Configuration Files

- **Workflow definition:** `.github/workflows/ci.yml`
- **Ruff config:** `pyproject.toml` [tool.ruff] section
- **Pytest config:** `pyproject.toml` (can be extended with [tool.pytest.ini_options])
- **Environment template:** `.env.example`

---

## Performance Notes

- **Lint job:** ~30 seconds
- **Test job:** ~2-3 minutes (depends on test count)
- **Config validation:** <5 seconds
- **Total pipeline time:** ~3-4 minutes

---

## Future Enhancements

Potential additions to the pipeline:
- Code coverage reporting with coverage.py
- Security scanning with bandit or safety
- Type checking with mypy
- Documentation generation
- Automated versioning and releases
- Integration test environment setup
