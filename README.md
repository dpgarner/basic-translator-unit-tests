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

## Why everything is currently `xfail`

`basic_translator/__init__.py` defines the **contract** (`translate(basic_source, target) -> str`, plus
`TranslationError` / `UnsupportedTargetError`) but no real parsing or code generation yet — every Python-target
call raises `NotImplementedError`. Tests that exercise the Python backend are marked
`@pytest.mark.xfail(raises=NotImplementedError, strict=False)`, so:

- **Today**: `pytest` runs clean (xfail, not fail) — this is the TDD "red" state, made visible instead of hidden.
- **As you implement a piece of the backend**: the corresponding test(s) start **passing**, which pytest will
  report as `XPASS`. Because `strict=False`, that's not a failure — but it's your signal to delete the `xfail`
  marker for that test (or split it into its own un-marked test) once real behavior backs it.

A few tests are **not** marked xfail and pass right now, because they test the interface's architecture rather
than the Python backend itself — e.g. `test_multi_target_translation.py` checks that requesting an
unimplemented target (`kotlin`, `rust`, ...) raises a clear `UnsupportedTargetError` rather than crashing.

Three tests are `pytest.skip`'d with a note explaining what interface addition they're waiting on (a warnings
channel, a diagnostics-JSON option, and a multi-target batch-run summary) — none of that surface exists on
`translate()` yet, so there's nothing to assert against.

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
