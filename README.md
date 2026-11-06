# BASIC Translator — Unit Tests

Pytest unit tests derived from the `features/*.feature` files, targeting the **Python backend** first (per the
feature-files README's suggested starting point). Each `tests/test_*.py` file mirrors one `.feature` file
one-for-one.

## Layout

```
basic_translator/
  __init__.py          # the translator's public interface (currently a stub)
tests/
  conftest.py           # shared fixtures: to_python(), run_python()
  test_output_print.py           <- features/output_print.feature
  test_input_statement.py        <- features/input_statement.feature
  test_variables_and_comments.py <- features/variables_and_comments.feature
  test_conditionals.py           <- features/conditionals.feature
  test_loops.py                  <- features/loops.feature
  test_arrays.py                 <- features/arrays.feature
  test_procedures.py             <- features/procedures.feature
  test_string_functions.py       <- features/string_functions.feature
  test_math_functions.py         <- features/math_functions.feature
  test_error_handling_and_diagnostics.py <- features/error_handling_and_diagnostics.feature
  test_multi_target_translation.py       <- features/multi_target_translation.feature
pytest.ini
```

> **Layout note:** the test files and `conftest.py` live at the repository root, not in
> `tests/`. The recovered copy had been flattened out of that directory, so `pytest.ini`
> points at the root instead.

## Status

`basic_translator/` now carries the Python backend -- lexer, recursive-descent parser, semantic checks and the
code generator -- taken from the `codegen` repository, so the suite runs against real behaviour rather than a
stub: `63 passed, 3 skipped in 2.55s`.

The three skips wait on interface additions, not missing behaviour: a warnings channel, a diagnostics-JSON
option, and a multi-target batch-run summary. None of those exist on `translate()` yet.

The backend here and the `codegen` repository are the same code; change both, or retire one.

## Running

```bash
pip install pytest
pytest -v
```

## Suggested workflow

1. Pick one test file (e.g. `test_output_print.py` — the smallest scope).
2. Implement just enough of `basic_translator/__init__.py`'s `python` branch (a real lexer/parser/codegen, even
   a minimal one) to make its tests pass.
3. Remove the `xfail` marker from that file once its tests genuinely pass (or leave `strict=False` xfail in place
   at the module level and let it show as `XPASS` until you're ready to clean it up — either is fine).
4. Move to the next file. `test_variables_and_comments.py` and `test_conditionals.py` are natural next steps since
   later files (`loops`, `procedures`, `arrays`) depend on those constructs existing.
5. Once the Python backend is solid, copy this pattern for the next target language: add a `SUPPORTED_TARGETS`
   branch in `basic_translator/__init__.py`, add a `to_<language>`/`run_<language>` fixture pair to `conftest.py`,
   and parametrize the existing tests (or duplicate the test files) for that target.
