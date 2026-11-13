# Reel language: Spec v0.1

A program is a list of scenes. Execution starts at `SCENE main`.
A scene ends with `CUT`. Keywords are UPPERCASE. Variable names use
lowercase letters, digits and `_`. Comments start with `--`.
Spaces at the start of a line do not matter. IF and REPEAT blocks end with END.

## Values
Numbers (10, 3.5), text ("hello"), and YES / NO.
Numbers like 10.0 are printed as 10.

## Statements
- `SET name TO expression`
- `SAY expression`  (prints one line)
- `IF condition` ... `OTHERWISE` ... `END`   (OTHERWISE is optional)
- `REPEAT number TIMES` ... `END`

## Expressions
- Math: PLUS, MINUS, TIMES, DIVIDED BY
- Text: `JOIN` glues two values as text, e.g. "Score: " JOIN score
- Compare: EQUALS, BIGGER THAN, SMALLER THAN
- Logic: AND, OR, NOT
- Parentheses ( ) and the usual order of operations

## Errors (friendly, with line number)
Unknown name, missing END, divide by zero, missing `SCENE main`.
Example: `Line 4: I don't know "villain". Did you SET it first?`

## Example
    SCENE main
      -- a tiny story
      SET hero TO 10
      SET villain TO hero PLUS 5
      SAY "Hello, world"
      IF villain BIGGER THAN 12
        SAY "The villain wins"
      OTHERWISE
        SAY "The hero wins"
      END
      REPEAT 3 TIMES
        SAY "Action!"
      END
    CUT