import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileCheckResult:
    passed: bool
    failures: list[str]


def backup_file(source: Path, backups_dir: Path) -> Path:
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = backups_dir / f"SKILL_{timestamp}.md"
    shutil.copy2(source, backup_path)
    return backup_path


def create_iteration_dir(runs_dir: Path, iteration: int) -> Path:
    iteration_dir = runs_dir / f"iter_{iteration:03d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    return iteration_dir


def compare_expected_files(expected_dir: Path, actual_dir: Path) -> FileCheckResult:
    failures: list[str] = []
    if not expected_dir.exists():
        return FileCheckResult(passed=True, failures=[])

    for expected_path in sorted(path for path in expected_dir.rglob("*") if path.is_file()):
        relative_path = expected_path.relative_to(expected_dir)
        actual_path = actual_dir / relative_path
        relative_text = relative_path.as_posix()
        if not actual_path.is_file():
            failures.append(f"{relative_text} is missing")
            continue
        if expected_path.read_bytes() != actual_path.read_bytes():
            failures.append(f"{relative_text} content differs")
    return FileCheckResult(passed=not failures, failures=failures)


def write_text_artifact(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_input_files(input_dir: Path, target_dir: Path) -> None:
    """将 input_dir 下所有文件递归复制到 target_dir。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    for src in input_dir.rglob("*"):
        if src.is_file():
            rel = src.relative_to(input_dir)
            dst = target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
