import tempfile
import unittest
from pathlib import Path

from skill_optimizer.files import backup_file, compare_expected_files, copy_input_files, create_iteration_dir, should_copy_skill_dir, copy_skill_dir


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


    def test_copy_input_files_copies_single_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "input_files"
            target_dir = root / "target"
            input_dir.mkdir()
            (input_dir / "source.py").write_text("print('hello')", encoding="utf-8")

            copy_input_files(input_dir, target_dir)

            copied = target_dir / "source.py"
            self.assertTrue(copied.is_file())
            self.assertEqual(copied.read_text(encoding="utf-8"), "print('hello')")

    def test_copy_input_files_copies_nested_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "input_files"
            target_dir = root / "target"
            (input_dir / "sub" / "nested").mkdir(parents=True)
            (input_dir / "sub" / "nested" / "data.txt").write_text("nested content", encoding="utf-8")
            (input_dir / "root_file.txt").write_text("root content", encoding="utf-8")

            copy_input_files(input_dir, target_dir)

            self.assertTrue((target_dir / "root_file.txt").is_file())
            self.assertTrue((target_dir / "sub" / "nested" / "data.txt").is_file())
            self.assertEqual(
                (target_dir / "sub" / "nested" / "data.txt").read_text(encoding="utf-8"),
                "nested content",
            )

    def test_copy_input_files_handles_empty_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_dir = root / "input_files"
            target_dir = root / "target"
            input_dir.mkdir()

            copy_input_files(input_dir, target_dir)

            self.assertTrue(target_dir.is_dir())

class SkillDirCopyTests(unittest.TestCase):
    def test_should_copy_skill_dir_returns_true_when_references_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "references").mkdir()
            (workspace / "SKILL.md").write_text("# Skill", encoding="utf-8")

            self.assertTrue(should_copy_skill_dir(workspace))

    def test_should_copy_skill_dir_returns_true_when_examples_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "examples").mkdir()

            self.assertTrue(should_copy_skill_dir(workspace))

    def test_should_copy_skill_dir_returns_false_for_skill_md_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "SKILL.md").write_text("# Skill", encoding="utf-8")

            self.assertFalse(should_copy_skill_dir(workspace))

    def test_should_copy_skill_dir_returns_false_for_empty_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            self.assertFalse(should_copy_skill_dir(workspace))

    def test_copy_skill_dir_copies_all_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            target = Path(temp_dir) / "target"
            (workspace / "references").mkdir(parents=True)
            (workspace / "SKILL.md").write_text("# Skill", encoding="utf-8")
            (workspace / "references" / "helper.py").write_text("def help(): pass", encoding="utf-8")
            (workspace / "references" / "sub" / "deep.txt").mkdir(parents=True)
            (workspace / "references" / "sub" / "deep.txt" / "data.txt").write_text("deep", encoding="utf-8")

            copy_skill_dir(workspace, target)

            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "# Skill")
            self.assertEqual((target / "references" / "helper.py").read_text(encoding="utf-8"), "def help(): pass")
            self.assertEqual(
                (target / "references" / "sub" / "deep.txt" / "data.txt").read_text(encoding="utf-8"),
                "deep",
            )

    def test_copy_skill_dir_excludes_hidden_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            target = Path(temp_dir) / "target"
            (workspace / "references").mkdir(parents=True)
            (workspace / ".gitignore").write_text("*.pyc", encoding="utf-8")
            (workspace / "references" / ".hidden").write_text("secret", encoding="utf-8")
            (workspace / "references" / "visible.py").write_text("ok", encoding="utf-8")

            copy_skill_dir(workspace, target)

            self.assertFalse((target / ".gitignore").exists())
            self.assertFalse((target / "references" / ".hidden").exists())
            self.assertTrue((target / "references" / "visible.py").is_file())

    def test_copy_skill_dir_handles_empty_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            target = Path(temp_dir) / "target"
            workspace.mkdir()

            copy_skill_dir(workspace, target)

            self.assertTrue(target.is_dir())


if __name__ == "__main__":
    unittest.main()
