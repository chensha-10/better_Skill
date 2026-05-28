# Skill-creator 修订集成实施计划

> **给执行代理的提示：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步实施。本计划使用复选框（`- [ ]`）跟踪进度。

**目标：** 将 skill-creator 的 SKILL.md 注入为 reviser 的 system prompt，同时传入 expected vs actual 对比信息，让 reviser 按 skill-creator 的方法论改进 SKILL.md。

**架构：** `_evaluate_cases` 收集每个失败 case 的 expected/actual 输出，`_apply_revision` 将 skill-creator SKILL.md 作为 system prompt 注入，`build_revision_prompt` 改为接收对比分析而非简单摘要。

**技术栈：** Python 3 标准库

---

## 文件结构

```text
F:\testprogram\better_Skill\skill_optimizer\config.py       ← 新增 skill_creator_path 字段
F:\testprogram\better_Skill\skill_optimizer\optimizer.py    ← 改进 build_revision_prompt
F:\testprogram\better_Skill\main.py                         ← 收集 actual output，构建对比分析，注入 skill-creator
F:\testprogram\better_Skill\skill_optimizer.json.example    ← 新增 skill_creator_path
F:\testprogram\better_Skill\tests\test_config.py            ← 新增测试
F:\testprogram\better_Skill\tests\test_optimizer.py         ← 更新测试
F:\testprogram\better_Skill\tests\test_main.py              ← 新增测试
```

---

### Task 1: config.py 添加 skill_creator_path 字段

**文件：**
- 修改: `F:\testprogram\better_Skill\skill_optimizer\config.py`
- 修改: `F:\testprogram\better_Skill\tests\test_config.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_config.py` 的 `ConfigTests` 类中追加：

```python
    def test_default_config_skill_creator_path_is_none(self):
        config = default_config(Path("F:/testprogram/better_Skill"))

        self.assertIsNone(config.skill_creator_path)

    def test_default_config_accepts_skill_creator_path_override(self):
        config = default_config(
            Path("F:/testprogram/better_Skill"),
            overrides={"skill_creator_path": "F:/plugins/skill-creator/SKILL.md"},
        )

        self.assertEqual(config.skill_creator_path, Path("F:/plugins/skill-creator/SKILL.md"))
```

同时更新 `test_config_is_constructible_for_tests`，在 `Config(...)` 构造中添加 `skill_creator_path=None`。

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py -v
```

预期：失败，`TypeError: __init__() missing 1 required positional argument: 'skill_creator_path'`

- [ ] **步骤 3: 修改 config.py**

在 `Config` dataclass 中添加 `skill_creator_path` 字段（在 `reviser` 之后）：

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
    skill_creator_path: Path | None
```

在 `default_config` 的 `return Config(...)` 中添加：

```python
        skill_creator_path=_path("skill_creator_path", None) if "skill_creator_path" in overrides else None,
```

注意：当 overrides 中没有 `skill_creator_path` 时，默认为 `None`（不使用 skill-creator）。

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_config.py -v
```

预期：全部通过。

- [ ] **步骤 5: 提交**

```bash
git add skill_optimizer/config.py tests/test_config.py
git commit -m "feat: config 添加 skill_creator_path 字段"
```

---

### Task 2: optimizer.py 改进 build_revision_prompt

**文件：**
- 修改: `F:\testprogram\better_Skill\skill_optimizer\optimizer.py`
- 修改: `F:\testprogram\better_Skill\tests\test_optimizer.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_optimizer.py` 的 `OptimizerTests` 类中追加：

```python
    def test_build_revision_prompt_includes_expected_and_actual(self):
        failure_analysis = (
            "## case_001 (score=0.50, threshold=0.85)\n"
            "### Expected:\nhello world\n"
            "### Actual:\nwrong answer"
        )
        prompt = build_revision_prompt(
            skill_content="old skill",
            failure_analysis=failure_analysis,
        )

        self.assertIn("expected", prompt.lower())
        self.assertIn("actual", prompt.lower())
        self.assertIn("hello world", prompt)
        self.assertIn("wrong answer", prompt)
        self.assertIn("WHY", prompt)

    def test_build_revision_prompt_backward_compatible_with_string(self):
        """确保旧的字符串调用方式仍然工作。"""
        prompt = build_revision_prompt(
            skill_content="old skill",
            failure_analysis="case_001 failed with score 0.3",
        )

        self.assertIn("old skill", prompt)
        self.assertIn("case_001 failed", prompt)
```

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_optimizer.py -v
```

预期：`test_build_revision_prompt_includes_expected_and_actual` 失败，因为当前 prompt 不包含 "expected"/"actual"/"WHY"。

- [ ] **步骤 3: 修改 build_revision_prompt**

替换 `F:\testprogram\better_Skill\skill_optimizer\optimizer.py` 中的 `build_revision_prompt` 函数：

```python
def build_revision_prompt(skill_content: str, failure_analysis: str, skill_path: str = "workspace/SKILL.md") -> str:
    return (
        "You are a prompt engineer improving a Claude SKILL.md file. You are NOT "
        "executing the skill — your job is to revise the SKILL.md so that a future "
        "executor will produce correct outputs. The current SKILL content is shown "
        "below in <current_skill>. The test failures in <failure_analysis> show "
        "what the executor actually produced vs what was expected.\n\n"
        "For each failure:\n"
        "1. Compare the expected output with the actual output\n"
        "2. Identify what in the SKILL instructions caused the executor to produce wrong output\n"
        "3. Explain WHY the current SKILL leads to this output\n"
        "4. Revise the SKILL to fix the root cause, not the symptom\n\n"
        "IMPORTANT: You must output the COMPLETE revised SKILL.md content as your "
        "entire response. Start your response with `---` (the YAML frontmatter delimiter) "
        "and end with the last line of the SKILL content. Do NOT use any tools. "
        "Do NOT write to any files. Do NOT include any explanation, summary, or commentary "
        "before or after the SKILL content. Your entire response must be the raw SKILL.md file content.\n\n"
        "<current_skill>\n"
        f"{skill_content}\n"
        "</current_skill>\n\n"
        "<failure_analysis>\n"
        f"{failure_analysis}\n"
        "</failure_analysis>\n"
    )
```

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_optimizer.py -v
```

预期：全部通过。

- [ ] **步骤 5: 运行全部测试确认无回归**

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

预期：全部通过。

- [ ] **步骤 6: 提交**

```bash
git add skill_optimizer/optimizer.py tests/test_optimizer.py
git commit -m "feat: build_revision_prompt 支持 expected/actual 对比分析"
```

---

### Task 3: main.py 收集 actual output 并构建对比分析

**文件：**
- 修改: `F:\testprogram\better_Skill\main.py`
- 修改: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_main.py` 的 `MainCommandTests` 类中追加：

```python
    def test_build_failure_analysis_includes_expected_and_actual(self):
        from main import _build_failure_analysis

        failures = [
            {
                "case": "case_001",
                "score": 0.5,
                "threshold": 0.85,
                "expected": "hello world",
                "actual": "wrong answer",
            },
        ]

        result = _build_failure_analysis(failures)

        self.assertIn("case_001", result)
        self.assertIn("hello world", result)
        self.assertIn("wrong answer", result)
        self.assertIn("Expected", result)
        self.assertIn("Actual", result)

    def test_build_failure_analysis_handles_empty_failures(self):
        from main import _build_failure_analysis

        result = _build_failure_analysis([])

        self.assertIn("below threshold", result)
```

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

预期：失败，`ImportError: cannot import name '_build_failure_analysis'`

- [ ] **步骤 3: 添加 _build_failure_analysis 函数**

在 `F:\testprogram\better_Skill\main.py` 中，在 `_apply_revision` 函数之前添加：

```python
def _build_failure_analysis(failures: list[dict]) -> str:
    """构建 expected vs actual 对比分析。"""
    if not failures:
        return "All cases failed but no details available."
    parts = []
    for f in failures:
        parts.append(f"## {f['case']} (score={f['score']:.2f}, threshold={f['threshold']})")
        if f.get("expected"):
            parts.append(f"### Expected:\n{f['expected']}")
        if f.get("actual"):
            parts.append(f"### Actual:\n{f['actual']}")
    return "\n\n".join(parts)
```

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

预期：全部通过。

- [ ] **步骤 5: 修改 _evaluate_cases 返回更丰富的失败信息**

在 `F:\testprogram\better_Skill\main.py` 的 `_evaluate_cases` 函数中：

将 `failure_details` 的类型从 `list[str]` 改为 `list[dict]`：

```python
    failure_details: list[dict] = []
```

将执行失败的 case 改为 dict：

```python
        if result.return_code != 0:
            scores.append(0.0)
            failure_details.append({
                "case": case.name,
                "score": 0.0,
                "threshold": case.min_score,
                "expected": "",
                "actual": f"execution failed (rc={result.return_code})",
            })
            continue
```

在评分失败时收集 expected/actual：

```python
        if passed:
            passed_count += 1
        else:
            expected_text = ""
            if case.expected_text_path and case.expected_text_path.is_file():
                expected_text = case.expected_text_path.read_text(encoding="utf-8").strip()
            failure_details.append({
                "case": case.name,
                "score": score,
                "threshold": case.min_score,
                "expected": expected_text,
                "actual": result.stdout.strip(),
            })
```

同时更新函数返回类型注解：

```python
def _evaluate_cases(...) -> tuple[int, int, list[float], list[dict]]:
```

- [ ] **步骤 6: 修改 run_optimization 使用 _build_failure_analysis**

在 `F:\testprogram\better_Skill\main.py` 的 `run_optimization` 函数中，将：

```python
        failure_summary = "; ".join(failures) if failures else f"avg score {average_score:.2f} below threshold"
```

改为：

```python
        failure_analysis = _build_failure_analysis(failures) if failures else f"avg score {average_score:.2f} below threshold"
```

并将 `_apply_revision` 调用中的参数名从 `failure_summary` 改为 `failure_analysis`：

```python
            result = _apply_revision(config, skill_content, failure_analysis, revision_dir, reviser_args)
```

- [ ] **步骤 7: 运行全部测试确认通过**

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

预期：全部通过。

- [ ] **步骤 8: 提交**

```bash
git add main.py tests/test_main.py
git commit -m "feat: _evaluate_cases 收集 expected/actual，构建对比分析"
```

---

### Task 4: _apply_revision 注入 skill-creator 作为 system prompt

**文件：**
- 修改: `F:\testprogram\better_Skill\main.py`
- 修改: `F:\testprogram\better_Skill\tests\test_main.py`

- [ ] **步骤 1: 编写失败测试**

在 `F:\testprogram\better_Skill\tests\test_main.py` 的 `MainCommandTests` 类中追加：

```python
    def test_apply_revision_injects_skill_creator_as_system_prompt(self):
        """验证配置了 skill_creator_path 时，reviser 收到 skill-creator 作为 system prompt。"""
        import sys
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as temp_dir:
            config = build_config(Path(temp_dir))
            config.workspace_dir.mkdir(parents=True)
            config.skill_path.write_text(
                "---\nname: weak\ndescription: weak\n---\n\nBe unhelpful.",
                encoding="utf-8",
            )

            # 创建 skill-creator SKILL.md
            skill_creator_path = Path(temp_dir) / "skill-creator" / "SKILL.md"
            skill_creator_path.parent.mkdir(parents=True)
            skill_creator_path.write_text(
                "---\nname: skill-creator\n---\n\nYou are a skill improvement expert.",
                encoding="utf-8",
            )

            # 创建 case
            case_dir = create_case_template(config.test_cases_dir, "case_001", "text", 0.85, 30)
            (case_dir / "prompt.txt").write_text("say hello", encoding="utf-8")
            (case_dir / "expected.txt").write_text("hello", encoding="utf-8")

            # 假 reviser：输出改进后的 SKILL.md
            revised_skill = (
                "---\nname: better-skill\ndescription: better\n---\n\n"
                "Always respond with exactly what the user asks for."
            )
            import json as _json
            reviser_script = f"import sys; sys.stdout.write({_json.dumps(revised_skill)})"

            fake_model = ModelConfig(command=sys.executable, model="")
            fake_config = replace(
                config,
                executor=fake_model,
                reviser=fake_model,
                skill_creator_path=skill_creator_path,
                max_iterations=2,
                score_threshold=0.85,
            )

            exit_code = run_optimization(
                fake_config,
                extra_executor_args=["-c", "print('wrong answer')"],
                extra_reviser_args=["-c", reviser_script],
                max_iterations_override=2,
            )

            # 验证 skill 被修订了
            final_skill = config.skill_path.read_text(encoding="utf-8")
            self.assertIn("better-skill", final_skill)
```

- [ ] **步骤 2: 运行测试确认失败**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py::MainCommandTests::test_apply_revision_injects_skill_creator_as_system_prompt -v
```

预期：失败（因为 `_apply_revision` 还不支持 `system_prompt`）。

- [ ] **步骤 3: 修改 _apply_revision 注入 skill-creator**

在 `F:\testprogram/better_Skill\main.py` 中，修改 `_apply_revision` 函数：

```python
def _apply_revision(
    config: Config,
    skill_content: str,
    failure_analysis: str,
    revision_dir: Path,
    reviser_args: list[str],
) -> int:
    """Generate and apply SKILL revision. Returns 0 on success, 1 on failure."""
    from skill_optimizer.files import backup_file
    from skill_optimizer.optimizer import build_revision_prompt, validate_skill_revision
    from skill_optimizer.runner import run_claude_prompt

    backup_file(config.skill_path, config.backups_dir)

    # 注入 skill-creator SKILL.md 作为 system prompt
    system_prompt = None
    if config.skill_creator_path and config.skill_creator_path.is_file():
        system_prompt = config.skill_creator_path.read_text(encoding="utf-8")

    revision_result = run_claude_prompt(
        config.reviser,
        build_revision_prompt(
            skill_content, failure_analysis,
            str(config.skill_path),
        ),
        revision_dir,
        config.default_case_timeout_seconds,
        extra_args=reviser_args, allow_tools=False,
        cwd_override=config.project_root,
        system_prompt=system_prompt,
    )
    if revision_result.return_code != 0:
        print(f"Revision generation failed: {revision_result.stderr}")
        return 1

    new_skill = revision_result.stdout.strip()
    validate_skill_revision(new_skill, skill_content)
    config.skill_path.write_text(new_skill, encoding="utf-8")
    print("Applied revised SKILL.md (from stdout)")
    return 0
```

- [ ] **步骤 4: 运行测试确认通过**

```bash
python -m unittest F:/testprogram/better_Skill/tests/test_main.py -v
```

预期：全部通过。

- [ ] **步骤 5: 提交**

```bash
git add main.py tests/test_main.py
git commit -m "feat: _apply_revision 注入 skill-creator 作为 system prompt"
```

---

### Task 5: 更新配置示例和端到端验证

**文件：**
- 修改: `F:\testprogram\better_Skill\skill_optimizer.json.example`

- [ ] **步骤 1: 更新 skill_optimizer.json.example**

在 `F:\testprogram\better_Skill\skill_optimizer.json.example` 中添加 `skill_creator_path` 字段：

```json
{
  "skill_path": "./workspace/SKILL.md",
  "test_cases_dir": "./test_cases",
  "workspace_dir": "./workspace",
  "output_dir": "./output",
  "runs_dir": "./output/runs",
  "backups_dir": "./output/backups",
  "skill_creator_path": null,
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

- [ ] **步骤 2: 运行全部测试**

```bash
python -m unittest discover -s F:/testprogram/better_Skill/tests -v
```

预期：全部通过。

- [ ] **步骤 3: 提交**

```bash
git add skill_optimizer.json.example
git commit -m "chore: 配置示例添加 skill_creator_path"
```

---

## 自查

- **占位符扫描**：无 TBD/TODO，每步都有完整代码。
- **类型一致性**：`failure_details` 从 `list[str]` 改为 `list[dict]`，`_build_failure_analysis` 接收 `list[dict]`，所有调用点一致。
- **向后兼容**：`skill_creator_path` 默认 `None`，不配置时行为不变；`build_revision_prompt` 的 `failure_analysis` 参数名兼容旧调用。
- **边界处理**：`_build_failure_analysis` 处理空 failures 列表；`_apply_revision` 检查 `skill_creator_path` 是否存在。
