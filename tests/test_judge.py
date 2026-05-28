import unittest

from skill_optimizer.judge import (
    combine_scores,
    judge_text_simple,
    parse_judge_output,
)


class JudgeTests(unittest.TestCase):
    # --- JSON parsing ---

    def test_parse_judge_output_reads_clean_json(self):
        result = parse_judge_output('{"score": 0.75, "reason": "mostly correct"}')

        self.assertEqual(result.score, 0.75)
        self.assertEqual(result.reason, "mostly correct")

    def test_parse_judge_output_extracts_from_markdown_code_fence(self):
        output = 'Here is my assessment:\n\n```json\n{"score": 0.9, "reason": "great"}\n```\n\nDone.'

        result = parse_judge_output(output)

        self.assertEqual(result.score, 0.9)
        self.assertEqual(result.reason, "great")

    def test_parse_judge_output_extracts_bare_json_from_text(self):
        output = 'The answer is correct.\n\n{"score": 0.8, "reason": "mostly there"}'

        result = parse_judge_output(output)

        self.assertEqual(result.score, 0.8)

    def test_parse_judge_output_rejects_invalid_score(self):
        with self.assertRaises(ValueError):
            parse_judge_output('{"score": 2, "reason": "bad"}')

    def test_parse_judge_output_raises_when_no_json_found(self):
        with self.assertRaises(ValueError):
            parse_judge_output("just some text, no json at all")

    # --- difflib shortcut ---

    def test_judge_text_simple_returns_score_for_short_expected(self):
        result = judge_text_simple("hello world", "hello world")

        self.assertIsNotNone(result)
        self.assertGreater(result.score, 0.95)

    def test_judge_text_simple_returns_none_for_long_expected(self):
        long_text = "x" * 150

        result = judge_text_simple("short", long_text)

        self.assertIsNone(result)

    def test_judge_text_simple_detects_difference(self):
        result = judge_text_simple("hello", "completely different")

        self.assertIsNotNone(result)
        self.assertLess(result.score, 0.5)

    # --- combine_scores ---

    def test_combine_scores_text_only_passes(self):
        score, passed = combine_scores(text_score=0.9, file_score=None, min_score=0.85)

        self.assertEqual(score, 0.9)
        self.assertTrue(passed)

    def test_combine_scores_text_only_fails_below_threshold(self):
        score, passed = combine_scores(text_score=0.5, file_score=None, min_score=0.85)

        self.assertEqual(score, 0.5)
        self.assertFalse(passed)

    def test_combine_scores_file_low_score(self):
        score, passed = combine_scores(text_score=0.9, file_score=0.3, min_score=0.85)

        self.assertAlmostEqual(score, 0.6)
        self.assertFalse(passed)

    def test_combine_scores_files_only_success(self):
        score, passed = combine_scores(text_score=None, file_score=1.0, min_score=0.85)

        self.assertEqual(score, 1.0)
        self.assertTrue(passed)

    def test_combine_scores_mixed_both_pass(self):
        score, passed = combine_scores(text_score=0.9, file_score=0.9, min_score=0.85)

        self.assertEqual(score, 0.9)
        self.assertTrue(passed)

    def test_combine_scores_mixed_text_fails(self):
        score, passed = combine_scores(text_score=0.5, file_score=0.9, min_score=0.85)

        self.assertAlmostEqual(score, 0.7)
        self.assertFalse(passed)


if __name__ == "__main__":
    unittest.main()
