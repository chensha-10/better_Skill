# 使用 skill-creator 优化 SKILL.md 设计

**Date:** 2026-05-28
**Status:** Approved

## Problem

当前修订逻辑（`optimizer.py` 的 `build_revision_prompt`）太简单：
- 只传失败摘要（`"case_001: score=0.50 (threshold=0.85)"`）
- AI 不知道实际输出了什么，不知道期望是什么
- 无法分析失败原因，只能盲改

skill-creator 有一套完整的方法论：分析输出、找模式、解释 why、基于反馈改进。

## Solution

将 skill-creator 的 SKILL.md 注入为 reviser 的 system prompt，同时传入 expected vs actual 对比信息，让 reviser 按 skill-creator 的方法论工作。

## 改动

### 1. `config.py` — 新增 `skill_creator_path`

```python
@dataclass(frozen=True)
class Config:
    ...
    skill_creator_path: Path | None  # skill-creator SKILL.md 路径
```

默认值：`None`（不使用 skill-creator，保持当前行为）
配置方式：`skill_optimizer.json` 中 `"skill_creator_path": "~/.claude/plugins/.../SKILL.md"`

### 2. `optimizer.py` — 改进 `build_revision_prompt`

接收 failure_analysis（包含 expected/actual 对比）而非简单字符串：

```python
def build_revision_prompt(
    skill_content: str,
    failure_analysis: str,
    skill_path: str = "workspace/SKILL.md",
) -> str:
    return (
        "You are a prompt engineer improving a Claude SKILL.md file...\n\n"
        "<current_skill>\n{skill_content}\n</current_skill>\n\n"
        "<failure_analysis>\n{failure_analysis}\n</failure_analysis>\n\n"
        "For each failure:\n"
        "1. Compare expected vs actual output\n"
        "2. Identify what the SKILL instructions caused the executor to do wrong\n"
        "3. Explain WHY the current SKILL leads to this output\n"
        "4. Revise the SKILL to fix the root cause\n"
    )
```

### 3. `main.py` — 收集 actual output，构建对比分析

`_evaluate_cases` 返回更丰富的失败信息：

```python
failure_details.append({
    "case": case.name,
    "score": score,
    "threshold": case.min_score,
    "expected": expected_text,
    "actual": result.stdout.strip(),
})
```

`_build_failure_analysis` 构建对比分析：

```python
def _build_failure_analysis(failures):
    parts = []
    for f in failures:
        parts.append(f"## {f['case']} (score={f['score']:.2f}, threshold={f['threshold']})")
        parts.append(f"### Expected:\n{f['expected']}")
        parts.append(f"### Actual:\n{f['actual']}")
    return "\n\n".join(parts)
```

### 4. `main.py` — `_apply_revision` 注入 skill-creator

```python
def _apply_revision(config, skill_content, failure_analysis, revision_dir, reviser_args):
    system_prompt = None
    if config.skill_creator_path and config.skill_creator_path.is_file():
        system_prompt = config.skill_creator_path.read_text(encoding="utf-8")

    revision_result = run_claude_prompt(
        config.reviser,
        build_revision_prompt(skill_content, failure_analysis),
        revision_dir,
        config.default_case_timeout_seconds,
        extra_args=reviser_args, allow_tools=False,
        cwd_override=config.project_root,
        system_prompt=system_prompt,  # skill-creator SKILL.md 作为 system prompt
    )
```

### 5. `runner.py` — reviser 移除 `--disable-slash-commands`

当 `system_prompt` 存在时（即使用 skill-creator），不添加 `--disable-slash-commands`，允许 skill 触发。

## 配置示例

```json
{
  "skill_creator_path": "C:/Users/admin/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md"
}
```

## 验证

```bash
python -m unittest discover -s tests -v
```
