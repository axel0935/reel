# Reel language: Spec v0.2

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



# v0.2 additions (v0.1 rules still apply)

## Reusable scenes
- A scene can take inputs: `SCENE greet WITH name` ... `CUT`.
  Several inputs are separated by commas: `SCENE add WITH a, b`.
- Scenes can be written in any order in the file.
- Run a scene with `CALL greet WITH "Ann"` (as a statement), or use it as
  a value: `SET total TO CALL add WITH 2, 3`.
  Inside a bigger expression, wrap it in parentheses: `x PLUS (CALL add WITH 2, 3)`.
- `GIVE BACK expression` ends the scene at once and returns a value.
  A scene without GIVE BACK returns NOTHING (a new value, printed as NOTHING).
- Variables created inside a scene stay inside that scene.
- A scene may call itself. After 100 nested calls, stop with a friendly error.
- Friendly errors: unknown scene, wrong number of inputs.

## Lists
- `SET cast TO LIST "Ann", "Bob"` creates a list. `SET empty TO LIST` makes an empty one.
  A LIST used inside CALL ... WITH must be wrapped in parentheses.
- `ADD value TO cast` adds at the end.
- `cast AT 1` gets an item. Counting starts at 1. Out of range = friendly error.
- `LENGTH OF value` gives the number of items in a list (or letters in a text).
  It applies to the single value right after it.
- `FOR EACH item IN cast` ... `END` runs once per item.
- `SAY cast` prints like: [Ann, Bob]

## While loops
- `WHILE condition` ... `END`. After 100000 turns, stop with a friendly error:
  "This loop never ends."

## Example
    SCENE double WITH n
      GIVE BACK n TIMES 2
    CUT

    SCENE main
      SET cast TO LIST "Ann", "Bob", "Cy"
      ADD "Dee" TO cast
      FOR EACH actor IN cast
        SAY "Hello " JOIN actor
      END
      SET total TO 0
      SET i TO 1
      WHILE NOT (i BIGGER THAN LENGTH OF cast)
        SET total TO total PLUS (CALL double WITH i)
        SET i TO i PLUS 1
      END
      SAY "Total: " JOIN total
    CUT

Expected output: Hello Ann / Hello Bob / Hello Cy / Hello Dee / Total: 20