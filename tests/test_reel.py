"""Contract tests for Reel v0.1 and v0.2.

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


class ReelV02SpecTests(unittest.TestCase):
    """Contract tests for every feature added by SPEC v0.2."""

    def assert_runs(self, source: str, expected_output: str) -> None:
        result = run(source)
        self.assertEqual(result["error"], None, result["error"])
        self.assertEqual(result["output"], expected_output)

    def assert_friendly_error(self, source: str, words: str | None = None) -> None:
        result = run(source)
        self.assertIsInstance(result["output"], str)
        self.assertIsNotNone(result["error"])
        self.assertRegex(result["error"], r"Line \d+")
        self.assertNotRegex(
            result["error"].lower(),
            r"do not understand|expected the line|character",
        )
        if words is not None:
            self.assertIn(words, result["error"].lower())

    def test_scenes_accept_one_or_more_inputs_in_any_file_order(self) -> None:
        self.assert_runs(
            "SCENE add WITH a, b\n"
            "GIVE BACK a PLUS b\n"
            "CUT\n"
            "SCENE main\n"
            "SAY CALL add WITH 2, 3\n"
            "CUT\n",
            "5\n",
        )

    def test_call_statement_runs_a_scene_and_ignores_its_return_value(self) -> None:
        self.assert_runs(
            "SCENE cheer WITH name\n"
            "SAY \"Go, \" JOIN name\n"
            "GIVE BACK 99\n"
            "CUT\n"
            "SCENE main\n"
            "CALL cheer WITH \"Mia\"\n"
            "SAY \"Finished\"\n"
            "CUT\n",
            "Go, Mia\nFinished\n",
        )

    def test_call_value_can_be_used_inside_a_larger_expression(self) -> None:
        self.assert_runs(
            "SCENE double WITH n\n"
            "GIVE BACK n TIMES 2\n"
            "CUT\n"
            "SCENE main\n"
            "SET answer TO 1 PLUS (CALL double WITH 4)\n"
            "SAY answer\n"
            "CUT\n",
            "9\n",
        )

    def test_give_back_ends_the_scene_immediately(self) -> None:
        self.assert_runs(
            "SCENE surprise\n"
            "GIVE BACK \"ta-da\"\n"
            "SAY \"too late\"\n"
            "CUT\n"
            "SCENE main\n"
            "SAY CALL surprise\n"
            "CUT\n",
            "ta-da\n",
        )

    def test_scene_without_give_back_returns_nothing(self) -> None:
        self.assert_runs(
            "SCENE wave\n"
            "SAY \"wave\"\n"
            "CUT\n"
            "SCENE main\n"
            "SAY CALL wave\n"
            "CUT\n",
            "wave\nNOTHING\n",
        )

    def test_scene_variables_do_not_escape_their_scene(self) -> None:
        self.assert_friendly_error(
            "SCENE make_secret\n"
            "SET secret TO \"shh\"\n"
            "CUT\n"
            "SCENE main\n"
            "CALL make_secret\n"
            "SAY secret\n"
            "CUT\n",
            "don't know",
        )

    def test_recursive_calls_stop_after_the_recursion_limit(self) -> None:
        self.assert_friendly_error(
            "SCENE forever WITH n\n"
            "GIVE BACK CALL forever WITH n\n"
            "CUT\n"
            "SCENE main\n"
            "SAY CALL forever WITH 1\n"
            "CUT\n",
        )

    def test_unknown_scene_is_a_friendly_line_numbered_error(self) -> None:
        self.assert_friendly_error(program("CALL missing_scene"))

    def test_wrong_number_of_scene_inputs_is_a_friendly_error(self) -> None:
        self.assert_friendly_error(
            "SCENE pair WITH left, right\n"
            "GIVE BACK left JOIN right\n"
            "CUT\n"
            "SCENE main\n"
            "SAY CALL pair WITH \"one\"\n"
            "CUT\n",
        )

    def test_lists_can_be_created_empty_extended_and_printed(self) -> None:
        self.assert_runs(
            program(
                'SET cast TO LIST "Ann", "Bob"\n'
                'SET empty TO LIST\n'
                'ADD "Cy" TO cast\n'
                "SAY cast\n"
                "SAY empty"
            ),
            "[Ann, Bob, Cy]\n[]\n",
        )

    def test_at_uses_one_based_counting_and_length_handles_lists_and_text(self) -> None:
        self.assert_runs(
            program(
                'SET cast TO LIST "Ann", "Bob"\n'
                "SAY cast AT 1\n"
                "SAY LENGTH OF cast\n"
                'SAY LENGTH OF "moons" PLUS 1'
            ),
            "Ann\n2\n6\n",
        )

    def test_list_at_out_of_range_is_a_friendly_error(self) -> None:
        self.assert_friendly_error(
            program('SET cast TO LIST "Ann"\nSAY cast AT 2')
        )

    def test_list_in_call_inputs_is_wrapped_in_parentheses(self) -> None:
        self.assert_runs(
            "SCENE count WITH items\n"
            "GIVE BACK LENGTH OF items\n"
            "CUT\n"
            "SCENE main\n"
            "SET cast TO LIST \"Ann\", \"Bob\"\n"
            "SAY CALL count WITH (cast)\n"
            "CUT\n",
            "2\n",
        )

    def test_for_each_runs_once_per_list_item(self) -> None:
        self.assert_runs(
            program(
                'SET cast TO LIST "Ann", "Bob", "Cy"\n'
                "FOR EACH actor IN cast\n"
                'SAY "Hello " JOIN actor\n'
                "END"
            ),
            "Hello Ann\nHello Bob\nHello Cy\n",
        )

    def test_while_repeats_until_its_condition_is_false(self) -> None:
        self.assert_runs(
            program(
                "SET i TO 1\n"
                "WHILE NOT (i BIGGER THAN 3)\n"
                "SAY i\n"
                "SET i TO i PLUS 1\n"
                "END"
            ),
            "1\n2\n3\n",
        )

    def test_non_ending_while_loop_is_a_friendly_error(self) -> None:
        self.assert_friendly_error(
            program("WHILE YES\nEND"), "this loop never ends"
        )


if __name__ == "__main__":
    unittest.main()
