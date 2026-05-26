import tempfile
import unittest
from pathlib import Path

from skill_optimizer.optimizer import apply_revision_with_backup, build_revision_prompt, validate_skill_revision


VALID_SKILL = """---
name: example-skill
description: Example skill for tests
---

# Example Skill

Use this skill to answer test prompts carefully.
"""


class OptimizerTests(unittest.TestCase):
    def test_validate_skill_revision_accepts_skill_with_name_and_description(self):
        validate_skill_revision(VALID_SKILL, previous_content="old content")

    def test_validate_skill_revision_rejects_empty_or_same_content(self):
        with self.assertRaises(ValueError):
            validate_skill_revision("", previous_content="old")
        with self.assertRaises(ValueError):
            validate_skill_revision("old", previous_content="old")

    def test_validate_skill_revision_requires_name_and_description(self):
        with self.assertRaises(ValueError):
            validate_skill_revision("# Missing frontmatter", previous_content="old")

    def test_apply_revision_with_backup_overwrites_skill_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_path = root / "SKILL.md"
            backups_dir = root / "backups"
            skill_path.write_text("old skill content", encoding="utf-8")

            backup_path = apply_revision_with_backup(skill_path, backups_dir, VALID_SKILL)

            self.assertTrue(backup_path.is_file())
            self.assertEqual(backup_path.read_text(encoding="utf-8"), "old skill content")
            self.assertEqual(skill_path.read_text(encoding="utf-8"), VALID_SKILL)

    def test_build_revision_prompt_includes_role_separation(self):
        prompt = build_revision_prompt(
            skill_content="old skill",
            failure_summary="case_001 failed with score 0.3",
        )

        self.assertIn("prompt engineer", prompt.lower())
        self.assertIn("NOT executing the skill", prompt)
        self.assertIn("old skill", prompt)
        self.assertIn("case_001 failed", prompt)


if __name__ == "__main__":
    unittest.main()
