# Skill Reference Files 支持实施计划

> **给执行代理的提示：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步实施。本计划使用复选框（`- [ ]`）跟踪进度。

**目标：** 让测试 runner 支持带 `references/`、`examples/`、`scripts/` 等子目录的 SKILL，通过将 workspace 复制到 case_run_dir 使 AI 能用 Read 工具按需读取参考文件，模拟真实 Claude Code 行为。

**架构：** workspace 目录改为纯 skill 目录（只含 SKILL.md 和资源子目录），运行产物（runs/backups）移至 `output/` 目录。执行前条件复制 workspace 到 case_run_dir，AI 在 cwd 中可用 Read 工具读取 reference 文件。

**技术栈：** Python 3 标准库（shutil、pathlib、unittest）

---

## 文件结构

修改这些文件：

```text
F:\testprogram\better_Skill\skill_optimizer\files.py        ← 新增 should_copy_skill_dir、copy_skill_dir
F:\testprogram\better_Skill\skill_optimizer\config.py       ← 新增 output_dir 字段，runs/backups 默认路径变更
F:\testprogram\better_Skill\main.py                         ← 新增 --output-dir 参数，_evaluate_cases 流程变更
F:\testprogram\better_Skill\skill_optimizer.json.example    ← 新增 output_dir，更新 runs/backups 路径
F:\testprogram\better_Skill\tests\test_files.py             ← 新增测试
F:\testprogram\better_Skill\tests\test_config.py            ← 更新路径断言
F:\testprogram\better_Skill\tests\test_main.py              ← 更新路径断言
```

---

### Task 1: 在 files.py 中添加 skill 目录复制功能

**文件：**
- 修改: `F:\testprogram\better_Skill\skill_optimizer\files.py`
- 修改: `F:\testprogram\better_Skill\tests\test_files.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_files.py` 中追加：

```python
from skill_optimizer.files import should_copy_skill_dir, copy_skill_dir


class SkillDirCopyTests(unittest.TestCase):
    def test_should_copy_skill_dir_returns_true_when_references_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "references").mkdir()
            (workspace / "SKILL.md").write_text("# Skill", encoding="utf-8")

            self.assertTrue(should_copy_skill_dir(workspace))

    def test_should_copy_skill_dir_returns_true_when_examples_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "examples").mkdir()

            self.assertTrue(should_copy_skill_dir(workspace))

    def test_should_copy_skill_dir_returns_false_for_skill_md_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "SKILL.md").write_text("# Skill", encoding="utf-8")

            self.assertFalse(should_copy_skill_dir(workspace))

    def test_should_copy_skill_dir_returns_false_for_empty_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            self.assertFalse(should_copy_skill_dir(workspace))

    def test_copy_skill_dir_copies_all_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            target = Path(temp_dir) / "target"
            (workspace / "references").mkdir(parents=True)
            (workspace / "SKILL.md").write_text("# Skill", encoding="utf-8")
            (workspace / "references" / "helper.py").write_text("def help(): pass", encoding="utf-8")
            (workspace / "references" / "sub" / "deep.txt").mkdir(parents=True)
            (workspace / "references" / "sub" / "deep.txt" / "data.txt").write_text("deep", encoding="utf-8")

            copy_skill_dir(workspace, target)

            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "# Skill")
            self.assertEqual((target / "references" / "helper.py").read_text(encoding="utf-8"), "def help(): pass")
            self.assertEqual(
                (target / "references" / "sub" / "deep.txt" / "data.txt").read_text(encoding="utf-8"),
                "deep",
            )

    def test_copy_skill_dir_excludes_hidden_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            target = Path(temp_dir) / "target"
            (workspace / "references").mkdir(parents=True)
            (workspace / ".gitignore").write_text("*.pyc", encoding="utf-8")
            (workspace / "references" / ".hidden").write_text("secret", encoding="utf-8")
            (workspace / "references" / "visible.py").write_text("ok", encoding="utf-8")

            copy_skill_dir(workspace, target)

            self.assertFalse((target / ".gitignore").exists())
            self.assertFalse((target / "references" / ".hidden").exists())
            self.assertTrue((target / "references" / "visible.py").is_file())

    def test_copy_skill_dir_handles_empty_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            target = Path(temp_dir) / "target"
            workspace.mkdir()

            copy_skill_dir(workspace, target)

            self.assertTrue(target.is_dir())
```

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_files.py -v
```

预期：失败，`ImportError: cannot import name 'should_copy_skill_dir'`

- [ ] **步骤 3: 实现功能**

在 `F:\testprogram\better_Skill\skill_optimizer\files.py` 中追加：

```python
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
```

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_files.py -v
```

预期：全部通过。

- [ ] **步骤 5: 提交**

```bash
git add skill_optimizer/files.py tests/test_files.py
git commit -m "feat: 添加 should_copy_skill_dir 和 copy_skill_dir 函数"
```

---

### Task 2: 在 config.py 中添加 output_dir 字段

**文件：**
- 修改: `F:\testprogram\better_Skill\skill_optimizer\config.py`
- 修改: `F:\testprogram\better_Skill\tests\test_config.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_config.py` 中追加测试用例：

在 `ConfigTests` 类中追加：

```python
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
```

同时更新 `test_default_config_uses_project_root_paths` 中的路径断言：

```python
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
```

同时更新 `test_config_is_constructible_for_tests`：

```python
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
        )

        self.assertEqual(config.score_threshold, 0.9)
        self.assertEqual(config.max_iterations, 3)
        self.assertEqual(config.executor.model, "claude-sonnet-4-6")
        self.assertEqual(config.judge.model, "claude-opus-4-7")
```

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py -v
```

预期：失败，`TypeError: __init__() missing 1 required positional argument: 'output_dir'`

- [ ] **步骤 3: 修改 config.py**

在 `Config` dataclass 中添加 `output_dir` 字段（在 `test_cases_dir` 之后）：

```python
@dataclass(frozen=True)
class Config:
    project_root: Path
    workspace_dir: Path
    skill_path: Path
    test_cases_dir: Path
    output_dir: Path
    runs_dir: Path
    backups_dir: Path
    score_threshold: float
    max_iterations: int
    default_case_timeout_seconds: int
    executor: ModelConfig
    judge: ModelConfig
    reviser: ModelConfig
```

修改 `default_config` 函数，添加 `output_dir` 并更新 `runs_dir`/`backups_dir` 默认值：

```python
def default_config(project_root: Path, overrides: dict[str, Any] | None = None) -> Config:
    """Build a Config from project_root with optional overrides.

    Priority: overrides dict > default derivations from project_root.
    Relative paths in overrides are resolved against project_root.
    """
    overrides = overrides or {}
    workspace_dir = project_root / "workspace"
    output_dir = _path_static(overrides, "output_dir", project_root, project_root / "output")

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
        output_dir=output_dir,
        runs_dir=_path("runs_dir", output_dir / "runs"),
        backups_dir=_path("backups_dir", output_dir / "backups"),
        score_threshold=float(overrides.get("score_threshold", 0.85)),
        max_iterations=int(overrides.get("max_iterations", 5)),
        default_case_timeout_seconds=int(overrides.get("default_case_timeout_seconds", 300)),
        executor=_model("executor", ModelConfig(command="claude", model="sonnet")),
        judge=_model("judge", ModelConfig(command="claude", model="sonnet")),
        reviser=_model("reviser", ModelConfig(command="claude", model="sonnet")),
    )
```

在 `default_config` 之前添加辅助函数：

```python
def _path_static(overrides: dict[str, Any], key: str, project_root: Path, default: Path) -> Path:
    """解析路径覆盖，相对于 project_root。"""
    value = overrides.get(key)
    if value is None:
        return default
    p = Path(value)
    return p if p.is_absolute() else project_root / p
```

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py -v
```

预期：全部通过。

- [ ] **步骤 5: 运行全部测试确认无回归**

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

预期：全部通过。

- [ ] **步骤 6: 提交**

```bash
git add skill_optimizer/config.py tests/test_config.py
git commit -m "feat: 添加 output_dir 配置项，runs/backups 默认移至 output/"
```

---

### Task 3: 在 main.py 中添加 --output-dir CLI 参数

**文件：**
- 修改: `F:\testprogram\better_Skill\main.py`
- 修改: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_main.py` 的 `MainCommandTests` 类中追加：

```python
    def test_parser_accepts_output_dir_override(self):
        parser = build_parser()

        args = parser.parse_args([
            "--output-dir", "/tmp/output",
            "init-case", "case_001",
        ])

        self.assertEqual(args.output_dir, "/tmp/output")

    def test_extract_cli_overrides_includes_output_dir(self):
        from main import _extract_cli_overrides

        parser = build_parser()
        args = parser.parse_args(["--output-dir", "/tmp/output", "init-case", "case_001"])

        overrides = _extract_cli_overrides(args)

        self.assertEqual(overrides["output_dir"], "/tmp/output")
```

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

预期：`test_parser_accepts_output_dir_override` 失败，`args.output_dir` 不存在。

- [ ] **步骤 3: 修改 main.py**

在 `build_parser` 的全局参数中添加 `--output-dir`（在 `--backups-dir` 之后）：

```python
    parser.add_argument("--output-dir", help="Output directory for runs and backups")
```

在 `_extract_cli_overrides` 的 `path_keys` 中添加 `"output_dir"`：

```python
    path_keys = ["skill_path", "workspace_dir", "test_cases_dir", "runs_dir", "backups_dir", "output_dir"]
```

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

预期：全部通过。

- [ ] **步骤 5: 提交**

```bash
git add main.py tests/test_main.py
git commit -m "feat: 添加 --output-dir CLI 参数"
```

---

### Task 4: 更新 _evaluate_cases 执行流程，条件复制 skill 目录

**文件：**
- 修改: `F:\testprogram\better_Skill\main.py`
- 修改: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_main.py` 的 `MainCommandTests` 类中追加：

```python
    def test_run_one_iteration_copies_skill_references_to_case_dir(self):
        """验证带 references/ 的 workspace 会被复制到 case_run_dir。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: ref-skill\ndescription: skill with refs\n---\n\nRead references/data.txt and output its content.",
                encoding="utf-8",
            )
            # 创建 references 目录和文件
            (config.workspace_dir / "references").mkdir()
            (config.workspace_dir / "references" / "data.txt").write_text("ref_content", encoding="utf-8")

            case_dir = create_case_template(config.test_cases_dir, "case_001", "text", 0.1, 30)
            (case_dir / "prompt.txt").write_text("output references/data.txt content", encoding="utf-8")
            (case_dir / "expected.txt").write_text("ref_content", encoding="utf-8")

            # 假 executor：读取 references/data.txt 并输出
            fake_script = (
                "import os; "
                "p = os.path.join(os.getcwd(), 'references', 'data.txt'); "
                "print(open(p).read().strip()) if os.path.exists(p) else print('FILE_NOT_FOUND')"
            )
            fake_executor = ModelConfig(command=sys.executable, model="")
            fake_config = replace(config, executor=fake_executor)

            exit_code = run_optimization(
                fake_config,
                extra_executor_args=["-c", fake_script],
                max_iterations_override=1,
            )

            self.assertEqual(exit_code, 0)
            # 验证 references 文件被复制到了 case_run_dir
            case_run_dir = config.runs_dir / "iter_001" / "case_001"
            self.assertTrue((case_run_dir / "references" / "data.txt").is_file())

    def test_run_one_iteration_does_not_copy_when_no_resource_dirs(self):
        """验证纯 SKILL.md（无 references/ 等）不会触发复制。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: simple\ndescription: simple skill\n---\n\nSay hello.",
                encoding="utf-8",
            )

            case_dir = create_case_template(config.test_cases_dir, "case_001", "text", 0.1, 30)
            (case_dir / "prompt.txt").write_text("say hello", encoding="utf-8")
            (case_dir / "expected.txt").write_text("hello", encoding="utf-8")

            fake_executor = ModelConfig(command=sys.executable, model="")
            fake_config = replace(config, executor=fake_executor)

            exit_code = run_optimization(
                fake_config,
                extra_executor_args=["-c", "print('hello')"],
                max_iterations_override=1,
            )

            self.assertEqual(exit_code, 0)
            # 验证 case_run_dir 中没有 SKILL.md（未复制）
            case_run_dir = config.runs_dir / "iter_001" / "case_001"
            self.assertFalse((case_run_dir / "SKILL.md").exists())
```

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py::MainCommandTests::test_run_one_iteration_copies_skill_references_to_case_dir -v
```

预期：失败，`AssertionError: False is not true`（references/data.txt 未被复制）。

- [ ] **步骤 3: 修改 _evaluate_cases**

在 `F:\testprogram\better_Skill\main.py` 的 `_evaluate_cases` 函数中，修改 import 和执行流程：

将 import 行改为：

```python
    from skill_optimizer.files import compare_expected_files, copy_input_files, copy_skill_dir, should_copy_skill_dir
```

在 `for case in cases:` 循环内，`copy_input_files` 之前添加条件复制：

```python
    for case in cases:
        case_run_dir = iteration_dir / case.name
        if should_copy_skill_dir(config.workspace_dir):
            copy_skill_dir(config.workspace_dir, case_run_dir)
        if case.input_files_dir is not None:
            copy_input_files(case.input_files_dir, case_run_dir)
```

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

预期：全部通过。

- [ ] **步骤 5: 提交**

```bash
git add main.py tests/test_main.py
git commit -m "feat: 条件复制 workspace 到 case_run_dir 支持 reference 文件"
```

---

### Task 5: 更新 skill_optimizer.json.example 和现有测试路径

**文件：**
- 修改: `F:\testprogram\better_Skill\skill_optimizer.json.example`
- 修改: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **步骤 1: 更新 skill_optimizer.json.example**

替换 `F:\testprogram\better_Skill\skill_optimizer.json.example` 内容为：

```json
{
  "skill_path": "./workspace/SKILL.md",
  "test_cases_dir": "./test_cases",
  "workspace_dir": "./workspace",
  "output_dir": "./output",
  "runs_dir": "./output/runs",
  "backups_dir": "./output/backups",
  "default_case_timeout_seconds": 300,
  "executor": {
    "command": "claude",
    "model": "sonnet"
  },
  "judge": {
    "command": "claude",
    "model": "sonnet"
  },
  "reviser": {
    "command": "claude",
    "model": "sonnet"
  }
}
```

- [ ] **步骤 2: 更新 test_main.py 中的路径引用**

在 `F:\testprogram\better_Skill\tests\test_main.py` 中，所有 `config.runs_dir` 和 `config.backups_dir` 的断言不需要修改（因为它们使用 `config` 对象，路径自动跟随）。但需要确保 `build_config` 生成的路径正确。

运行全部测试确认：

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

预期：全部通过。

- [ ] **步骤 3: 更新 .gitignore**

在 `F:\testprogram\better_Skill\.gitignore` 中将 `workspace/runs/` 和 `workspace/backups/` 替换为：

```text
output/
```

- [ ] **步骤 4: 提交**

```bash
git add skill_optimizer.json.example .gitignore
git commit -m "chore: 更新配置示例和 gitignore 适配 output 目录"
```

---

### Task 6: 端到端验证

- [ ] **步骤 1: 运行全部单元测试**

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

预期：全部通过。

- [ ] **步骤 2: 手动验证 init-case**

```bash
python F:/testprogram/better_Skill/main.py init-case case_999 --type mixed
python F:/testprogram/better_Skill/main.py init-case case_999 --type mixed
```

预期：第一次创建用例；第二次拒绝覆盖。

- [ ] **步骤 3: 手动验证 --output-dir**

```bash
python F:/testprogram/better_Skill/main.py --output-dir ./my_output init-case case_998 --type text
```

预期：用例创建在 `./test_cases/case_998/`。

- [ ] **步骤 4: 清理测试产物**

```bash
rm -rf F:/testprogram/better_Skill/test_cases F:/testprogram/better_Skill/output F:/testprogram/better_Skill/my_output
```

---

## 自查

- **占位符扫描**：无 TBD/TODO，每步都有完整代码。
- **类型一致性**：`Config.output_dir`、`should_copy_skill_dir`、`copy_skill_dir` 在所有任务中签名一致。
- **架构一致性**：output_dir 贯穿 config → CLI → json.example，复制逻辑在 _evaluate_cases 中统一处理。
- **向后兼容**：纯 SKILL.md skill 不受影响（should_copy 返回 False），已有 CLI 参数保留。
- **边界处理**：隐藏文件排除、空目录处理、input_files 后复制覆盖 workspace 同名文件。
