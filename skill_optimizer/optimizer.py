from pathlib import Path

from skill_optimizer.files import backup_file


def validate_skill_revision(new_content: str, previous_content: str) -> None:
    stripped = new_content.strip()
    if not stripped:
        raise ValueError("New SKILL.md content is empty")
    if stripped == previous_content.strip():
        raise ValueError("New SKILL.md content is unchanged")
    if len(stripped) < 80:
        raise ValueError("New SKILL.md content is too short")
    if "name:" not in stripped or "description:" not in stripped:
        raise ValueError("New SKILL.md must contain name and description")


def apply_revision_with_backup(skill_path: Path, backups_dir: Path, new_content: str) -> Path:
    previous_content = skill_path.read_text(encoding="utf-8")
    validate_skill_revision(new_content, previous_content)
    backup_path = backup_file(skill_path, backups_dir)
    skill_path.write_text(new_content, encoding="utf-8")
    return backup_path


def build_revision_prompt(skill_content: str, failure_summary: str, skill_path: str = "workspace/SKILL.md") -> str:
    return (
        "You are a prompt engineer improving a Claude SKILL.md file. You are NOT "
        "executing the skill — your job is to revise the SKILL.md so that a future "
        "executor will produce correct outputs. The current SKILL content is shown "
        "below in <current_skill>. The test failures in <failures> indicate what the "
        "SKILL doesn't handle well.\n\n"
        "Analyze the failures, then revise the SKILL to address every issue.\n\n"
        "IMPORTANT: You must output the COMPLETE revised SKILL.md content as your "
        "entire response. Start your response with `---` (the YAML frontmatter delimiter) "
        "and end with the last line of the SKILL content. Do NOT use any tools. "
        "Do NOT write to any files. Do NOT include any explanation, summary, or commentary "
        "before or after the SKILL content. Your entire response must be the raw SKILL.md file content.\n\n"
        "<current_skill>\n"
        f"{skill_content}\n"
        "</current_skill>\n\n"
        "<failures>\n"
        f"{failure_summary}\n"
        "</failures>\n"
    )
