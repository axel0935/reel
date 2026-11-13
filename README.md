# Reel

Reel is a tiny programming language that reads a little like a movie script.
Reel files end in `.reel`. A program has scenes, and it starts at the scene
named `main`.

## A short language tour

Print a line with `SAY`, and save a value with `SET`:

```reel
SCENE main
  SET hero TO "Ada"
  SAY "Hello, " JOIN hero
CUT
```

Use `IF` and `REPEAT` to make choices and repeat actions:

```reel
SCENE main
  SET stars TO 3
  IF stars BIGGER THAN 2
    REPEAT stars TIMES
      SAY "Twinkle!"
    END
  END
CUT
```

Scenes can be reusable. Give them inputs with `WITH`, run them with `CALL`,
and send a value back with `GIVE BACK`:

```reel
SCENE double WITH number
  GIVE BACK number TIMES 2
CUT

SCENE main
  SET answer TO CALL double WITH 21
  SAY answer
CUT
```

Lists hold several values. Counting with `AT` starts at 1:

```reel
SCENE main
  SET cast TO LIST "Ann", "Bob"
  ADD "Cy" TO cast
  SAY cast AT 1
  FOR EACH actor IN cast
    SAY "Hello " JOIN actor
  END
CUT
```

Try `examples/v02_demo.reel` for a larger v0.2 program with lists, a loop,
and a reusable scene.

## Run a Reel file

From the project folder, run:

```bash
python3 reel.py run examples/v02_demo.reel
```

## Run the tests

From the project folder, run:

```bash
python3 -m unittest discover -s tests -v
```

The project uses only Python's built-in tools, so there is nothing to install.

## Start the playground

From the project folder, run:

```bash
python3 playground/server.py
```

Then open [http://localhost:8000](http://localhost:8000) in a web browser.
