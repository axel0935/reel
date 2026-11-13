# Progress

- Built the Reel interpreter in core/reel/ (lexer, parser, interpreter, api.run) plus reel.py CLI and examples/hello.reel.
- Verified: `python3 reel.py run examples/hello.reel` prints Hello, world / The villain wins / Action! x3; errors show line numbers.
- Built the Reel web playground in playground/ (index.html, style.css, app.js, server.py) with a cinematic dark theme and example picker.
- Verified: `python3 playground/server.py` serves on http://localhost:8000, runs examples via core/reel/api.py, and shows friendly errors.
- 2026-11-13 — Codex: Added v0.2 contract tests for scenes, calls, lists, loops, recursion, and all v0.2 friendly errors.
- 2026-11-13 — Codex: Added five v0.2 examples, a beginner-friendly README, and automatic GitHub Actions test checks.
- Implemented Reel v0.2 in core/reel: scenes WITH inputs, CALL/GIVE BACK/NOTHING, lists (LIST, ADD, AT, LENGTH OF, FOR EACH), WHILE, and commas.
- Verified: all 34 tests pass (python3 -m unittest discover -s tests) and every examples/*.reel runs, including v02_demo.reel (Total: 20).
- Upgraded playground/ with syntax coloring (v0.2 keywords), line numbers, error line highlighting, URL hash sharing, and process safety limits (127.0.0.1, 20 KB limit, 5s timeout).
- Verified: tested syntax highlighting on v0.2 keywords, faulty line highlighting, URL hash code sharing, and confirmed 20 KB payload rejection and 5s subprocess timeout.
