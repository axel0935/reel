"""Contract tests for every Reel v0.3 feature.

The interpreter is used only through its public ``run`` function.  Temporary
folders make the import and file tests independent from a developer's machine.
"""

from pathlib import Path
import re
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from reel.api import run  # noqa: E402


def program(body: str) -> str:
    return f"SCENE main\n{body}\nCUT\n"


class ReelV03SpecTests(unittest.TestCase):
    """SPEC v0.3 behaviour, including imports, libraries, and safe mode."""

    def assert_runs(self, source: str, expected: str, **options: object) -> None:
        result = run(source, **options)
        self.assertIsNone(result["error"], result["error"])
        self.assertEqual(result["output"], expected)

    def assert_v03_error(self, source: str, **options: object) -> str:
        result = run(source, **options)
        self.assertIsInstance(result["output"], str)
        self.assertIsNotNone(result["error"])
        self.assertRegex(result["error"], r"Line \d+")
        self.assertNotRegex(
            result["error"].lower(),
            r"do not understand|expected the line|character|do not know a scene",
        )
        return result["error"]

    def test_call_without_with_runs_a_scene_with_no_inputs(self) -> None:
        self.assert_runs(
            "SCENE bell\nSAY \"ring\"\nCUT\n"
            "SCENE main\nCALL bell\nCUT\n",
            "ring\n",
        )

    def test_import_loads_scenes_but_ignores_imported_main(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "helper.reel").write_text(
                "SCENE greeting\nSAY \"hello from helper\"\nCUT\n"
                "SCENE main\nSAY \"this must stay quiet\"\nCUT\n",
                encoding="utf-8",
            )
            self.assert_runs(
                'IMPORT "helper"\nSCENE main\nCALL greeting\nCUT\n',
                "hello from helper\n",
                base_dir=folder,
            )

    def test_import_is_turned_off_in_safe_mode(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            error = self.assert_v03_error(
                'IMPORT "helper"\nSCENE main\nCUT\n', safe=True, base_dir=folder
            )
        self.assertIn("importing files is turned off", error.lower())

    def test_import_lib_still_works_in_safe_mode(self) -> None:
        self.assert_runs(
            'IMPORT LIB "maths"\nSCENE main\nSAY CALL max_of WITH 2, 7\nCUT\n',
            "7\n",
            safe=True,
        )

    def test_duplicate_scene_names_are_a_friendly_error(self) -> None:
        self.assert_v03_error(
            "SCENE helper\nCUT\nSCENE helper\nCUT\nSCENE main\nCUT\n"
        )

    def test_scene_name_cannot_replace_a_builtin_scene(self) -> None:
        self.assert_v03_error("SCENE upper WITH text\nCUT\nSCENE main\nCUT\n")

    def test_circular_imports_are_a_friendly_error(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "one.reel").write_text(
                'IMPORT "two"\nSCENE one\nCUT\n', encoding="utf-8"
            )
            Path(folder, "two.reel").write_text(
                'IMPORT "one"\nSCENE two\nCUT\n', encoding="utf-8"
            )
            self.assert_v03_error(
                'IMPORT "one"\nSCENE main\nCUT\n', base_dir=folder
            )

    def test_error_in_imported_file_names_that_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "broken.reel").write_text(
                "SCENE helper\nSAY unknown_name\nCUT\n", encoding="utf-8"
            )
            error = self.assert_v03_error(
                'IMPORT "broken"\nSCENE main\nCALL helper\nCUT\n', base_dir=folder
            )
        self.assertIn("broken.reel, line 2", error.lower())

    def test_maths_library_scenes(self) -> None:
        self.assert_runs(
            'IMPORT LIB "maths"\n'
            "SCENE main\n"
            "SAY CALL max_of WITH 3, 9\n"
            "SAY CALL min_of WITH 3, 9\n"
            "SAY CALL average WITH (LIST 2, 4, 6)\n"
            "SAY CALL average WITH (LIST)\n"
            "SAY CALL is_even WITH 8\n"
            "SAY CALL power WITH 3, 0\n"
            "SAY CALL power WITH 2, 4\n"
            "CUT\n",
            "9\n3\n4\n0\nYES\n1\n16\n",
        )

    def test_fun_library_scenes_and_random_result_types(self) -> None:
        result = run(
            'IMPORT LIB "fun"\n'
            "SCENE main\n"
            'SAY CALL shout WITH "quiet"\n'
            "SAY CALL coin_flip\n"
            "SAY CALL dice\n"
            "CUT\n"
        )
        self.assertIsNone(result["error"], result["error"])
        shout, flip, die = result["output"].splitlines()
        self.assertEqual(shout, "QUIET!")
        self.assertIn(flip, {"heads", "tails"})
        self.assertTrue(die.isdecimal())
        self.assertIn(int(die), range(1, 7))

    def test_chance_builtins_return_values_in_the_promised_ranges(self) -> None:
        result = run(
            "SCENE main\n"
            "SAY CALL random_between WITH 4, 8\n"
            'SAY CALL random_pick WITH (LIST "red", "blue")\n'
            'SAY CALL shuffle WITH (LIST "red", "blue", "green")\n'
            "CUT\n"
        )
        self.assertIsNone(result["error"], result["error"])
        number, picked, shuffled = result["output"].splitlines()
        self.assertIn(int(number), range(4, 9))
        self.assertIn(picked, {"red", "blue"})
        self.assertEqual(sorted(shuffled[1:-1].split(", ")), ["blue", "green", "red"])

    def test_word_builtins(self) -> None:
        self.assert_runs(
            "SCENE main\n"
            'SAY CALL upper WITH "hello"\n'
            'SAY CALL lower WITH "HeLLo"\n'
            'SAY CALL trim WITH "  hello  "\n'
            'SAY CALL split WITH "a,b,c", ","\n'
            'SAY CALL glue WITH (LIST "a", "b", "c"), "+"\n'
            'SAY CALL replace WITH "pop pop", "pop", "hop"\n'
            'SAY CALL contains WITH "reel movie", "movie"\n'
            'SAY CALL contains WITH (LIST "a", "b"), "b"\n'
            'SAY CALL starts_with WITH "reel", "re"\n'
            'SAY CALL to_number WITH "12.5"\n'
            "CUT\n",
            "HELLO\nhello\nhello\n[a, b, c]\na+b+c\nhop hop\nYES\nYES\nYES\n12.5\n",
        )

    def test_date_builtins(self) -> None:
        result = run(
            "SCENE main\n"
            "SAY CALL today\n"
            "SAY CALL now\n"
            'SAY CALL days_between WITH "2026-11-13", "2026-11-16"\n'
            'SAY CALL add_days WITH "2026-11-13", 2\n'
            'SAY CALL weekday WITH "2026-11-13"\n'
            "CUT\n"
        )
        self.assertIsNone(result["error"], result["error"])
        today, now, days, added, weekday = result["output"].splitlines()
        self.assertRegex(today, r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(now, r"^\d{2}:\d{2}$")
        self.assertEqual((days, added, weekday), ("3", "2026-11-15", "Friday"))

    def test_random_pick_empty_to_number_and_bad_date_are_friendly_errors(self) -> None:
        for source in (
            program("SAY CALL random_pick WITH (LIST)"),
            program('SAY CALL to_number WITH "not-a-number"'),
            program('SAY CALL weekday WITH "not-a-date"'),
        ):
            with self.subTest(source=source):
                self.assert_v03_error(source)

    def test_file_builtins_write_append_read_lines_and_exists(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            self.assert_runs(
                "SCENE main\n"
                'CALL write_file WITH "hello.txt", "Hello"\n'
                'CALL append_file WITH "hello.txt", " file"\n'
                'SAY CALL read_file WITH "hello.txt"\n'
                'SAY CALL read_lines WITH "hello.txt"\n'
                'SAY CALL file_exists WITH "hello.txt"\n'
                "CUT\n",
                "Hello file\n[Hello file]\nYES\n",
                base_dir=folder,
            )

    def test_file_builtins_are_turned_off_in_safe_mode(self) -> None:
        error = self.assert_v03_error(
            program('SAY CALL file_exists WITH "hello.txt"'), safe=True
        )
        self.assertIn("files are turned off", error.lower())

    def test_missing_and_unsafe_file_names_are_friendly_errors(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            sources = (
                program('SAY CALL read_file WITH "missing.txt"'),
                program('CALL write_file WITH "folder/no.txt", "x"'),
                program('CALL write_file WITH "../no.txt", "x"'),
            )
            for source in sources:
                with self.subTest(source=source):
                    self.assert_v03_error(source, base_dir=folder)

    def test_file_larger_than_one_megabyte_is_a_friendly_error(self) -> None:
        too_large = "x" * (1024 * 1024 + 1)
        with tempfile.TemporaryDirectory() as folder:
            self.assert_v03_error(
                program(f'CALL write_file WITH "big.txt", "{too_large}"'),
                base_dir=folder,
            )


if __name__ == "__main__":
    unittest.main()
