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


def build_revision_prompt(skill_content: str, failure_summary: str) -> str:
    return (
        "You are an expert prompt engineer reviewing a Claude SKILL.md file. "
        "You are NOT executing the skill below — you are analyzing and improving it "
        "as an independent reviewer. Your task is to revise the skill definition "
        "so it passes all test cases.\n\n"
        "Improve this Claude SKILL.md so it passes the failed test cases. "
        "Return only the complete revised SKILL.md content.\n\n"
        "<current_skill>\n"
        f"{skill_content}\n"
        "</current_skill>\n\n"
        "<failures>\n"
        f"{failure_summary}\n"
        "</failures>\n"
    )
