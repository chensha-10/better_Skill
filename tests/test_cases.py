import json
import tempfile
import unittest
from pathlib import Path

from skill_optimizer.cases import create_case_template


class CreateCaseTemplateTests(unittest.TestCase):
    def test_create_case_template_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "test_cases"

            case_dir = create_case_template(root, "case_001", "mixed", 0.85, 120)

            self.assertEqual(case_dir, root / "case_001")
            self.assertTrue((case_dir / "prompt.txt").is_file())
            self.assertTrue((case_dir / "expected.txt").is_file())
            self.assertTrue((case_dir / "expected_files").is_dir())
            metadata = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["name"], "case_001")
            self.assertEqual(metadata["type"], "mixed")
            self.assertEqual(metadata["min_score"], 0.85)
            self.assertEqual(metadata["timeout_seconds"], 120)

    def test_create_case_template_rejects_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "test_cases"
            create_case_template(root, "case_001", "text", 0.8, 30)

            with self.assertRaises(FileExistsError):
                create_case_template(root, "case_001", "text", 0.8, 30)

    def test_create_case_template_rejects_unknown_type(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "test_cases"

            with self.assertRaises(ValueError):
                create_case_template(root, "case_001", "unknown", 0.8, 30)

    def test_load_cases_sorts_directories_by_name(self):
        from skill_optimizer.cases import load_cases

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "test_cases"
            create_case_template(root, "case_002", "text", 0.7, 50)
            create_case_template(root, "case_001", "files", 0.9, 60)
            (root / "case_001" / "prompt.txt").write_text("first", encoding="utf-8")
            (root / "case_002" / "prompt.txt").write_text("second", encoding="utf-8")

            cases = load_cases(root, default_min_score=0.85, default_timeout_seconds=120)

            self.assertEqual([case.name for case in cases], ["case_001", "case_002"])
            self.assertEqual(cases[0].case_type, "files")
            self.assertEqual(cases[0].min_score, 0.9)
            self.assertEqual(cases[0].timeout_seconds, 60)
            self.assertEqual(cases[1].case_type, "text")

    def test_load_cases_requires_prompt_file(self):
        from skill_optimizer.cases import load_cases

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "test_cases"
            case_dir = create_case_template(root, "case_001", "text", 0.7, 50)
            (case_dir / "prompt.txt").unlink()

            with self.assertRaises(FileNotFoundError):
                load_cases(root, default_min_score=0.85, default_timeout_seconds=120)


if __name__ == "__main__":
    unittest.main()
