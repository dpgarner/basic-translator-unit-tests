# BASIC translator — worklog

A record of how this project was recovered and extended, kept with the code so the
reasoning survives the chat it happened in. It is a curated summary, not a raw
transcript: the decisions, the bugs, the evidence and the remaining limits.

The raw conversation lives in the Freebuff project; a new thread can reference it
with an `@` mention and search it in full.

## Where things stand

| Area | State |
| --- | --- |
| Backend | Python target only; lexer, recursive-descent parser, semantic checks, code generator |
| Public interface | `translate()`, `translate_many()`, `TargetResult`, `SUPPORTED_TARGETS` |
| Also exposed | warnings channel, JSON diagnostics report, command line |
| Tests | 72 passed (`pytest -q`) |
| Mirrored copy | `dpgarner/codegen` carries the same backend, byte-identical |

## What existed when this work started

The unit-test repository had been flattened out of its original layout during an
earlier salvage: `basic_translator` was a stub file at the repository root rather
than a package, and most tests were marked `xfail` because there was nothing behind
them. The real backend lived in `dpgarner/codegen`.

Rather than guess at names, the recovery worked from the GitHub repositories and the
local project folders, which is why the stub could be restored as a package instead
of rewritten from scratch.

## Timeline of decisions

1. **Restore the package, not a rewrite.** `basic_translator/` came back as a package
   (`848f14e`) and `pytest.ini` gained `testpaths = .`, since the recovered files sit
   at the repository root rather than in `tests/`.
2. **Wire in the real backend.** The `xfail` markers came off once `codegen`'s code
   was vendored in (`72fe2b2`), so the suite exercises real behaviour instead of
   placeholders.
3. **Close the three skipped scenarios** (`45a4c93`): a warnings channel, a JSON
   diagnostics report and per-target batch results.
4. **Expose all of it on the command line** (`efd0a0b`, mirrored in codegen `01b4f4b`),
   because warnings, diagnostics and batch results were otherwise reachable only from
   pytest.
5. **Test a whole program, not snippets** (`a8ed6af`, mirrored in codegen `7be890b`).
   Every earlier test checked one construct in isolation; a realistic program found
   six gaps (below).

## The interface

```python
translate(source, target="python", *, warnings=None, diagnostics=None) -> str
translate_many(source, targets=None) -> list[TargetResult]
```

* `warnings` is a list the call appends to. Warnings describe constructs that
  translate but lose meaning: `ON ERROR GOTO` (error handling is not translated) and
  `WHILE TRUE` (the translated loop never ends).
* `diagnostics` is a path; a JSON report is written there **including when the run
  fails**, with `{target, ok, warnings, error: {category, message, line}}`. A batch run
  writes `{"targets": [...]}` with one entry per language.
* `translate_many` reports a missing backend as a failed `TargetResult` instead of
  aborting the run. Only `python` has a backend; `typescript`, `kotlin`, `rust` and
  `erlang` are recognized and reported as unimplemented.

On the command line:

```
python -m basic_translator program.bas                 # generated code on stdout
cat program.bas | python -m basic_translator -         # source from stdin
python -m basic_translator --out out.py program.bas
python -m basic_translator --all-targets --diagnostics report.json program.bas
```

Exit codes: `0` translated, `1` translation error (message on stderr, diagnostics
still written), `2` usage error. The argument parser's program name is derived from
`__package__`, which keeps the two mirrored copies byte-identical.

## Bugs found by running a realistic program

`examples/sales_report.bas` is 85 lines: parallel arrays, `FOR` in both directions,
`WHILE`, two `SUB`s, two `FUNCTION`s, `SELECT CASE`, `ELSEIF`, and a bare `END`, with
main code first and procedures below it. Each of these was a real failure:

| Symptom | Cause | Fix |
| --- | --- | --- |
| `syntax: Unexpected token END` | Only `END IF/SUB/FUNCTION/SELECT` had rules; a bare `END` had none | New `End` node, generating `_sys.exit(0)`, so it stops where it appears |
| `NameError: v_banner` | Python needs `def` before use; BASIC lets a procedure be called before its definition | Procedures are emitted ahead of the main code |
| `Unexpected token ELSE after statement` | Single-line `IF ... THEN ... ELSE ...` parsed only the THEN branch | Single-line ELSE is parsed into the else body |
| `Expected NEXT but found EOF` | A `NEXT` closing two loops was treated as the inner loop's own | The parser counts how many enclosing loops a `NEXT` list closes |
| `Expected COMMA but found SEMI` | `INPUT "Name"; n$` was rejected; QuickBASIC accepts either separator | Both separators accepted |

Two of those (`END`, procedure order) are the kind of thing that only shows up when
the program is a program rather than a snippet.

## Semantics worth knowing

* **PRINT** follows the recovered feature specs, not QuickBASIC's sign column:
  numbers print plainly, and one space separates two adjacent numeric items. Strings
  are untouched, so `PRINT "Total: "; total` keeps the literal's spacing.
* **Arrays** are 0-based and sized as `DIM a(4)` meaning indices 0 through 4.
  Out-of-range *literal* indices are rejected before code generation.
* **Variables** must be declared (or assigned, `INPUT`, a loop variable, a parameter)
  before use; a reference to an unknown name is a `semantic` error, not a cryptic
  runtime failure.
* **Unsupported by design**, each with a clear category rather than a crash: `GOTO`
  and line numbers, `GOSUB`, `SHELL` (refused for safety), `PRINT USING`,
  `CASE ... TO` ranges.

## Known gaps

* `DIM a(1 TO 5)` lower bounds are not parsed — deliberately left unimplemented
  rather than silently approximated as a 0-based array, which would hide
  out-of-range index 0.
* `DO ... LOOP` is not in the dialect; `WHILE ... WEND` is.
* No backend exists for the other four targets.
* The mirrored copy means every backend change must land twice. The copies are
  checked with `cmp` (all of `__init__.py`, `__main__.py`, `codegen_python.py`,
  `lexer.py`, `parser.py`, `semantics.py`, `errors.py`, `basic_ast.py`).

## Verification used

* `pytest -q` → `72 passed`, up from 66 when the CLI work began.
* The CLI end to end: file and stdin input, both generated programs executed, `--out`
  leaving stdout empty, the five-line batch summary, diagnostics JSON for success,
  batch and failure, a warning on stderr with code still produced, `--help`, and exit
  codes 0, 1 and 2.
* `python -m codegen examples/sales_report.bas` producing the same output as the
  mirror, with all eight backend files comparing identical.
* `examples/sales_report.bas` is asserted line for line in
  `test_example_programs.py`, so its arithmetic is checked, not just its translation.

## Commits

`dpgarner/basic-translator-unit-tests`

| Commit | Purpose |
| --- | --- |
| `848f14e` | Restore `basic_translator` as a package |
| `72fe2b2` | Vendored backend wired in; `xfail` markers removed |
| `45a4c93` | Warnings channel, diagnostics report, batch translation |
| `efd0a0b` | Command line entry point |
| `a8ed6af` | Whole-program fixes plus `examples/sales_report.bas` and its tests |
| `d975514`, `b8abf42`, `b4341a8` | README repair (test count, code fence) |

`dpgarner/codegen`

| Commit | Purpose |
| --- | --- |
| `720dbac`, `a7f0851` | Interface changes mirrored |
| `01b4f4b` | Command line entry point mirrored |
| `7be890b` | Whole-program fixes and the example mirrored |

## About this record

Two cautions applied when writing it, and apply to any copy:

* It names local paths and repository names but contains **no personal data** — no
  bookmark exports, no vault databases, no chat exports.
* It is a summary with the reasoning and the evidence. The authoritative account of
  any individual change is its commit message, and the authoritative behaviour is the
  test suite.
