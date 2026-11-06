' Monthly sales report
' Exercises arrays, FOR/NEXT (both directions), WHILE/WEND, SUB, FUNCTION,
' SELECT CASE and the string/number functions. Main code runs first and the
' procedures are defined at the bottom, the way a QuickBASIC program is
' usually laid out.
OPTION BASE 1

DIM month$(4)
DIM sales(4) AS DOUBLE
DIM total AS DOUBLE
DIM i AS INTEGER

month$(0) = "Jan"
month$(1) = "Feb"
month$(2) = "Mar"
month$(3) = "Apr"
month$(4) = "May"

FOR i = 0 TO 4
    sales(i) = 1000 + i * 250.5
    total = total + sales(i)
NEXT i

Banner "Monthly sales report", 24
Report total, 5

PRINT
FOR i = 4 TO 0 STEP -1
    PRINT month$(i); ": "; sales(i); "  "; Rating(sales(i))
NEXT i

PRINT "Total   : "; total
PRINT "Average : "; total / 5
PRINT "Digits in total: "; CountDigits(INT(total))

IF total > 7500 THEN
    PRINT "Target met."
ELSEIF total = 7500 THEN
    PRINT "Right on target."
ELSE
    PRINT "Below target."
END IF

SUB Banner (title AS STRING, width AS INTEGER)
    PRINT UCASE$(LEFT$(title, width))
    Line width
END SUB

SUB Report (amount AS DOUBLE, count AS INTEGER)
    PRINT "Rows: "; count; " at avg "; amount / count
END SUB

SUB Line (n AS INTEGER)
    DIM dash AS STRING
    dash = ""
    WHILE LEN(dash) < n
        dash = dash + "-"
    WEND
    PRINT dash
END SUB

FUNCTION Rating (amount AS DOUBLE) AS STRING
    SELECT CASE amount
        CASE 1000
            Rating = "low"
        CASE 1250.5, 1500.5
            Rating = "fair"
        CASE ELSE
            Rating = "good"
    END SELECT
END FUNCTION

FUNCTION CountDigits (n AS DOUBLE) AS INTEGER
    DIM rest AS DOUBLE
    DIM digits AS INTEGER
    rest = n
    IF rest < 0 THEN rest = -rest
    WHILE rest >= 1
        digits = digits + 1
        rest = INT(rest / 10)
    WEND
    CountDigits = digits
END FUNCTION

END
