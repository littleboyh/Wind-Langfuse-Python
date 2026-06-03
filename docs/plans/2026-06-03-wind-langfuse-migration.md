# Wind Langfuse Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate the Wind Langfuse thin wrapper out of the local `langfuse-python` fork into this standalone package repository.

**Architecture:** The standalone package exposes `wind_langfuse.WindLangfuse` and depends on `langfuse==3.15.0` instead of vendoring upstream Langfuse source. The wrapper code keeps the existing naming, Wind attribute, trace update, native pass-through, and OpenTelemetry resource behavior.

**Tech Stack:** Python 3.10+, Poetry/PEP 517 packaging, `langfuse==3.15.0`, `opentelemetry-sdk`, pytest, ruff, mypy.

---

### Task 1: Add Standalone Package Metadata

**Files:**
- Create: `pyproject.toml`
- Modify: `README.md`

**Step 1: Create package metadata**

Create `pyproject.toml` with:

```toml
[tool.poetry]
name = "wind-langfuse-sdk"
version = "0.1.0"
description = "Wind wrapper SDK for Langfuse"
authors = ["wind"]
license = "MIT"
readme = "README.md"
packages = [{ include = "wind_langfuse" }]

[tool.poetry.dependencies]
python = ">=3.10,<4.0"
langfuse = "3.15.0"
opentelemetry-sdk = "^1.33.1"

[tool.poetry.group.dev.dependencies]
pytest = ">=7.4,<9.0"
ruff = "^0.15.2"
mypy = "^1.0.0"
build = "^1.2.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
log_cli = true

[tool.ruff]
target-version = "py310"

[tool.ruff.lint]
extend-select = ["I"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = false
warn_no_return = true
warn_unreachable = true
strict_equality = true
show_error_codes = true
show_column_numbers = true

[[tool.mypy.overrides]]
module = [
    "langfuse.*",
    "opentelemetry.*",
]
ignore_missing_imports = true
```

**Step 2: Update the README skeleton**

Replace the placeholder README with the Wind SDK README from the fork.

**Step 3: Commit**

```bash
git add pyproject.toml README.md
git commit -m "chore: add standalone package metadata"
```

### Task 2: Migrate Wrapper Tests First

**Files:**
- Create: `tests/test_wind_langfuse.py`

**Step 1: Copy the existing fake-based tests**

Copy `/Users/hqhe/git/langfuse-python/tests/test_wind_langfuse.py` into `tests/test_wind_langfuse.py`.

**Step 2: Run test to verify it fails before code exists**

Run:

```bash
python -m pytest tests/test_wind_langfuse.py -q
```

Expected: FAIL during import because `wind_langfuse` does not exist yet.

**Step 3: Commit**

```bash
git add tests/test_wind_langfuse.py
git commit -m "test: add wind langfuse wrapper tests"
```

### Task 3: Migrate Wrapper Package

**Files:**
- Create: `wind_langfuse/__init__.py`
- Create: `wind_langfuse/_version.py`
- Create: `wind_langfuse/client.py`
- Test: `tests/test_wind_langfuse.py`

**Step 1: Copy wrapper source**

Copy these files from `/Users/hqhe/git/langfuse-python/wind_langfuse/`:

- `__init__.py`
- `_version.py`
- `client.py`

**Step 2: Run wrapper tests**

Run:

```bash
python -m pytest tests/test_wind_langfuse.py -q
```

Expected: PASS.

**Step 3: Commit**

```bash
git add wind_langfuse tests/test_wind_langfuse.py
git commit -m "feat: migrate wind langfuse wrapper"
```

### Task 4: Migrate Usage Documentation

**Files:**
- Create: `WIND_SDK_USAGE.md`
- Modify: `README.md`

**Step 1: Copy usage documentation**

Copy `/Users/hqhe/git/langfuse-python/WIND_SDK_USAGE.md` into the new repository.

**Step 2: Check documentation references**

Verify the README links to `WIND_SDK_USAGE.md` and that verification commands reference the standalone repository paths.

**Step 3: Commit**

```bash
git add README.md WIND_SDK_USAGE.md
git commit -m "docs: migrate wind sdk usage guide"
```

### Task 5: Verify Package

**Files:**
- Verify: `pyproject.toml`
- Verify: `wind_langfuse/`
- Verify: `tests/test_wind_langfuse.py`
- Verify: `README.md`
- Verify: `WIND_SDK_USAGE.md`

**Step 1: Run tests**

```bash
python -m pytest tests/test_wind_langfuse.py -q
```

Expected: all tests pass.

**Step 2: Run lint**

```bash
python -m ruff check wind_langfuse tests
```

Expected: no lint errors.

**Step 3: Run build**

```bash
python -m build
```

Expected: source distribution and wheel are created under `dist/`.

**Step 4: Final status**

```bash
git status --short --branch
```

Expected: clean working tree, except for generated `dist/` artifacts if not ignored.
