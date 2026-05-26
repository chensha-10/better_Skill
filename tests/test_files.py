import tempfile
import unittest
from pathlib import Path

from skill_optimizer.files import backup_file, compare_expected_files, create_iteration_dir


class FileUtilityTests(unittest.TestCase):
    def test_backup_file_copies_content_to_backup_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "SKILL.md"
            backups = root / "backups"
            source.write_text("skill content", encoding="utf-8")

            backup_path = backup_file(source, backups)

            self.assertTrue(backup_path.is_file())
            self.assertEqual(backup_path.read_text(encoding="utf-8"), "skill content")
            self.assertTrue(backup_path.name.startswith("SKILL_"))
            self.assertEqual(backup_path.suffix, ".md")

    def test_create_iteration_dir_uses_three_digit_number(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runs_dir = Path(temp_dir) / "runs"

            iter_dir = create_iteration_dir(runs_dir, 2)

            self.assertEqual(iter_dir, runs_dir / "iter_002")
            self.assertTrue(iter_dir.is_dir())

    def test_compare_expected_files_passes_and_ignores_extra_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = root / "expected"
            actual = root / "actual"
            (expected / "nested").mkdir(parents=True)
            (actual / "nested").mkdir(parents=True)
            (expected / "nested" / "result.txt").write_text("ok", encoding="utf-8")
            (actual / "nested" / "result.txt").write_text("ok", encoding="utf-8")
            (actual / "extra.txt").write_text("ignored", encoding="utf-8")

            result = compare_expected_files(expected, actual)

            self.assertTrue(result.passed)
            self.assertEqual(result.failures, [])

    def test_compare_expected_files_reports_missing_and_different_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = root / "expected"
            actual = root / "actual"
            expected.mkdir()
            actual.mkdir()
            (expected / "missing.txt").write_text("missing", encoding="utf-8")
            (expected / "different.txt").write_text("expected", encoding="utf-8")
            (actual / "different.txt").write_text("actual", encoding="utf-8")

            result = compare_expected_files(expected, actual)

            self.assertFalse(result.passed)
            self.assertIn("missing.txt is missing", result.failures)
            self.assertIn("different.txt content differs", result.failures)

    def test_compare_expected_files_returns_pass_when_expected_dir_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = root / "nonexistent"
            actual = root / "actual"
            actual.mkdir()

            result = compare_expected_files(expected, actual)

            self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
