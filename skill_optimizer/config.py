import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a single Claude CLI invocation target."""
    command: str
    model: str


@dataclass(frozen=True)
class Config:
    project_root: Path
    workspace_dir: Path
    skill_path: Path
    test_cases_dir: Path
    runs_dir: Path
    backups_dir: Path
    score_threshold: float
    max_iterations: int
    default_case_timeout_seconds: int
    executor: ModelConfig
    judge: ModelConfig
    reviser: ModelConfig


def default_config(project_root: Path, overrides: dict[str, Any] | None = None) -> Config:
    """Build a Config from project_root with optional overrides.

    Priority: overrides dict > default derivations from project_root.
    Relative paths in overrides are resolved against project_root.
    """
    overrides = overrides or {}
    workspace_dir = project_root / "workspace"

    def _path(key: str, default: Path) -> Path:
        value = overrides.get(key)
        if value is None:
            return default
        p = Path(value)
        return p if p.is_absolute() else project_root / p

    def _model(key: str, default: ModelConfig) -> ModelConfig:
        value = overrides.get(key)
        if value is None:
            return default
        if isinstance(value, dict):
            return ModelConfig(
                command=value.get("command", default.command),
                model=value.get("model", default.model),
            )
        return default

    return Config(
        project_root=project_root,
        workspace_dir=_path("workspace_dir", workspace_dir),
        skill_path=_path("skill_path", workspace_dir / "SKILL.md"),
        test_cases_dir=_path("test_cases_dir", project_root / "test_cases"),
        runs_dir=_path("runs_dir", workspace_dir / "runs"),
        backups_dir=_path("backups_dir", workspace_dir / "backups"),
        score_threshold=float(overrides.get("score_threshold", 0.85)),
        max_iterations=int(overrides.get("max_iterations", 5)),
        default_case_timeout_seconds=int(overrides.get("default_case_timeout_seconds", 300)),
        executor=_model("executor", ModelConfig(command="claude", model="sonnet")),
        judge=_model("judge", ModelConfig(command="claude", model="sonnet")),
        reviser=_model("reviser", ModelConfig(command="claude", model="sonnet")),
    )


def load_config_file(path: Path) -> dict[str, Any]:
    """Load configuration from a JSON file. Returns empty dict if file not found."""
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_config(
    project_root: Path,
    config_file_path: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> Config:
    """Build Config with layered priority: CLI overrides > config file > defaults.

    If config_file_path is not given, looks for skill_optimizer.json in project_root.
    """
    if config_file_path is None:
        config_file_path = project_root / "skill_optimizer.json"

    file_overrides = load_config_file(config_file_path)
    merged = {**file_overrides, **(cli_overrides or {})}
    return default_config(project_root, overrides=merged)
