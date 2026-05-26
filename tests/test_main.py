import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from main import build_parser, handle_init_case, run_optimization
from skill_optimizer.cases import create_case_template
from skill_optimizer.config import ModelConfig, build_config


class MainCommandTests(unittest.TestCase):
    def test_parser_accepts_init_case_with_type(self):
        parser = build_parser()

        args = parser.parse_args(["init-case", "case_001", "--type", "files"])

        self.assertEqual(args.command, "init-case")
        self.assertEqual(args.case_name, "case_001")
        self.assertEqual(args.case_type, "files")

    def test_parser_accepts_global_path_overrides(self):
        parser = build_parser()

        args = parser.parse_args([
            "--project-root", "/tmp/proj",
            "--skill-path", "/tmp/skill.md",
            "--test-cases-dir", "/tmp/cases",
            "init-case", "case_001",
        ])

        self.assertEqual(args.project_root, "/tmp/proj")
        self.assertEqual(args.skill_path, "/tmp/skill.md")
        self.assertEqual(args.test_cases_dir, "/tmp/cases")

    def test_handle_init_case_creates_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            parser = build_parser()
            args = parser.parse_args(["init-case", "case_001", "--type", "mixed"])

            exit_code = handle_init_case(args, config)

            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(temp_dir) / "test_cases" / "case_001" / "metadata.json").is_file())

    def test_handle_init_case_returns_error_for_existing_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            parser = build_parser()
            args = parser.parse_args(["init-case", "case_001"])
            handle_init_case(args, config)

            exit_code = handle_init_case(args, config)

            self.assertEqual(exit_code, 1)

    # --- Task 9: Preflight checks ---

    def test_run_optimization_requires_skill_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))

            exit_code = run_optimization(config)

            self.assertEqual(exit_code, 1)

    def test_run_optimization_reports_no_cases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: test\ndescription: test skill\n---\n\nBody text",
                encoding="utf-8",
            )

            exit_code = run_optimization(config)

            self.assertEqual(exit_code, 1)

    # --- Task 10: Single-iteration evaluation ---

    def test_run_one_iteration_evaluates_text_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: test-skill\ndescription: test skill\n---\n\nReturn the expected answer.",
                encoding="utf-8",
            )
            case_dir = create_case_template(config.test_cases_dir, "case_001", "text", 0.1, 30)
            (case_dir / "prompt.txt").write_text("say hello", encoding="utf-8")
            (case_dir / "expected.txt").write_text("hello", encoding="utf-8")

            # Executor outputs "hello" which difflib shortcut will match against expected "hello"
            fake_executor = ModelConfig(command=sys.executable, model="")
            # Judge not needed — difflib shortcut handles short expected text (< 100 chars)
            fake_config = replace(config, executor=fake_executor)

            exit_code = run_optimization(
                fake_config,
                extra_executor_args=["-c", "print('hello')"],
                max_iterations_override=1,
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((config.runs_dir / "iter_001" / "case_001" / "stdout.txt").is_file())

    # --- Task 11: File output verification via cwd isolation ---

    def test_run_one_iteration_checks_expected_files_via_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: test-skill\ndescription: test skill\n---\n\nCreate files on request.",
                encoding="utf-8",
            )
            case_dir = create_case_template(config.test_cases_dir, "case_001", "files", 0.85, 30)
            (case_dir / "prompt.txt").write_text("create result.txt", encoding="utf-8")
            (case_dir / "expected_files" / "result.txt").write_text("expected content", encoding="utf-8")
            (case_dir / "expected.txt").unlink()

            fake_script = (
                "import os; "
                "os.makedirs(os.getcwd(), exist_ok=True); "
                "open(os.path.join(os.getcwd(), 'result.txt'), 'w').write('expected content'); "
                "print('done')"
            )
            fake_executor = ModelConfig(command=sys.executable, model="")
            fake_config = replace(config, executor=fake_executor)

            exit_code = run_optimization(
                fake_config,
                extra_executor_args=["-c", fake_script],
                max_iterations_override=1,
            )

            self.assertEqual(exit_code, 0)

    # --- Task 12: Iteration loop with revision ---

    def test_iteration_loop_applies_revision_after_failure(self):
        import json as _json

        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: weak-skill\ndescription: weak\n---\n\nBe unhelpful.",
                encoding="utf-8",
            )
            case_dir = create_case_template(config.test_cases_dir, "case_001", "text", 0.85, 30)
            (case_dir / "prompt.txt").write_text("say hello", encoding="utf-8")
            (case_dir / "expected.txt").write_text("hello", encoding="utf-8")

            fake_model = ModelConfig(command=sys.executable, model="")
            revised_skill = (
                "---\nname: better-skill\ndescription: better\n---\n\n"
                "Always respond with exactly what the user asks for."
            )
            reviser_script = f"import sys; sys.stdout.write({_json.dumps(revised_skill)})"

            fake_config = replace(
                config,
                executor=fake_model,
                reviser=fake_model,
                max_iterations=3,
                score_threshold=0.85,
            )

            exit_code = run_optimization(
                fake_config,
                extra_executor_args=["-c", "print('wrong answer')"],
                extra_reviser_args=["-c", reviser_script],
                max_iterations_override=3,
            )

            final_skill = config.skill_path.read_text(encoding="utf-8")
            self.assertIn("better-skill", final_skill)
            self.assertTrue(any(config.backups_dir.iterdir()))


if __name__ == "__main__":
    unittest.main()
