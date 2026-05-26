# Python SKILL 优化器实施计划

> **给执行代理的提示：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步实施。本计划使用复选框（`- [ ]`）跟踪进度。

**目标：** 构建一个可直接修改的 Python 脚本化框架，用多个测试用例目录测试 Claude `SKILL.md`，对结果评分，并在未达阈值时迭代优化 SKILL。

**架构：** `main.py` 保持为脚本入口。`skill_optimizer/` 下的专注模块分别负责配置、用例加载/创建、文件工具、Claude CLI 执行、评分裁判和 SKILL 修订。MVP 只使用标准库 `unittest`、`argparse`、`json`、`subprocess`、`pathlib` 和 `difflib`，方便检查和修改。

**技术栈：** Python 3 标准库、本地 Claude CLI、`unittest` 测试运行器。MVP 不引入第三方依赖。

---

## 范围和约束

- 当前项目 `F:\testprogram\better_Skill` 不是 git 仓库，并且只有一个 PyCharm 模板 `main.py`。
- 实施时编辑文件必须使用绝对 Windows 路径。
- 不引入包发布、Web UI、插件注册表、数据库或 YAML 依赖。
- 测试用例是多个编号目录：`case_001`、`case_002`，按目录名排序执行。
- 文件期望只对 `expected_files/` 中列出的文件做精确内容检查；实际输出中的额外文件默认忽略。
- `init-case` 通过命令行参数创建测试用例模板，并拒绝覆盖已有用例目录。

## 文件结构

创建或修改这些文件：

```text
F:\testprogram\better_Skill\main.py
F:\testprogram\better_Skill\skill_optimizer\__init__.py
F:\testprogram\better_Skill\skill_optimizer\config.py
F:\testprogram\better_Skill\skill_optimizer\cases.py
F:\testprogram\better_Skill\skill_optimizer\files.py
F:\testprogram\better_Skill\skill_optimizer\runner.py
F:\testprogram\better_Skill\skill_optimizer\judge.py
F:\testprogram\better_Skill\skill_optimizer\optimizer.py
F:\testprogram\better_Skill\tests\test_cases.py
F:\testprogram\better_Skill\tests\test_files.py
F:\testprogram\better_Skill\tests\test_main.py
F:\testprogram\better_Skill\tests\test_judge.py
F:\testprogram\better_Skill\tests\test_optimizer.py
```

文件职责：

- `main.py`：解析命令，分发 `init-case`，运行优化循环。
- `config.py`：定义 `Config` 数据类和默认项目路径。
- `cases.py`：创建用例目录并加载用例元数据。
- `files.py`：创建运行目录、备份 `SKILL.md`、精确比较期望文件树、写入运行产物。
- `runner.py`：调用 Claude CLI 执行 SKILL。
- `judge.py`：解析裁判输出，并合并文本/文件分数。
- `optimizer.py`：校验并应用修订后的 `SKILL.md` 内容。
- `tests/`：标准库单元测试；通过假命令或直接测试函数，避免依赖真实 Claude CLI。

---

### Task 1: Establish Configuration Module

**Files:**
- Create: `F:\testprogram\better_Skill\skill_optimizer\__init__.py`
- Create: `F:\testprogram\better_Skill\skill_optimizer\config.py`
- Create: `F:\testprogram\better_Skill\tests\test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `F:\testprogram\better_Skill\tests\test_config.py`:

```python
import unittest
from pathlib import Path

from skill_optimizer.config import Config, default_config


class ConfigTests(unittest.TestCase):
    def test_default_config_uses_project_root_paths(self):
        config = default_config(Path("F:/testprogram/better_Skill"))

        self.assertEqual(config.project_root, Path("F:/testprogram/better_Skill"))
        self.assertEqual(config.workspace_dir, Path("F:/testprogram/better_Skill/workspace"))
        self.assertEqual(config.skill_path, Path("F:/testprogram/better_Skill/workspace/SKILL.md"))
        self.assertEqual(config.test_cases_dir, Path("F:/testprogram/better_Skill/test_cases"))
        self.assertEqual(config.runs_dir, Path("F:/testprogram/better_Skill/workspace/runs"))
        self.assertEqual(config.backups_dir, Path("F:/testprogram/better_Skill/workspace/backups"))
        self.assertEqual(config.score_threshold, 0.85)
        self.assertEqual(config.max_iterations, 5)
        self.assertEqual(config.default_case_timeout_seconds, 120)
        self.assertEqual(config.claude_cmd, "claude")

    def test_config_is_constructible_for_tests(self):
        config = Config(
            project_root=Path("C:/tmp/project"),
            workspace_dir=Path("C:/tmp/project/workspace"),
            skill_path=Path("C:/tmp/project/workspace/SKILL.md"),
            test_cases_dir=Path("C:/tmp/project/test_cases"),
            runs_dir=Path("C:/tmp/project/workspace/runs"),
            backups_dir=Path("C:/tmp/project/workspace/backups"),
            score_threshold=0.9,
            max_iterations=3,
            default_case_timeout_seconds=60,
            claude_cmd="claude",
        )

        self.assertEqual(config.score_threshold, 0.9)
        self.assertEqual(config.max_iterations, 3)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `skill_optimizer.config`.

- [ ] **Step 3: Implement the minimal module**

Create empty package marker `F:\testprogram\better_Skill\skill_optimizer\__init__.py`:

```python
```

Create `F:\testprogram\better_Skill\skill_optimizer\config.py`:

```python
from dataclasses import dataclass
from pathlib import Path


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
    claude_cmd: str


def default_config(project_root: Path) -> Config:
    workspace_dir = project_root / "workspace"
    return Config(
        project_root=project_root,
        workspace_dir=workspace_dir,
        skill_path=workspace_dir / "SKILL.md",
        test_cases_dir=project_root / "test_cases",
        runs_dir=workspace_dir / "runs",
        backups_dir=workspace_dir / "backups",
        score_threshold=0.85,
        max_iterations=5,
        default_case_timeout_seconds=120,
        claude_cmd="claude",
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py -v
```

Expected: PASS. This project is not a git repository, so do not run commit commands unless the user has initialized git.

---

### Task 2: Implement Case Template Creation

**Files:**
- Create: `F:\testprogram\better_Skill\skill_optimizer\cases.py`
- Create: `F:\testprogram\better_Skill\tests\test_cases.py`

- [ ] **Step 1: Write the failing tests**

Create `F:\testprogram\better_Skill\tests\test_cases.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_cases.py -v
```

Expected: FAIL with `ImportError` or missing `create_case_template`.

- [ ] **Step 3: Implement case template creation**

Create `F:\testprogram\better_Skill\skill_optimizer\cases.py`:

```python
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
    case_type: str
    min_score: float
    timeout_seconds: int


def create_case_template(
    test_cases_dir: Path,
    case_name: str,
    case_type: str,
    min_score: float,
    timeout_seconds: int,
) -> Path:
    if case_type not in VALID_CASE_TYPES:
        raise ValueError(f"Unsupported case type: {case_type}")

    case_dir = test_cases_dir / case_name
    if case_dir.exists():
        raise FileExistsError(f"Case directory already exists: {case_dir}")

    case_dir.mkdir(parents=True)
    (case_dir / "prompt.txt").write_text("", encoding="utf-8")
    (case_dir / "expected.txt").write_text("", encoding="utf-8")
    (case_dir / "expected_files").mkdir()
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_cases.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py F:/testprogram/better_Skill/tests/test_cases.py -v
```

Expected: PASS.

---

### Task 3: Implement Case Loading for Multiple Numbered Directories

**Files:**
- Modify: `F:\testprogram\better_Skill\skill_optimizer\cases.py`
- Modify: `F:\testprogram\better_Skill\tests\test_cases.py`

- [ ] **Step 1: Add failing tests for loading cases**

Append these tests inside `CreateCaseTemplateTests` in `F:\testprogram\better_Skill\tests\test_cases.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_cases.py -v
```

Expected: FAIL because `load_cases` does not exist.

- [ ] **Step 3: Implement `load_cases`**

Replace `F:\testprogram\better_Skill\skill_optimizer\cases.py` with:

```python
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
    case_type: str
    min_score: float
    timeout_seconds: int


def create_case_template(
    test_cases_dir: Path,
    case_name: str,
    case_type: str,
    min_score: float,
    timeout_seconds: int,
) -> Path:
    if case_type not in VALID_CASE_TYPES:
        raise ValueError(f"Unsupported case type: {case_type}")

    case_dir = test_cases_dir / case_name
    if case_dir.exists():
        raise FileExistsError(f"Case directory already exists: {case_dir}")

    case_dir.mkdir(parents=True)
    (case_dir / "prompt.txt").write_text("", encoding="utf-8")
    (case_dir / "expected.txt").write_text("", encoding="utf-8")
    (case_dir / "expected_files").mkdir()
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
        cases.append(
            TestCase(
                name=case_name,
                case_dir=case_dir,
                prompt_path=prompt_path,
                expected_text_path=expected_text_path if expected_text_path.is_file() else None,
                expected_files_dir=expected_files_dir if expected_files_dir.is_dir() else None,
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_cases.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 4: Implement File Utilities

**Files:**
- Create: `F:\testprogram\better_Skill\skill_optimizer\files.py`
- Create: `F:\testprogram\better_Skill\tests\test_files.py`

- [ ] **Step 1: Write failing tests for backup and file comparison**

Create `F:\testprogram\better_Skill\tests\test_files.py`:

```python
import tempfile
import unittest
from pathlib import Path

from skill_optimizer.files import backup_file, compare_expected_files, create_iteration_dir


class FileUtilityTests(unittest.TestCase):
    def test_backup_file_copies_content_to_backup_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "SKILL.md"
            backups = root / "backups"
            source.write_text("skill content", encoding="utf-8")

            backup_path = backup_file(source, backups)

            self.assertTrue(backup_path.is_file())
            self.assertEqual(backup_path.read_text(encoding="utf-8"), "skill content")
            self.assertTrue(backup_path.name.startswith("SKILL_"))
            self.assertEqual(backup_path.suffix, ".md")

    def test_create_iteration_dir_uses_three_digit_number(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runs_dir = Path(temp_dir) / "runs"

            iter_dir = create_iteration_dir(runs_dir, 2)

            self.assertEqual(iter_dir, runs_dir / "iter_002")
            self.assertTrue(iter_dir.is_dir())

    def test_compare_expected_files_passes_and_ignores_extra_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = root / "expected"
            actual = root / "actual"
            (expected / "nested").mkdir(parents=True)
            (actual / "nested").mkdir(parents=True)
            (expected / "nested" / "result.txt").write_text("ok", encoding="utf-8")
            (actual / "nested" / "result.txt").write_text("ok", encoding="utf-8")
            (actual / "extra.txt").write_text("ignored", encoding="utf-8")

            result = compare_expected_files(expected, actual)

            self.assertTrue(result.passed)
            self.assertEqual(result.failures, [])

    def test_compare_expected_files_reports_missing_and_different_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = root / "expected"
            actual = root / "actual"
            expected.mkdir()
            actual.mkdir()
            (expected / "missing.txt").write_text("missing", encoding="utf-8")
            (expected / "different.txt").write_text("expected", encoding="utf-8")
            (actual / "different.txt").write_text("actual", encoding="utf-8")

            result = compare_expected_files(expected, actual)

            self.assertFalse(result.passed)
            self.assertIn("missing.txt is missing", result.failures)
            self.assertIn("different.txt content differs", result.failures)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_files.py -v
```

Expected: FAIL because `skill_optimizer.files` does not exist.

- [ ] **Step 3: Implement file utilities**

Create `F:\testprogram\better_Skill\skill_optimizer\files.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_files.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 5: Implement Claude CLI Runner

**Files:**
- Create: `F:\testprogram\better_Skill\skill_optimizer\runner.py`
- Create: `F:\testprogram\better_Skill\tests\test_runner.py`

- [ ] **Step 1: Write failing runner tests**

Create `F:\testprogram\better_Skill\tests\test_runner.py`:

```python
import sys
import tempfile
import unittest
from pathlib import Path

from skill_optimizer.runner import run_claude_prompt


class RunnerTests(unittest.TestCase):
    def test_run_claude_prompt_captures_stdout_stderr_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            command = sys.executable
            script = "import sys; print('ok'); print('warn', file=sys.stderr)"

            result = run_claude_prompt(command, ["-c", script], "ignored prompt", run_dir, 30)

            self.assertEqual(result.return_code, 0)
            self.assertEqual(result.stdout.strip(), "ok")
            self.assertEqual(result.stderr.strip(), "warn")
            self.assertEqual((run_dir / "stdout.txt").read_text(encoding="utf-8").strip(), "ok")
            self.assertEqual((run_dir / "stderr.txt").read_text(encoding="utf-8").strip(), "warn")
            self.assertEqual((run_dir / "prompt.txt").read_text(encoding="utf-8"), "ignored prompt")

    def test_run_claude_prompt_records_timeout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            command = sys.executable
            script = "import time; time.sleep(2)"

            result = run_claude_prompt(command, ["-c", script], "prompt", run_dir, 1)

            self.assertNotEqual(result.return_code, 0)
            self.assertIn("timed out", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_runner.py -v
```

Expected: FAIL because `skill_optimizer.runner` does not exist.

- [ ] **Step 3: Implement runner**

Create `F:\testprogram\better_Skill\skill_optimizer\runner.py`:

```python
import subprocess
from dataclasses import dataclass
from pathlib import Path

from skill_optimizer.files import write_text_artifact


@dataclass(frozen=True)
class RunResult:
    stdout: str
    stderr: str
    return_code: int
    run_dir: Path


def run_claude_prompt(
    command: str,
    args: list[str],
    prompt: str,
    run_dir: Path,
    timeout_seconds: int,
) -> RunResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_text_artifact(run_dir / "prompt.txt", prompt)
    try:
        completed = subprocess.run(
            [command, *args],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        return_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = f"Command timed out after {timeout_seconds} seconds"
        return_code = 124
    except FileNotFoundError as exc:
        stdout = ""
        stderr = str(exc)
        return_code = 127

    write_text_artifact(run_dir / "stdout.txt", stdout)
    write_text_artifact(run_dir / "stderr.txt", stderr)
    write_text_artifact(run_dir / "return_code.txt", str(return_code))
    return RunResult(stdout=stdout, stderr=stderr, return_code=return_code, run_dir=run_dir)


def build_skill_execution_prompt(skill_content: str, user_prompt: str) -> str:
    return (
        "You are evaluating the following Claude SKILL instructions.\n\n"
        "<skill>\n"
        f"{skill_content}\n"
        "</skill>\n\n"
        "Apply the skill to this user request:\n\n"
        f"{user_prompt}\n"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_runner.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 6: Implement Judge Result Parsing and Score Combination

**Files:**
- Create: `F:\testprogram\better_Skill\skill_optimizer\judge.py`
- Create: `F:\testprogram\better_Skill\tests\test_judge.py`

- [ ] **Step 1: Write failing judge tests**

Create `F:\testprogram\better_Skill\tests\test_judge.py`:

```python
import unittest

from skill_optimizer.files import FileCheckResult
from skill_optimizer.judge import combine_scores, parse_judge_output


class JudgeTests(unittest.TestCase):
    def test_parse_judge_output_reads_score_and_reason_json(self):
        result = parse_judge_output('{"score": 0.75, "reason": "mostly correct"}')

        self.assertEqual(result.score, 0.75)
        self.assertEqual(result.reason, "mostly correct")

    def test_parse_judge_output_rejects_invalid_score(self):
        with self.assertRaises(ValueError):
            parse_judge_output('{"score": 2, "reason": "bad"}')

    def test_combine_scores_for_text_only(self):
        score, passed = combine_scores(text_score=0.9, file_result=None, min_score=0.85)

        self.assertEqual(score, 0.9)
        self.assertTrue(passed)

    def test_combine_scores_fails_when_file_check_fails(self):
        file_result = FileCheckResult(passed=False, failures=["result.md content differs"])

        score, passed = combine_scores(text_score=0.9, file_result=file_result, min_score=0.85)

        self.assertEqual(score, 0.0)
        self.assertFalse(passed)

    def test_combine_scores_for_file_only_success(self):
        file_result = FileCheckResult(passed=True, failures=[])

        score, passed = combine_scores(text_score=None, file_result=file_result, min_score=0.85)

        self.assertEqual(score, 1.0)
        self.assertTrue(passed)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_judge.py -v
```

Expected: FAIL because `skill_optimizer.judge` does not exist.

- [ ] **Step 3: Implement judge helpers**

Create `F:\testprogram\better_Skill\skill_optimizer\judge.py`:

```python
import json
from dataclasses import dataclass

from skill_optimizer.files import FileCheckResult


@dataclass(frozen=True)
class JudgeResult:
    score: float
    reason: str


def parse_judge_output(output: str) -> JudgeResult:
    data = json.loads(output)
    score = float(data["score"])
    if score < 0 or score > 1:
        raise ValueError(f"Judge score must be between 0 and 1: {score}")
    reason = str(data.get("reason", ""))
    return JudgeResult(score=score, reason=reason)


def build_judge_prompt(actual: str, expected: str) -> str:
    return (
        "Compare the actual answer with the expected answer. "
        "Return only JSON with keys score and reason. "
        "score must be between 0 and 1.\n\n"
        "<expected>\n"
        f"{expected}\n"
        "</expected>\n\n"
        "<actual>\n"
        f"{actual}\n"
        "</actual>\n"
    )


def combine_scores(
    text_score: float | None,
    file_result: FileCheckResult | None,
    min_score: float,
) -> tuple[float, bool]:
    if file_result is not None and not file_result.passed:
        return 0.0, False
    if text_score is None:
        score = 1.0 if file_result is not None and file_result.passed else 0.0
    else:
        score = text_score
    return score, score >= min_score
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_judge.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 7: Implement Skill Revision Safeguards

**Files:**
- Create: `F:\testprogram\better_Skill\skill_optimizer\optimizer.py`
- Create: `F:\testprogram\better_Skill\tests\test_optimizer.py`

- [ ] **Step 1: Write failing optimizer tests**

Create `F:\testprogram\better_Skill\tests\test_optimizer.py`:

```python
import tempfile
import unittest
from pathlib import Path

from skill_optimizer.optimizer import apply_revision_with_backup, validate_skill_revision


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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_optimizer.py -v
```

Expected: FAIL because `skill_optimizer.optimizer` does not exist.

- [ ] **Step 3: Implement optimizer safeguards**

Create `F:\testprogram\better_Skill\skill_optimizer\optimizer.py`:

```python
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
        "Improve this Claude SKILL.md so it passes the failed test cases. "
        "Return only the complete revised SKILL.md content.\n\n"
        "<current_skill>\n"
        f"{skill_content}\n"
        "</current_skill>\n\n"
        "<failures>\n"
        f"{failure_summary}\n"
        "</failures>\n"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_optimizer.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 8: Implement `init-case` Command in `main.py`

**Files:**
- Modify: `F:\testprogram\better_Skill\main.py`
- Create: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **Step 1: Write failing CLI tests**

Create `F:\testprogram\better_Skill\tests\test_main.py`:

```python
import tempfile
import unittest
from pathlib import Path

from main import build_parser, handle_init_case
from skill_optimizer.config import default_config


class MainCommandTests(unittest.TestCase):
    def test_parser_accepts_init_case_with_type(self):
        parser = build_parser()

        args = parser.parse_args(["init-case", "case_001", "--type", "files"])

        self.assertEqual(args.command, "init-case")
        self.assertEqual(args.case_name, "case_001")
        self.assertEqual(args.case_type, "files")

    def test_handle_init_case_creates_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = default_config(Path(temp_dir))
            parser = build_parser()
            args = parser.parse_args(["init-case", "case_001", "--type", "mixed"])

            exit_code = handle_init_case(args, config)

            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(temp_dir) / "test_cases" / "case_001" / "metadata.json").is_file())

    def test_handle_init_case_returns_error_for_existing_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = default_config(Path(temp_dir))
            parser = build_parser()
            args = parser.parse_args(["init-case", "case_001"])
            handle_init_case(args, config)

            exit_code = handle_init_case(args, config)

            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: FAIL because `build_parser` and `handle_init_case` do not exist.

- [ ] **Step 3: Replace `main.py` with command parser and init-case handler**

Replace `F:\testprogram\better_Skill\main.py` with:

```python
import argparse
from pathlib import Path

from skill_optimizer.cases import create_case_template
from skill_optimizer.config import Config, default_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optimize Claude SKILL.md with test cases")
    subparsers = parser.add_subparsers(dest="command")

    init_case = subparsers.add_parser("init-case", help="Create a test case directory template")
    init_case.add_argument("case_name")
    init_case.add_argument("--type", dest="case_type", choices=["text", "files", "mixed"], default="mixed")
    init_case.add_argument("--min-score", type=float, default=0.85)
    init_case.add_argument("--timeout", type=int, default=120)

    return parser


def handle_init_case(args: argparse.Namespace, config: Config) -> int:
    try:
        case_dir = create_case_template(
            config.test_cases_dir,
            args.case_name,
            args.case_type,
            args.min_score,
            args.timeout,
        )
    except FileExistsError as exc:
        print(str(exc))
        return 1
    except ValueError as exc:
        print(str(exc))
        return 1

    print(f"Created test case: {case_dir}")
    return 0


def run_optimization(config: Config) -> int:
    print("Optimization flow is not implemented yet")
    return 1


def main() -> int:
    project_root = Path(__file__).resolve().parent
    config = default_config(project_root)
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-case":
        return handle_init_case(args, config)
    return run_optimization(config)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: PASS.

- [ ] **Step 5: Manually verify `init-case`**

Run:

```bash
python F:/testprogram/better_Skill/main.py init-case case_001 --type mixed
```

Expected: command prints `Created test case:` and creates `F:\testprogram\better_Skill\test_cases\case_001\prompt.txt`, `expected.txt`, `expected_files\`, and `metadata.json`.

- [ ] **Step 6: Verify existing case is not overwritten**

Run:

```bash
python F:/testprogram/better_Skill/main.py init-case case_001 --type mixed
```

Expected: command exits non-zero and prints `Case directory already exists`.

---

### Task 9: Implement One Iteration of Evaluation Without Revision

**Files:**
- Modify: `F:\testprogram\better_Skill\main.py`
- Modify: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **Step 1: Add failing test for missing skill and empty cases**

Append to `F:\testprogram\better_Skill\tests\test_main.py`:

```python
    def test_run_optimization_requires_skill_file(self):
        from main import run_optimization

        with tempfile.TemporaryDirectory() as temp_dir:
            config = default_config(Path(temp_dir))

            exit_code = run_optimization(config)

            self.assertEqual(exit_code, 1)
```

- [ ] **Step 2: Run tests to verify failure or incomplete behavior**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: current placeholder returns 1, so the new test may pass. If it passes, continue by adding the next behavior test in Step 3.

- [ ] **Step 3: Add failing test for loading multiple cases**

Append to `F:\testprogram\better_Skill\tests\test_main.py`:

```python
    def test_run_optimization_reports_no_cases(self):
        from main import run_optimization

        with tempfile.TemporaryDirectory() as temp_dir:
            config = default_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text("---\nname: test\ndescription: test skill\n---\n\nBody text", encoding="utf-8")

            exit_code = run_optimization(config)

            self.assertEqual(exit_code, 1)
```

- [ ] **Step 4: Implement skill and case preflight checks**

Modify `run_optimization` in `F:\testprogram\better_Skill\main.py` to:

```python
def run_optimization(config: Config) -> int:
    from skill_optimizer.cases import load_cases

    if not config.skill_path.is_file():
        print(f"Missing SKILL.md: {config.skill_path}")
        return 1

    cases = load_cases(
        config.test_cases_dir,
        default_min_score=config.score_threshold,
        default_timeout_seconds=config.default_case_timeout_seconds,
    )
    if not cases:
        print(f"No test cases found in: {config.test_cases_dir}")
        return 1

    print(f"Loaded {len(cases)} test case(s)")
    return 0
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: PASS.

- [ ] **Step 6: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 10: Implement Evaluation Loop with Injectable Fake Claude Command

**Files:**
- Modify: `F:\testprogram\better_Skill\config.py`
- Modify: `F:\testprogram\better_Skill\main.py`
- Modify: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **Step 1: Add failing integration-style test using Python as fake command**

Append to `F:\testprogram\better_Skill\tests\test_main.py`:

```python
    def test_run_optimization_creates_iteration_directory_for_cases(self):
        from dataclasses import replace
        import sys
        from main import run_optimization
        from skill_optimizer.cases import create_case_template

        with tempfile.TemporaryDirectory() as temp_dir:
            config = default_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: test-skill\ndescription: test skill\n---\n\nReturn the expected answer.",
                encoding="utf-8",
            )
            case_dir = create_case_template(config.test_cases_dir, "case_001", "text", 0.1, 30)
            (case_dir / "prompt.txt").write_text("say hello", encoding="utf-8")
            (case_dir / "expected.txt").write_text("hello", encoding="utf-8")
            fake_config = replace(config, claude_cmd=sys.executable)

            exit_code = run_optimization(fake_config, claude_args=["-c", "print('{\\\"score\\\": 1.0, \\\"reason\\\": \\\"ok\\\"}')"])

            self.assertEqual(exit_code, 0)
            self.assertTrue((config.runs_dir / "iter_001" / "case_001" / "stdout.txt").is_file())
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: FAIL because `run_optimization` does not accept `claude_args` and does not create iteration directories.

- [ ] **Step 3: Implement basic one-iteration evaluation**

Replace `run_optimization` in `F:\testprogram\better_Skill\main.py` with:

```python
def run_optimization(config: Config, claude_args: list[str] | None = None) -> int:
    from skill_optimizer.cases import load_cases
    from skill_optimizer.files import create_iteration_dir
    from skill_optimizer.judge import combine_scores, parse_judge_output
    from skill_optimizer.runner import build_skill_execution_prompt, run_claude_prompt

    if not config.skill_path.is_file():
        print(f"Missing SKILL.md: {config.skill_path}")
        return 1

    cases = load_cases(
        config.test_cases_dir,
        default_min_score=config.score_threshold,
        default_timeout_seconds=config.default_case_timeout_seconds,
    )
    if not cases:
        print(f"No test cases found in: {config.test_cases_dir}")
        return 1

    skill_content = config.skill_path.read_text(encoding="utf-8")
    iteration_dir = create_iteration_dir(config.runs_dir, 1)
    passed_count = 0
    scores: list[float] = []
    args = claude_args or []

    for case in cases:
        prompt = case.prompt_path.read_text(encoding="utf-8")
        execution_prompt = build_skill_execution_prompt(skill_content, prompt)
        case_run_dir = iteration_dir / case.name
        result = run_claude_prompt(config.claude_cmd, args, execution_prompt, case_run_dir, case.timeout_seconds)
        if result.return_code != 0:
            scores.append(0.0)
            continue

        text_score = None
        if case.expected_text_path is not None:
            judge_result = parse_judge_output(result.stdout.strip())
            text_score = judge_result.score
        score, passed = combine_scores(text_score=text_score, file_result=None, min_score=case.min_score)
        scores.append(score)
        if passed:
            passed_count += 1

    average_score = sum(scores) / len(scores)
    print(f"Passed {passed_count}/{len(cases)} case(s), average score {average_score:.2f}")
    return 0 if passed_count == len(cases) and average_score >= config.score_threshold else 1
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 11: Add Exact File Checking to Evaluation

**Files:**
- Modify: `F:\testprogram\better_Skill\main.py`
- Modify: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **Step 1: Add failing test for expected files**

Append to `F:\testprogram\better_Skill\tests\test_main.py`:

```python
    def test_run_optimization_checks_expected_files(self):
        from main import run_optimization
        from skill_optimizer.cases import create_case_template

        with tempfile.TemporaryDirectory() as temp_dir:
            config = default_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: test-skill\ndescription: test skill\n---\n\nCreate files.",
                encoding="utf-8",
            )
            case_dir = create_case_template(config.test_cases_dir, "case_001", "files", 0.85, 30)
            (case_dir / "prompt.txt").write_text("create result", encoding="utf-8")
            (case_dir / "expected_files" / "result.txt").write_text("expected", encoding="utf-8")

            actual_dir = config.runs_dir / "iter_001" / "case_001" / "actual_files"
            actual_dir.mkdir(parents=True)
            (actual_dir / "result.txt").write_text("expected", encoding="utf-8")

            exit_code = run_optimization(config, skip_execution=True)

            self.assertEqual(exit_code, 0)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: FAIL because `run_optimization` does not accept `skip_execution` or compare files.

- [ ] **Step 3: Update evaluation to compare expected files**

Modify `run_optimization` signature and case loop in `F:\testprogram\better_Skill\main.py` to this complete version:

```python
def run_optimization(
    config: Config,
    claude_args: list[str] | None = None,
    skip_execution: bool = False,
) -> int:
    from skill_optimizer.cases import load_cases
    from skill_optimizer.files import compare_expected_files, create_iteration_dir
    from skill_optimizer.judge import combine_scores, parse_judge_output
    from skill_optimizer.runner import build_skill_execution_prompt, run_claude_prompt

    if not config.skill_path.is_file():
        print(f"Missing SKILL.md: {config.skill_path}")
        return 1

    cases = load_cases(
        config.test_cases_dir,
        default_min_score=config.score_threshold,
        default_timeout_seconds=config.default_case_timeout_seconds,
    )
    if not cases:
        print(f"No test cases found in: {config.test_cases_dir}")
        return 1

    skill_content = config.skill_path.read_text(encoding="utf-8")
    iteration_dir = create_iteration_dir(config.runs_dir, 1)
    passed_count = 0
    scores: list[float] = []
    args = claude_args or []

    for case in cases:
        case_run_dir = iteration_dir / case.name
        if skip_execution:
            stdout = ""
            return_code = 0
        else:
            prompt = case.prompt_path.read_text(encoding="utf-8")
            execution_prompt = build_skill_execution_prompt(skill_content, prompt)
            result = run_claude_prompt(config.claude_cmd, args, execution_prompt, case_run_dir, case.timeout_seconds)
            stdout = result.stdout
            return_code = result.return_code

        if return_code != 0:
            scores.append(0.0)
            continue

        text_score = None
        if case.expected_text_path is not None and case.expected_text_path.read_text(encoding="utf-8").strip():
            judge_result = parse_judge_output(stdout.strip())
            text_score = judge_result.score

        file_result = None
        if case.expected_files_dir is not None:
            actual_files_dir = case_run_dir / "actual_files"
            file_result = compare_expected_files(case.expected_files_dir, actual_files_dir)

        score, passed = combine_scores(text_score=text_score, file_result=file_result, min_score=case.min_score)
        scores.append(score)
        if passed:
            passed_count += 1

    average_score = sum(scores) / len(scores)
    print(f"Passed {passed_count}/{len(cases)} case(s), average score {average_score:.2f}")
    return 0 if passed_count == len(cases) and average_score >= config.score_threshold else 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: PASS.

- [ ] **Step 5: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 12: Implement Iterative Revision Loop

**Files:**
- Modify: `F:\testprogram\better_Skill\main.py`
- Modify: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **Step 1: Add failing test for revision after failure**

Append to `F:\testprogram\better_Skill\tests\test_main.py`:

```python
    def test_apply_revision_after_failed_score(self):
        from main import apply_revision_if_needed

        with tempfile.TemporaryDirectory() as temp_dir:
            config = default_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: weak-skill\ndescription: weak skill\n---\n\nThis is intentionally weak.",
                encoding="utf-8",
            )
            new_skill = "---\nname: better-skill\ndescription: better skill\n---\n\nThis skill is now detailed enough to pass the tests."

            changed = apply_revision_if_needed(config, average_score=0.2, failure_summary="bad answer", new_skill_content=new_skill)

            self.assertTrue(changed)
            self.assertIn("better-skill", config.skill_path.read_text(encoding="utf-8"))
            self.assertTrue(any(config.backups_dir.iterdir()))
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: FAIL because `apply_revision_if_needed` does not exist.

- [ ] **Step 3: Implement revision helper**

Add this function to `F:\testprogram\better_Skill\main.py` above `run_optimization`:

```python
def apply_revision_if_needed(
    config: Config,
    average_score: float,
    failure_summary: str,
    new_skill_content: str,
) -> bool:
    from skill_optimizer.optimizer import apply_revision_with_backup

    if average_score >= config.score_threshold:
        return False
    apply_revision_with_backup(config.skill_path, config.backups_dir, new_skill_content)
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

Expected: PASS.

- [ ] **Step 5: Extend real loop after helper is tested**

Replace the last two lines of `run_optimization` with this explicit stop behavior:

```python
    average_score = sum(scores) / len(scores)
    print(f"Passed {passed_count}/{len(cases)} case(s), average score {average_score:.2f}")
    if passed_count == len(cases) and average_score >= config.score_threshold:
        return 0
    print("Score threshold not met. Revision generation will run in the next implementation step.")
    return 1
```

Expected: This task proves safe backup and overwrite behavior separately before wiring live Claude revision calls.

- [ ] **Step 6: Checkpoint**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all current tests PASS.

---

### Task 13: Wire Claude-Based Revision Generation

**Files:**
- Modify: `F:\testprogram\better_Skill\main.py`

- [ ] **Step 1: Add a small revision function that uses existing runner**

Add this function to `F:\testprogram\better_Skill\main.py`:

```python
def generate_revision_with_claude(
    config: Config,
    failure_summary: str,
    run_dir: Path,
    claude_args: list[str] | None = None,
) -> str:
    from skill_optimizer.optimizer import build_revision_prompt
    from skill_optimizer.runner import run_claude_prompt

    skill_content = config.skill_path.read_text(encoding="utf-8")
    prompt = build_revision_prompt(skill_content, failure_summary)
    result = run_claude_prompt(
        config.claude_cmd,
        claude_args or [],
        prompt,
        run_dir,
        config.default_case_timeout_seconds,
    )
    if result.return_code != 0:
        raise RuntimeError(result.stderr)
    return result.stdout
```

- [ ] **Step 2: Wire revision into non-passing runs**

In `run_optimization`, replace the final failing branch with:

```python
    if passed_count == len(cases) and average_score >= config.score_threshold:
        return 0

    failure_summary = f"Passed {passed_count}/{len(cases)} case(s), average score {average_score:.2f}"
    revision_dir = iteration_dir / "revision"
    try:
        new_skill_content = generate_revision_with_claude(config, failure_summary, revision_dir, claude_args=args)
        apply_revision_if_needed(config, average_score, failure_summary, new_skill_content)
    except Exception as exc:
        print(f"Revision failed: {exc}")
        return 1
    print("Applied revised SKILL.md")
    return 1
```

- [ ] **Step 3: Run full tests**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all tests PASS. Existing tests should not require real Claude CLI because they pass fake command args or test helpers directly.

- [ ] **Step 4: Manual smoke test with real command availability check**

Run:

```bash
python F:/testprogram/better_Skill/main.py
```

Expected if no workspace/cases exist yet: exits with a clear `Missing SKILL.md` or `No test cases found` message. Do not require real Claude CLI until a valid `workspace/SKILL.md` and cases exist.

---

### Task 14: Add Example Workspace and Case Skeletons

**Files:**
- Create: `F:\testprogram\better_Skill\workspace\SKILL.md`
- Create: `F:\testprogram\better_Skill\test_cases\case_001\prompt.txt`
- Create: `F:\testprogram\better_Skill\test_cases\case_001\expected.txt`
- Create: `F:\testprogram\better_Skill\test_cases\case_001\metadata.json`
- Create: `F:\testprogram\better_Skill\test_cases\case_001\expected_files\.gitkeep`

- [ ] **Step 1: Create sample skill**

Create `F:\testprogram\better_Skill\workspace\SKILL.md`:

```markdown
---
name: sample-answer-skill
description: Answers simple test prompts with concise, verifiable output
---

# Sample Answer Skill

When given a test prompt, answer directly and preserve any exact wording requested by the prompt.
```

- [ ] **Step 2: Create sample case files**

Create `F:\testprogram\better_Skill\test_cases\case_001\prompt.txt`:

```text
Respond with exactly: hello skill
```

Create `F:\testprogram\better_Skill\test_cases\case_001\expected.txt`:

```text
hello skill
```

Create `F:\testprogram\better_Skill\test_cases\case_001\metadata.json`:

```json
{
  "name": "case_001",
  "type": "text",
  "min_score": 0.85,
  "timeout_seconds": 120
}
```

Create `F:\testprogram\better_Skill\test_cases\case_001\expected_files\.gitkeep` as an empty file.

- [ ] **Step 3: Run tests**

Run:

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

Expected: all tests PASS.

- [ ] **Step 4: Manual case generation check**

Run:

```bash
python F:/testprogram/better_Skill/main.py init-case case_002 --type files
```

Expected: creates `F:\testprogram\better_Skill\test_cases\case_002` with `prompt.txt`, `expected.txt`, `expected_files`, and `metadata.json`.

---

## 最终验证

运行全部单元测试：

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

期望：所有测试通过。

手动运行用例创建命令：

```bash
python F:/testprogram/better_Skill/main.py init-case case_999 --type mixed
python F:/testprogram/better_Skill/main.py init-case case_999 --type mixed
```

期望：第一次命令创建用例；第二次命令拒绝覆盖已有用例。

运行优化器预检：

```bash
python F:/testprogram/better_Skill/main.py
```

期望：如果存在有效的 `workspace/SKILL.md` 和至少一个用例，就加载用例并尝试执行 Claude CLI。如果没有安装 Claude CLI，应通过 runner 的 stderr 产物清晰失败，而不是崩溃。

## 自查

- 规格覆盖：计划覆盖脚本模块、多个用例目录、`init-case`、文本评分、精确文件检查、备份、自动覆盖、运行产物和停止行为。
- 占位扫描：没有 `TBD`、`TODO` 或未说明的实施步骤。
- 类型一致性：`Config`、`TestCase`、`FileCheckResult`、`RunResult` 和 `JudgeResult` 都先定义后使用，字段名在各任务中保持稳定。
- 范围检查：Web UI、包发布、插件注册表、YAML 和外部数据库明确排除在 MVP 之外。

## 执行提示

计划已保存到 `C:\Users\admin\.claude\plans\python-skill-skill-skill-sunny-babbage.md`。

用户已选择并再次确认执行方式：**子代理驱动（推荐）**。

执行要求：

- 实施前必须使用 `superpowers:subagent-driven-development`。
- 每个任务派发一个新的子代理执行。
- 每个任务完成后先复查实际改动和测试结果，再进入下一个任务。
- 如果技能调用被 hook 拦截，需要先处理 hook 配置，再开始实施。
