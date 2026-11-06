"""End-to-end tests: the example programs must translate and run as a whole.

`examples/sales_report.bas` is a realistic multi-construct program -- arrays,
FOR/NEXT in both directions, WHILE/WEND, SUB, FUNCTION, SELECT CASE -- with its
main code first and the procedures defined afterwards. It exists because the
per-feature tests each check one statement in isolation; this one checks that a
whole program survives the trip.
"""

from pathlib import Path

from basic_translator import translate

EXAMPLES = Path(__file__).parent / "examples"


def test_sales_report_translates_and_runs(run_python):
    source = (EXAMPLES / "sales_report.bas").read_text(encoding="utf-8")
    output = run_python(translate(source, target="python"))
    assert output.splitlines() == [
        "MONTHLY SALES REPORT",
        "-" * 24,
        "Rows: 5 at avg 1501",
        "",
        "May: 2002  good",
        "Apr: 1751.5  good",
        "Mar: 1501  good",
        "Feb: 1250.5  fair",
        "Jan: 1000  low",
        "Total   : 7505",
        "Average : 1501",
        "Digits in total: 4",
        "Target met.",
    ]


def test_bare_end_stops_the_program(to_python, run_python):
    # Scenario: Translate a bare END as "stop here, successfully"
    code = to_python(
        """
        PRINT "before"
        END
        PRINT "after"
        """
    )
    assert run_python(code).splitlines() == ["before"]


def test_procedures_called_before_their_definition(to_python, run_python):
    # Scenario: Call a FUNCTION and a SUB declared after the calling code
    code = to_python(
        """
        PRINT Twice(21)
        Shout "hi"
        FUNCTION Twice (n AS INTEGER) AS INTEGER
            Twice = n * 2
        END FUNCTION
        SUB Shout (word AS STRING)
            PRINT UCASE$(word)
        END SUB
        """
    )
    assert run_python(code).splitlines() == ["42", "HI"]
