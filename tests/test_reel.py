"""Contract tests for Reel v0.1.

These tests deliberately talk to the language through its public `run` function
only.  That keeps them independent from the parser and evaluator internals.
"""

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from reel.api import run  # noqa: E402


def program(body: str, scene: str = "main") -> str:
    """Put statement text into one complete Reel scene."""
    return f"SCENE {scene}\n{body}\nCUT\n"


class ReelSpecTests(unittest.TestCase):
    """Examples of every behaviour promised by SPEC v0.1."""

    def assert_runs(self, source: str, expected_output: str) -> None:
        result = run(source)
        self.assertEqual(result["error"], None, result["error"])
        self.assertEqual(result["output"], expected_output)

    def assert_friendly_error(self, source: str, words: str) -> None:
        result = run(source)
        self.assertIsInstance(result["output"], str)
        self.assertIsNotNone(result["error"])
        self.assertRegex(result["error"], r"Line \d+")
        self.assertIn(words, result["error"].lower())

    def test_execution_starts_at_main_not_another_scene(self) -> None:
        self.assert_runs(
            "SCENE prologue\nSAY \"do not print\"\nCUT\n"
            "SCENE main\nSAY \"The movie starts\"\nCUT\n",
            "The movie starts\n",
        )

    def test_scene_ends_at_cut(self) -> None:
        self.assert_runs(program('SAY "That is a wrap"'), "That is a wrap\n")

    def test_indentation_and_comments_are_ignored(self) -> None:
        self.assert_runs(
            program('  -- camera notes\n    SAY "Space does not matter"'),
            "Space does not matter\n",
        )

    def test_set_and_say_support_lowercase_name_with_digits_and_underscore(self) -> None:
        self.assert_runs(
            program('SET take_2 TO "great"\nSAY take_2'), "great\n"
        )

    def test_values_include_integer_decimal_text_and_booleans(self) -> None:
        self.assert_runs(
            program('SAY 10\nSAY 3.5\nSAY "hello"\nSAY YES\nSAY NO'),
            "10\n3.5\nhello\nYES\nNO\n",
        )

    def test_whole_decimal_numbers_print_without_dot_zero(self) -> None:
        self.assert_runs(program("SAY 10.0"), "10\n")

    def test_math_operators_and_order_of_operations(self) -> None:
        self.assert_runs(
            program(
                "SAY 2 PLUS 3 TIMES 4\n"
                "SAY (2 PLUS 3) TIMES 4\n"
                "SAY 9 MINUS 4\n"
                "SAY 8 DIVIDED BY 2"
            ),
            "14\n20\n5\n4\n",
        )

    def test_join_turns_values_into_text(self) -> None:
        self.assert_runs(
            program('SET score TO 7\nSAY "Score: " JOIN score'), "Score: 7\n"
        )

    def test_comparisons_produce_yes_or_no(self) -> None:
        self.assert_runs(
            program("SAY 4 EQUALS 4\nSAY 5 BIGGER THAN 2\nSAY 1 SMALLER THAN 3"),
            "YES\nYES\nYES\n",
        )

    def test_logic_and_parentheses(self) -> None:
        self.assert_runs(
            program("SAY YES AND NOT NO\nSAY NO OR (YES AND YES)"), "YES\nYES\n"
        )

    def test_if_runs_its_true_branch(self) -> None:
        self.assert_runs(
            program('IF 4 BIGGER THAN 2\nSAY "hero wins"\nEND'), "hero wins\n"
        )

    def test_if_otherwise_runs_its_false_branch(self) -> None:
        self.assert_runs(
            program(
                'IF 1 BIGGER THAN 2\nSAY "wrong"\nOTHERWISE\nSAY "right"\nEND'
            ),
            "right\n",
        )

    def test_repeat_runs_exact_number_of_times(self) -> None:
        self.assert_runs(
            program('REPEAT 3 TIMES\nSAY "Action!"\nEND'), "Action!\nAction!\nAction!\n"
        )

    def test_nested_if_and_repeat_blocks_end_with_end(self) -> None:
        self.assert_runs(
            program(
                'REPEAT 2 TIMES\nIF YES\nSAY "beat"\nEND\nEND'
            ),
            "beat\nbeat\n",
        )

    def test_unknown_name_is_a_friendly_line_numbered_error(self) -> None:
        self.assert_friendly_error(program("SAY villain"), "don't know")

    def test_missing_end_is_a_friendly_line_numbered_error(self) -> None:
        self.assert_friendly_error(program('IF YES\nSAY "unfinished"'), "end")

    def test_dividing_by_zero_is_a_friendly_line_numbered_error(self) -> None:
        self.assert_friendly_error(program("SAY 8 DIVIDED BY 0"), "zero")

    def test_missing_main_scene_is_a_friendly_line_numbered_error(self) -> None:
        self.assert_friendly_error(program('SAY "no star"', scene="opening"), "main")


if __name__ == "__main__":
    unittest.main()
