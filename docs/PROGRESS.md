# Progress

- Built the Reel interpreter in core/reel/ (lexer, parser, interpreter, api.run) plus reel.py CLI and examples/hello.reel.
- Verified: `python3 reel.py run examples/hello.reel` prints Hello, world / The villain wins / Action! x3; errors show line numbers.
- Built the Reel web playground in playground/ (index.html, style.css, app.js, server.py) with a cinematic dark theme and example picker.
- Verified: `python3 playground/server.py` serves on http://localhost:8000, runs examples via core/reel/api.py, and shows friendly errors.
- 2026-11-13 — Codex: Added v0.2 contract tests for scenes, calls, lists, loops, recursion, and all v0.2 friendly errors.
- 2026-11-13 — Codex: Added five v0.2 examples, a beginner-friendly README, and automatic GitHub Actions test checks.
- 2026-11-13 — Codex: Added v0.3 API-only tests for imports, safe mode, libraries, built-ins, files, and friendly errors.
- 2026-11-13 — Codex: Added v0.3 examples, the VSCodium extension, online-use documentation, and the Pages deployment workflow.
- Implemented Reel v0.2 in core/reel: scenes WITH inputs, CALL/GIVE BACK/NOTHING, lists (LIST, ADD, AT, LENGTH OF, FOR EACH), WHILE, and commas.
- Verified: all 34 tests pass (python3 -m unittest discover -s tests) and every examples/*.reel runs, including v02_demo.reel (Total: 20).
- Upgraded playground/ with syntax coloring (v0.2 keywords), line numbers, error line highlighting, URL hash sharing, and process safety limits (127.0.0.1, 20 KB limit, 5s timeout).
- Verified: tested syntax highlighting on v0.2 keywords, faulty line highlighting, URL hash code sharing, and confirmed 20 KB payload rejection and 5s subprocess timeout.
- Session A of v0.3: added IMPORT "name" / IMPORT LIB "name" (loader.py with circular-import, missing-file, name-clash and per-file error names), CALL name without WITH, safe mode run(source, safe, base_dir), --safe flag in reel.py, and core/reel/lib/maths.reel + fun.reel.
- Verified: 34 tests still pass; manual checks for imports, safe mode, and all friendly errors work.
- Session B of v0.3: added core/reel/builtins.py with all built-in scenes (chance, words, dates, files), wired into call_scene, BUILTIN_SCENE_NAMES blocks user name clashes, files restricted to reel_files/ with 1 MB limit and safe-mode lockout.
- Verified: 52 tests pass; all builtins, file read/write/append, safe mode, lib fun.reel (dice/coin_flip/shout) and maths.reel work.
