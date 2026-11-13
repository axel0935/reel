# Reel: project rules (READ THIS FIRST)

Reel is a small programming language that reads like a movie script.
Files end with `.reel`. The human running this project is a beginner:
explain everything in plain, simple English.

## Who works where
- Devin: ONLY edit `core/` and `reel.py`
- Codex: ONLY edit `tests/` and `examples/`
- Antigravity: ONLY edit `playground/`
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