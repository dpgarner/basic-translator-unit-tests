# BASIC Translator — Unit Tests

Pytest unit tests derived from the `features/*.feature` files, targeting the **Python backend** first (per the
feature-files README's suggested starting point). Each `tests/test_*.py` file mirrors one `.feature` file
one-for-one.

## Layout

```
basic_translator/
  __init__.py          # the translator's public interface
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
  test_example_programs.py               # end-to-end: examples/*.bas
examples/
  sales_report.bas       # realistic multi-construct program
pytest.ini
```

> **Layout note:** the test files and `conftest.py` live at the repository root, not in
> `tests/`. The recovered copy had been flattened out of that directory, so `pytest.ini`
> points at the root instead.

## Status

`basic_translator/` holds the Python backend -- lexer, recursive-descent parser, semantic checks and the code
generator -- taken from the `codegen` repository, so the suite runs against real behaviour: `72 passed`.

The interface also covers the three scenarios that used to be skipped. `translate(..., warnings=[...])`
collects warnings for constructs that translate but lose meaning, `translate(..., diagnostics=path)` writes a
JSON report of the run (including on failure), and `translate_many(source)` reports per-target pass/fail
instead of aborting on the first missing backend.

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

## Command line

```
python -m basic_translator program.bas                    # generated code on stdout
cat program.bas | python -m basic_translator -            # source from stdin
python -m basic_translator --out out.py program.bas       # write the code to a file
python -m basic_translator --all-targets --diagnostics report.json program.bas
```

Exit codes: 0 when the translation succeeded, 1 on a translation error (printed to
stderr with its category, and the `--diagnostics` report is still written), 2 on a
usage error. `--all-targets` prints one line per language and exits 0 if any target
worked; with `--diagnostics` the report lists every target's status.

## History

`docs/translator-worklog.md` records how this repository was recovered and
extended: the decisions, the bugs a realistic program exposed, the verification
runs and the remaining gaps.
