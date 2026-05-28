import difflib
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileCheckResult:
    passed: bool
    failures: list[str]
    score: float


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
    scores: list[float] = []
    if not expected_dir.exists():
        return FileCheckResult(passed=True, failures=[], score=1.0)

    for expected_path in sorted(path for path in expected_dir.rglob("*") if path.is_file()):
        relative_path = expected_path.relative_to(expected_dir)
        actual_path = actual_dir / relative_path
        relative_text = relative_path.as_posix()
        if not actual_path.is_file():
            failures.append(f"{relative_text} is missing")
            scores.append(0.0)
            continue
        expected_text = expected_path.read_text(encoding="utf-8", errors="replace")
        actual_text = actual_path.read_text(encoding="utf-8", errors="replace")
        ratio = difflib.SequenceMatcher(None, expected_text, actual_text).ratio()
        scores.append(ratio)
        if ratio < 0.8:
            failures.append(f"{relative_text} similarity {ratio:.2f}")

    avg = sum(scores) / len(scores) if scores else 1.0
    return FileCheckResult(passed=not failures, failures=failures, score=avg)


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


SKILL_RESOURCE_DIRS = {"references", "examples", "scripts", "assets"}


def should_copy_skill_dir(workspace_dir: Path) -> bool:
    """workspace 中是否有除 SKILL.md 之外的 skill 资源目录。"""
    return any((workspace_dir / d).is_dir() for d in SKILL_RESOURCE_DIRS)


def copy_skill_dir(workspace_dir: Path, target_dir: Path) -> None:
    """将 workspace 中的 skill 资源复制到 target_dir，排除隐藏文件。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    for src in workspace_dir.rglob("*"):
        if src.is_file():
            parts = src.relative_to(workspace_dir).parts
            if any(p.startswith(".") for p in parts):
                continue
            rel = src.relative_to(workspace_dir)
            dst = target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
