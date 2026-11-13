# Reel: project rules (READ THIS FIRST)

Reel is a small programming language that reads like a movie script.
Files end with `.reel`. The human running this project is a beginner:
explain everything in plain, simple English.

## Who works where
- Devin: ONLY edit `core/` and `reel.py`
- Codex: ONLY edit `tests/`, `examples/`, `README.md`, `.github/` and `editor/`
- Antigravity: ONLY edit `playground/` and `site/`
- Everyone may ADD lines at the bottom of `docs/PROGRESS.md`

## Rules
1. Python 3.11+, standard library only. No installs without asking the human.
2. `docs/SPEC.md` is the law. Never change it. If something is unclear or
   seems wrong, write the question in `docs/QUESTIONS.md` and stop.
3. Work in small steps. After each task: say what you did in simple words,
   tell the human exactly how to check it works, add 2 lines to PROGRESS.md.
4. Do not re-read or rewrite the whole project each time (limited free quota).
5. Error messages must be friendly and always include the line number.

## Contract between the parts
- `core/reel/api.py` exposes: `run(source: str) -> dict`
  returning `{"output": str, "error": str or None}`.
  Tests and the playground ONLY use this function. They add `core/` to
  the Python import path.
- Run a file from the project root: `python3 reel.py run examples/hello.reel`


## Safe mode (v0.3)
`run(source, safe=False, base_dir=None)` in core/reel/api.py.
`safe=True` turns off file functions and `IMPORT "name"` (but `IMPORT LIB`
still works). `base_dir` is the folder used to find imported files and
`reel_files/`. The command line (`reel.py run file.reel`) uses safe=False
and base_dir = the folder of the file. The local playground and the online
site ALWAYS use safe=True.

## Online site contract (v0.3)
- `site/` is a static website with NO server. It runs Reel inside the browser
  with Pyodide, in a Web Worker that is stopped after 5 seconds.
- `site/build_site.py` (by Antigravity, standard library only) builds what the
  site needs: `site/reel.zip` (a zip of `core/reel`, without __pycache__),
  `site/examples/` (copy of examples/*.reel) and `site/examples.json` (list of
  example names). These generated files are never committed.
- The GitHub workflow (by Codex) runs the tests, runs
  `python3 site/build_site.py`, then deploys `site/` to GitHub Pages.
- The site must use relative URLs only (it is served under /reel/).