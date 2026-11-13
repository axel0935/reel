# Reel language: Spec v0.3

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


# v0.3 additions (v0.1 and v0.2 rules still apply)

## Calling a scene with no input
A scene with no inputs is called with just `CALL name` (no WITH).

## Safe mode
Reel can run in "safe mode" (used by the online site and the playground).
In safe mode, file functions and `IMPORT "name"` are turned off and give the
friendly error: `Line 3: Files are turned off here.` (or `Importing files
is turned off here.`). `IMPORT LIB` still works.

## IMPORT
- `IMPORT "name"` (written at the top of the file, before any SCENE) loads
  `name.reel` from the same folder as the running file.
- `IMPORT LIB "name"` loads a library that ships with Reel
  (core/reel/lib/name.reel).
- Only the scenes of an imported file are loaded. Its `SCENE main` is ignored.
- Two scenes with the same name, or a scene named like a built-in scene,
  give a friendly error. Circular imports give a friendly error.
- Errors inside an imported file name that file: `maths.reel, Line 4: ...`
- Libraries that ship with Reel (written in Reel itself):
  - `maths`: max_of WITH a, b / min_of WITH a, b / average WITH list
    (an empty list gives 0) / is_even WITH n / power WITH base, times
    (times is a whole number, 0 or more)
  - `fun`: shout WITH text (upper case + "!") / coin_flip ("heads" or "tails")
    / dice (a whole number from 1 to 6)

## Built-in scenes (always available, called with CALL)
Chance
- `random_between WITH low, high`: a whole number from low to high, both included
- `random_pick WITH list`: one random item (empty list = friendly error)
- `shuffle WITH list`: a new list in random order
Words
- `upper WITH text` / `lower WITH text` / `trim WITH text`
- `split WITH text, separator`: a list of texts
- `glue WITH list, separator`: one text
- `replace WITH text, old, new`
- `contains WITH text, part`: YES or NO (also works with a list and an item)
- `starts_with WITH text, part`: YES or NO
- `to_number WITH text`: a number (not a number = friendly error)
Dates (a date is a text like "2026-11-13"; a wrong date = friendly error)
- `today`: today's date / `now`: the time as "HH:MM" (24 hours)
- `days_between WITH date1, date2`: whole number (date2 minus date1)
- `add_days WITH date, n`: a date / `weekday WITH date`: "Monday", "Tuesday"...
Files (turned off in safe mode)
- `read_file WITH name` (text) / `read_lines WITH name` (list of texts)
- `write_file WITH name, text` (replaces) / `append_file WITH name, text`
- `file_exists WITH name`: YES or NO
- Files live ONLY in a folder called `reel_files` next to the program
  (created at the first write). A name must be a simple file name: no `/`,
  no `..`. A file may not be bigger than 1 MB. A missing file = friendly error.

## Example (examples/v03_demo.reel)
    IMPORT LIB "fun"

    SCENE main
      SET roll TO CALL dice
      SAY "You rolled " JOIN roll
      SET d TO CALL today
      SAY "Today is " JOIN (CALL weekday WITH d)
      SET words TO CALL split WITH "the quick brown fox", " "
      SAY CALL shout WITH (CALL random_pick WITH words)
    CUT

Expected: a line with a number from 1 to 6, a line with today's weekday in
English, then one of the four words in capitals followed by "!".