import json
from dataclasses import dataclass
from pathlib import Path

VALID_CASE_TYPES = {"text", "files", "mixed"}


@dataclass(frozen=True)
class TestCase:
    name: str
    case_dir: Path
    prompt_path: Path
    expected_text_path: Path | None
    expected_files_dir: Path | None
    input_files_dir: Path | None
    case_type: str
    min_score: float
    timeout_seconds: int


def create_case_template(
    test_cases_dir: Path,
    case_name: str,
    case_type: str,
    min_score: float,
    timeout_seconds: int,
    with_input_files: bool = False,
) -> Path:
    if case_type not in VALID_CASE_TYPES:
        raise ValueError(f"Unsupported case type: {case_type}")

    case_dir = test_cases_dir / case_name
    if case_dir.exists():
        raise FileExistsError(f"Case directory already exists: {case_dir}")

    case_dir.mkdir(parents=True)
    (case_dir / "prompt.txt").write_text("", encoding="utf-8")
    if case_type in {"text", "mixed"}:
        (case_dir / "expected.txt").write_text("", encoding="utf-8")
    if case_type in {"files", "mixed"}:
        (case_dir / "expected_files").mkdir()
    if with_input_files:
        (case_dir / "input_files").mkdir()
    metadata = {
        "name": case_name,
        "type": case_type,
        "min_score": min_score,
        "timeout_seconds": timeout_seconds,
    }
    (case_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return case_dir


def load_cases(
    test_cases_dir: Path,
    default_min_score: float,
    default_timeout_seconds: int,
) -> list[TestCase]:
    if not test_cases_dir.exists():
        return []

    cases: list[TestCase] = []
    for case_dir in sorted(path for path in test_cases_dir.iterdir() if path.is_dir()):
        metadata = _read_metadata(case_dir)
        case_name = str(metadata.get("name", case_dir.name))
        case_type = str(metadata.get("type", "mixed"))
        if case_type not in VALID_CASE_TYPES:
            raise ValueError(f"Unsupported case type in {case_dir}: {case_type}")

        prompt_path = case_dir / "prompt.txt"
        if not prompt_path.is_file():
            raise FileNotFoundError(f"Missing prompt.txt: {prompt_path}")

        expected_text_path = case_dir / "expected.txt"
        expected_files_dir = case_dir / "expected_files"
        input_files_dir = case_dir / "input_files"
        has_text = case_type in {"text", "mixed"} and expected_text_path.is_file()
        has_files = case_type in {"files", "mixed"} and expected_files_dir.is_dir()
        cases.append(
            TestCase(
                name=case_name,
                case_dir=case_dir,
                prompt_path=prompt_path,
                expected_text_path=expected_text_path if has_text else None,
                expected_files_dir=expected_files_dir if has_files else None,
                input_files_dir=input_files_dir if input_files_dir.is_dir() else None,
                case_type=case_type,
                min_score=float(metadata.get("min_score", default_min_score)),
                timeout_seconds=int(metadata.get("timeout_seconds", default_timeout_seconds)),
            )
        )
    return cases


def _read_metadata(case_dir: Path) -> dict:
    metadata_path = case_dir / "metadata.json"
    if not metadata_path.is_file():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))
