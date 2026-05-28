import json
import tempfile
import unittest
from pathlib import Path

from skill_optimizer.config import (
    Config,
    ModelConfig,
    build_config,
    default_config,
    load_config_file,
)


class ModelConfigTests(unittest.TestCase):
    def test_model_config_holds_command_and_model(self):
        mc = ModelConfig(command="claude", model="claude-sonnet-4-6")
        self.assertEqual(mc.command, "claude")
        self.assertEqual(mc.model, "claude-sonnet-4-6")

    def test_model_config_repr_is_readable(self):
        mc = ModelConfig(command="claude", model="claude-haiku-4-5")
        self.assertIn("claude-haiku-4-5", repr(mc))


class ConfigTests(unittest.TestCase):
    def test_default_config_uses_project_root_paths(self):
        config = default_config(Path("F:/testprogram/better_Skill"))

        self.assertEqual(config.project_root, Path("F:/testprogram/better_Skill"))
        self.assertEqual(config.workspace_dir, Path("F:/testprogram/better_Skill/workspace"))
        self.assertEqual(config.skill_path, Path("F:/testprogram/better_Skill/workspace/SKILL.md"))
        self.assertEqual(config.test_cases_dir, Path("F:/testprogram/better_Skill/test_cases"))
        self.assertEqual(config.output_dir, Path("F:/testprogram/better_Skill/output"))
        self.assertEqual(config.runs_dir, Path("F:/testprogram/better_Skill/output/runs"))
        self.assertEqual(config.backups_dir, Path("F:/testprogram/better_Skill/output/backups"))
        self.assertEqual(config.score_threshold, 0.85)
        self.assertEqual(config.max_iterations, 5)
        self.assertEqual(config.default_case_timeout_seconds, 300)

    def test_default_config_accepts_path_overrides(self):
        config = default_config(
            Path("F:/testprogram/better_Skill"),
            overrides={
                "skill_path": "F:/custom/skill.md",
                "test_cases_dir": "F:/custom/cases",
            },
        )

        self.assertEqual(config.skill_path, Path("F:/custom/skill.md"))
        self.assertEqual(config.test_cases_dir, Path("F:/custom/cases"))
        # Non-overridden paths stay default
        self.assertEqual(config.workspace_dir, Path("F:/testprogram/better_Skill/workspace"))

    def test_default_config_accepts_model_overrides(self):
        config = default_config(
            Path("F:/testprogram/better_Skill"),
            overrides={
                "executor": {"command": "claude", "model": "claude-haiku-4-5"},
            },
        )

        self.assertEqual(config.executor.model, "claude-haiku-4-5")
        # Non-overridden models stay default
        self.assertEqual(config.judge.model, "sonnet")

    def test_default_config_creates_three_model_configs(self):
        config = default_config(Path("F:/testprogram/better_Skill"))

        self.assertIsInstance(config.executor, ModelConfig)
        self.assertIsInstance(config.judge, ModelConfig)
        self.assertIsInstance(config.reviser, ModelConfig)
        self.assertEqual(config.executor.command, "claude")
        self.assertEqual(config.judge.command, "claude")
        self.assertEqual(config.reviser.command, "claude")

    def test_config_is_constructible_for_tests(self):
        config = Config(
            project_root=Path("C:/tmp/project"),
            workspace_dir=Path("C:/tmp/project/workspace"),
            skill_path=Path("C:/tmp/project/workspace/SKILL.md"),
            test_cases_dir=Path("C:/tmp/project/test_cases"),
            output_dir=Path("C:/tmp/project/output"),
            runs_dir=Path("C:/tmp/project/output/runs"),
            backups_dir=Path("C:/tmp/project/output/backups"),
            score_threshold=0.9,
            max_iterations=3,
            default_case_timeout_seconds=60,
            executor=ModelConfig(command="claude", model="claude-sonnet-4-6"),
            judge=ModelConfig(command="claude", model="claude-opus-4-7"),
            reviser=ModelConfig(command="claude", model="claude-opus-4-7"),
            skill_creator_path=None,
        )

        self.assertEqual(config.score_threshold, 0.9)
        self.assertEqual(config.max_iterations, 3)
        self.assertEqual(config.executor.model, "claude-sonnet-4-6")
        self.assertEqual(config.judge.model, "claude-opus-4-7")

    def test_default_config_uses_output_dir_for_runs_and_backups(self):
        config = default_config(Path("F:/testprogram/better_Skill"))

        self.assertEqual(config.output_dir, Path("F:/testprogram/better_Skill/output"))
        self.assertEqual(config.runs_dir, Path("F:/testprogram/better_Skill/output/runs"))
        self.assertEqual(config.backups_dir, Path("F:/testprogram/better_Skill/output/backups"))

    def test_default_config_accepts_output_dir_override(self):
        config = default_config(
            Path("F:/testprogram/better_Skill"),
            overrides={"output_dir": "F:/custom/output"},
        )

        self.assertEqual(config.output_dir, Path("F:/custom/output"))
        self.assertEqual(config.runs_dir, Path("F:/custom/output/runs"))
        self.assertEqual(config.backups_dir, Path("F:/custom/output/backups"))

    def test_default_config_skill_creator_path_is_none(self):
        config = default_config(Path("F:/testprogram/better_Skill"))

        self.assertIsNone(config.skill_creator_path)

    def test_default_config_accepts_skill_creator_path_override(self):
        config = default_config(
            Path("F:/testprogram/better_Skill"),
            overrides={"skill_creator_path": "F:/plugins/skill-creator/SKILL.md"},
        )

        self.assertEqual(config.skill_creator_path, Path("F:/plugins/skill-creator/SKILL.md"))

    def test_default_config_runs_dir_override_takes_precedence_over_output_dir(self):
        config = default_config(
            Path("F:/testprogram/better_Skill"),
            overrides={
                "output_dir": "F:/custom/output",
                "runs_dir": "F:/special/runs",
            },
        )

        self.assertEqual(config.runs_dir, Path("F:/special/runs"))
        self.assertEqual(config.backups_dir, Path("F:/custom/output/backups"))


class ConfigFileTests(unittest.TestCase):
    def test_load_config_file_returns_dict_for_valid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "skill_optimizer.json"
            config_path.write_text(json.dumps({
                "skill_path": "./my_skill/SKILL.md",
                "test_cases_dir": "./my_cases",
            }), encoding="utf-8")

            result = load_config_file(config_path)

            self.assertEqual(result["skill_path"], "./my_skill/SKILL.md")
            self.assertEqual(result["test_cases_dir"], "./my_cases")

    def test_load_config_file_returns_empty_dict_when_file_missing(self):
        result = load_config_file(Path("/nonexistent/config.json"))

        self.assertEqual(result, {})


class BuildConfigTests(unittest.TestCase):
    def test_build_config_merges_defaults_file_and_cli_overrides(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_file = root / "skill_optimizer.json"
            config_file.write_text(json.dumps({
                "skill_path": "./custom/SKILL.md",
            }), encoding="utf-8")

            config = build_config(
                project_root=root,
                config_file_path=config_file,
                cli_overrides={"test_cases_dir": str(root / "cli_cases")},
            )

            self.assertEqual(config.project_root, root)
            self.assertEqual(config.skill_path, root / "custom" / "SKILL.md")
            self.assertEqual(config.test_cases_dir, root / "cli_cases")
            # Not overridden: stays default
            self.assertEqual(config.workspace_dir, root / "workspace")

    def test_build_config_cli_wins_over_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_file = root / "skill_optimizer.json"
            config_file.write_text(json.dumps({
                "skill_path": "./from_file/SKILL.md",
            }), encoding="utf-8")

            config = build_config(
                project_root=root,
                config_file_path=config_file,
                cli_overrides={"skill_path": str(root / "from_cli" / "SKILL.md")},
            )

            self.assertEqual(config.skill_path, root / "from_cli" / "SKILL.md")

    def test_build_config_works_without_config_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            config = build_config(project_root=root)

            self.assertEqual(config.project_root, root)
            self.assertEqual(config.skill_path, root / "workspace" / "SKILL.md")


if __name__ == "__main__":
    unittest.main()
