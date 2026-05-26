# Input Files 功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为所有用例类型增加可选的 `input_files/` 目录支持，使 executor 能够在已有文件基础上进行修改。

**Architecture:** 在 TestCase 数据类增加 `input_files_dir` 字段，在 files.py 增加 `copy_input_files` 函数，在 _evaluate_cases 执行前调用复制逻辑。CLI 的 init-case 子命令增加 `--with-input-files` 参数。

**Tech Stack:** Python 3.10+, pathlib, shutil, unittest

---

### Task 1: TestCase 增加 input_files_dir 字段 + load_cases 检测

**Files:**
- Modify: `skill_optimizer/cases.py`
- Modify: `tests/test_cases.py`

- [ ] **Step 1: 编写失败测试 — load_cases 检测 input_files 目录**

在 `tests/test_cases.py` 的 `CreateCaseTemplateTests` 类中增加两个测试方法：

```python
def test_load_cases_detects_input_files_dir(self):
    from skill_optimizer.cases import load_cases

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "test_cases"
        case_dir = create_case_template(root, "case_001", "files", 0.8, 60)
        (case_dir / "prompt.txt").write_text("modify the file", encoding="utf-8")
        (case_dir / "input_files").mkdir()
        (case_dir / "input_files" / "source.py").write_text("x = 1", encoding="utf-8")

        cases = load_cases(root, default_min_score=0.85, default_timeout_seconds=120)

        self.assertEqual(len(cases), 1)
        self.assertIsNotNone(cases[0].input_files_dir)
        self.assertEqual(cases[0].input_files_dir, case_dir / "input_files")

def test_load_cases_input_files_dir_none_when_missing(self):
    from skill_optimizer.cases import load_cases

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "test_cases"
        case_dir = create_case_template(root, "case_001", "text", 0.8, 60)
        (case_dir / "prompt.txt").write_text("hello", encoding="utf-8")

        cases = load_cases(root, default_min_score=0.85, default_timeout_seconds=120)

        self.assertEqual(len(cases), 1)
        self.assertIsNone(cases[0].input_files_dir)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_cases.py::CreateCaseTemplateTests::test_load_cases_detects_input_files_dir tests/test_cases.py::CreateCaseTemplateTests::test_load_cases_input_files_dir_none_when_missing -v
```
期望：两个测试均失败 — `unexpected keyword argument 'input_files_dir'` 或 `AttributeError`

- [ ] **Step 3: 修改 TestCase 数据类，增加字段**

在 `skill_optimizer/cases.py` 中：

```python
@dataclass(frozen=True)
class TestCase:
    name: str
    case_dir: Path
    prompt_path: Path
    expected_text_path: Path | None
    expected_files_dir: Path | None
    input_files_dir: Path | None  # 新增
    case_type: str
    min_score: float
    timeout_seconds: int
```

- [ ] **Step 4: 修改 load_cases，检测 input_files 目录**

在 `skill_optimizer/cases.py` 的 `load_cases` 函数中，在 `TestCase(...)` 构造调用中增加：

```python
input_files_dir = case_dir / "input_files"

cases.append(
    TestCase(
        name=case_name,
        case_dir=case_dir,
        prompt_path=prompt_path,
        expected_text_path=expected_text_path if expected_text_path.is_file() else None,
        expected_files_dir=expected_files_dir if expected_files_dir.is_dir() else None,
        input_files_dir=input_files_dir if input_files_dir.is_dir() else None,  # 新增
        case_type=case_type,
        min_score=float(metadata.get("min_score", default_min_score)),
        timeout_seconds=int(metadata.get("timeout_seconds", default_timeout_seconds)),
    )
)
```

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/test_cases.py -v
```
期望：全部 6 个测试通过

- [ ] **Step 6: 提交**

```bash
git add skill_optimizer/cases.py tests/test_cases.py
git commit -m "feat: TestCase 增加 input_files_dir 字段，load_cases 自动检测 input_files 目录"
```

---

### Task 2: create_case_template 支持 with_input_files 参数

**Files:**
- Modify: `skill_optimizer/cases.py`
- Modify: `tests/test_cases.py`

- [ ] **Step 1: 编写失败测试 — 带 with_input_files 创建模板**

在 `tests/test_cases.py` 的 `CreateCaseTemplateTests` 类中增加两个测试方法：

```python
def test_create_case_template_with_input_files(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "test_cases"

        case_dir = create_case_template(root, "case_001", "files", 0.85, 120, with_input_files=True)

        input_files_dir = case_dir / "input_files"
        self.assertTrue(input_files_dir.is_dir())

def test_create_case_template_without_input_files(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "test_cases"

        case_dir = create_case_template(root, "case_001", "text", 0.85, 120)

        input_files_dir = case_dir / "input_files"
        self.assertFalse(input_files_dir.exists())
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_cases.py::CreateCaseTemplateTests::test_create_case_template_with_input_files tests/test_cases.py::CreateCaseTemplateTests::test_create_case_template_without_input_files -v
```
期望：第一个测试失败 — `unexpected keyword argument 'with_input_files'`

- [ ] **Step 3: 修改 create_case_template 函数签名和实现**

在 `skill_optimizer/cases.py` 的 `create_case_template` 函数中：

```python
def create_case_template(
    test_cases_dir: Path,
    case_name: str,
    case_type: str,
    min_score: float,
    timeout_seconds: int,
    with_input_files: bool = False,  # 新增参数
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
    if with_input_files:                         # 新增
        (case_dir / "input_files").mkdir()       # 新增
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

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_cases.py -v
```
期望：全部 8 个测试通过

- [ ] **Step 5: 提交**

```bash
git add skill_optimizer/cases.py tests/test_cases.py
git commit -m "feat: create_case_template 支持 with_input_files 参数创建 input_files 目录"
```

---

### Task 3: 新增 copy_input_files 函数

**Files:**
- Modify: `skill_optimizer/files.py`
- Modify: `tests/test_files.py`

- [ ] **Step 1: 编写失败测试**

在 `tests/test_files.py` 的 `FileUtilityTests` 类中增加测试方法：

```python
def test_copy_input_files_copies_single_file(self):
    from skill_optimizer.files import copy_input_files

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        input_dir = root / "input_files"
        target_dir = root / "target"
        input_dir.mkdir()
        (input_dir / "source.py").write_text("print('hello')", encoding="utf-8")

        copy_input_files(input_dir, target_dir)

        copied = target_dir / "source.py"
        self.assertTrue(copied.is_file())
        self.assertEqual(copied.read_text(encoding="utf-8"), "print('hello')")

def test_copy_input_files_copies_nested_directories(self):
    from skill_optimizer.files import copy_input_files

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        input_dir = root / "input_files"
        target_dir = root / "target"
        (input_dir / "sub" / "nested").mkdir(parents=True)
        (input_dir / "sub" / "nested" / "data.txt").write_text("nested content", encoding="utf-8")
        (input_dir / "root_file.txt").write_text("root content", encoding="utf-8")

        copy_input_files(input_dir, target_dir)

        self.assertTrue((target_dir / "root_file.txt").is_file())
        self.assertTrue((target_dir / "sub" / "nested" / "data.txt").is_file())
        self.assertEqual(
            (target_dir / "sub" / "nested" / "data.txt").read_text(encoding="utf-8"),
            "nested content",
        )

def test_copy_input_files_handles_empty_directory(self):
    from skill_optimizer.files import copy_input_files

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        input_dir = root / "input_files"
        target_dir = root / "target"
        input_dir.mkdir()

        copy_input_files(input_dir, target_dir)

        self.assertTrue(target_dir.is_dir())
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_files.py -k "copy_input_files" -v
```
期望：3 个测试失败 — `ImportError: cannot import name 'copy_input_files'`

- [ ] **Step 3: 实现 copy_input_files 函数**

在 `skill_optimizer/files.py` 末尾增加：

```python
def copy_input_files(input_dir: Path, target_dir: Path) -> None:
    """将 input_dir 下所有文件递归复制到 target_dir。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    for src in input_dir.rglob("*"):
        if src.is_file():
            rel = src.relative_to(input_dir)
            dst = target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/test_files.py -v
```
期望：全部 6 个测试通过

- [ ] **Step 5: 提交**

```bash
git add skill_optimizer/files.py tests/test_files.py
git commit -m "feat: 新增 copy_input_files 函数，递归复制输入文件到目标目录"
```

---

### Task 4: _evaluate_cases 执行前复制输入文件

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 在 _evaluate_cases 中增加复制逻辑**

在 `main.py` 的 `_evaluate_cases` 函数中，在 `case_run_dir` 创建之后、executor 运行之前插入复制逻辑。修改 `case_run_dir` 创建方式，并在 executor 调用前增加：

```python
def _evaluate_cases(
    config: Config,
    cases: list,
    skill_content: str,
    iteration_dir: Path,
    exec_args: list[str],
    judge_args: list[str],
) -> tuple[int, int, list[float], list[str]]:
    from skill_optimizer.files import compare_expected_files, copy_input_files  # 修改：增加 copy_input_files 导入
    from skill_optimizer.judge import combine_scores, judge_text_simple, parse_judge_output
    from skill_optimizer.runner import build_skill_execution_prompt, run_claude_prompt

    passed_count = 0
    scores: list[float] = []
    failure_details: list[str] = []

    for case in cases:
        case_run_dir = iteration_dir / case.name
        # 新增：复制输入文件到工作目录
        if case.input_files_dir is not None:
            copy_input_files(case.input_files_dir, case_run_dir)
        prompt = case.prompt_path.read_text(encoding="utf-8")
        execution_prompt = build_skill_execution_prompt(skill_content, prompt)
        result = run_claude_prompt(
            config.executor, execution_prompt, case_run_dir,
            case.timeout_seconds, extra_args=exec_args,
        )

        # ... 后续代码不变 ...
```

注意：`run_claude_prompt` 内部已经有 `run_dir.mkdir(parents=True, exist_ok=True)`，所以 `copy_input_files` 在 `run_claude_prompt` 调用之前执行时需要 `case_run_dir` 存在。由于 `copy_input_files` 内部也有 `target_dir.mkdir(parents=True, exist_ok=True)`，这不会出问题。

- [ ] **Step 2: 运行现有测试确保无回归**

```bash
python -m pytest tests/test_main.py -v
```
期望：全部 7 个测试通过

- [ ] **Step 3: 运行全部测试**

```bash
python -m pytest tests/ -v
```
期望：全部测试通过

- [ ] **Step 4: 提交**

```bash
git add main.py
git commit -m "feat: _evaluate_cases 在 executor 运行前复制 input_files 到工作目录"
```

---

### Task 5: CLI init-case 增加 --with-input-files 参数

**Files:**
- Modify: `main.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: 编写失败测试 — CLI 解析和模板创建**

在 `tests/test_main.py` 的 `MainCommandTests` 类中增加两个测试方法：

```python
def test_parser_accepts_init_case_with_input_files(self):
    parser = build_parser()

    args = parser.parse_args(["init-case", "case_001", "--with-input-files"])

    self.assertTrue(args.with_input_files)

def test_parser_init_case_defaults_with_input_files_to_false(self):
    parser = build_parser()

    args = parser.parse_args(["init-case", "case_001"])

    self.assertFalse(args.with_input_files)

def test_handle_init_case_creates_input_files_when_requested(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        config = build_config(Path(temp_dir))
        parser = build_parser()
        args = parser.parse_args(["init-case", "case_001", "--with-input-files"])

        exit_code = handle_init_case(args, config)

        self.assertEqual(exit_code, 0)
        case_dir = Path(temp_dir) / "test_cases" / "case_001"
        self.assertTrue((case_dir / "input_files").is_dir())
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/test_main.py::MainCommandTests::test_parser_accepts_init_case_with_input_files tests/test_main.py::MainCommandTests::test_parser_init_case_defaults_with_input_files_to_false tests/test_main.py::MainCommandTests::test_handle_init_case_creates_input_files_when_requested -v
```
期望：测试失败 — `unrecognized arguments: --with-input-files` / `AttributeError`

- [ ] **Step 3: 修改 build_parser，增加 --with-input-files 参数**

在 `main.py` 的 `build_parser` 函数中，在 `init_case` 子命令定义处增加：

```python
init_case.add_argument("--with-input-files", action="store_true", default=False,
                       help="Create an input_files/ directory in the case template")
```

- [ ] **Step 4: 修改 handle_init_case，传递参数**

在 `main.py` 的 `handle_init_case` 函数中：

```python
def handle_init_case(args: argparse.Namespace, config: Config) -> int:
    try:
        case_dir = create_case_template(
            config.test_cases_dir,
            args.case_name,
            args.case_type,
            args.min_score,
            args.timeout,
            with_input_files=args.with_input_files,  # 新增
        )
    except FileExistsError as exc:
        print(str(exc))
        return 1
    except ValueError as exc:
        print(str(exc))
        return 1

    print(f"Created test case: {case_dir}")
    return 0
```

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/test_main.py -v
```
期望：全部 10 个测试通过

- [ ] **Step 6: 运行全部测试确认无回归**

```bash
python -m pytest tests/ -v
```
期望：全部测试通过

- [ ] **Step 7: 提交**

```bash
git add main.py tests/test_main.py
git commit -m "feat: init-case 子命令增加 --with-input-files 参数"
```

---

### Task 6: 更新 README.md 文档

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 在 README 用例结构说明中增加 input_files 目录**

在 `README.md` 的用例目录结构说明（第 62-70 行附近）中，更新为：

```
test_cases/case_001/
├── prompt.txt          # 用户输入（测试 prompt）
├── expected.txt        # 期望的文本输出
├── expected_files/     # 期望的输出文件
│   └── result.txt
├── input_files/        # [可选] 执行前复制到工作目录的初始文件
│   └── source.py
└── metadata.json       # 用例元数据
```

同时在 `init-case` 参数表中增加 `--with-input-files` 行。

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: README 补充 input_files 目录和 --with-input-files 参数说明"
```

---

### 实现顺序

```
Task 1 (TestCase 字段 + load_cases)  →  Task 2 (create_case_template)
                                           ↓
Task 3 (copy_input_files 函数)       →  Task 4 (_evaluate_cases 集成)
                                           ↓
Task 5 (CLI --with-input-files)       →  Task 6 (README 文档)
```

Task 1 和 Task 3 可以并行执行（无依赖关系）。Task 2 依赖 Task 1。Task 4 依赖 Task 3。Task 5 依赖 Task 2。Task 6 依赖 Task 5。
