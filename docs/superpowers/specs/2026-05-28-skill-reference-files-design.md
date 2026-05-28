# Skill Reference Files Support Design

**Date:** 2026-05-28
**Status:** Approved

## Problem

Current test runner (`runner.py`) only sends SKILL.md content as system prompt. When a skill includes `references/`, `examples/`, `scripts/` etc., the AI cannot access them because:

1. SKILL.md is injected as system prompt text, not as a file on disk
2. cwd is `case_run_dir`, not the skill directory — relative paths like `references/helper.py` don't resolve
3. `--disable-slash-commands` prevents skill invocation

Real Claude Code behavior: SKILL.md loaded on trigger, references/examples loaded **on demand** via Read tool. The test system needs to simulate this.

## Solution

Copy the workspace (skill directory) to `case_run_dir` before executor runs, so the AI can use Read tool to access reference files — matching real Claude Code behavior.

## Directory Structure Change

**Before:**
```
workspace/
├── SKILL.md
├── references/
├── runs/          ← mixed with skill files
└── backups/       ← mixed with skill files
```

**After:**
```
workspace/              ← pure skill directory, copyable as-is
├── SKILL.md
├── references/
├── examples/
└── scripts/

output/                 ← runtime artifacts, separate
├── runs/
│   └── iter_001/
└── backups/
```

## Code Changes

### 1. `files.py` — Add `copy_skill_dir()` and `should_copy_skill_dir()`

```python
SKILL_RESOURCE_DIRS = {"references", "examples", "scripts", "assets"}

def should_copy_skill_dir(workspace_dir: Path) -> bool:
    """Check if workspace has skill resource directories beyond SKILL.md."""
    return any((workspace_dir / d).is_dir() for d in SKILL_RESOURCE_DIRS)

def copy_skill_dir(workspace_dir: Path, target_dir: Path) -> None:
    """Copy workspace skill resources to target_dir, excluding hidden files."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for src in workspace_dir.rglob("*"):
        if src.is_file():
            # Skip hidden files/dirs
            parts = src.relative_to(workspace_dir).parts
            if any(p.startswith(".") for p in parts):
                continue
            rel = src.relative_to(workspace_dir)
            dst = target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
```

### 2. `config.py` — Add `output_dir`

- New field: `output_dir: Path` (default: `project_root / "output"`)
- `runs_dir` default changes to `output_dir / "runs"`
- `backups_dir` default changes to `output_dir / "backups"`
- Existing `--runs-dir` and `--backups-dir` CLI overrides still work

### 3. `main.py` — Update `_evaluate_cases()` execution flow

```
for each case:
    1. if should_copy_skill_dir(workspace_dir):
           copy_skill_dir(workspace_dir → case_run_dir)
    2. copy_input_files(input_files_dir → case_run_dir)    [existing]
    3. read SKILL.md content as system prompt               [existing]
    4. execute claude -p (cwd=case_run_dir, tools=True)     [existing]
```

### 4. CLI — Add `--output-dir` global argument

```
python main.py --output-dir ./my_output
```

## Execution Effect

For a skill with references, AI sees in case_run_dir:
```
case_run_dir/
├── SKILL.md           ← from workspace copy
├── references/
│   ├── helper.py      ← AI reads via Read tool
│   └── config.yaml
├── source.py          ← from input_files copy
└── ...
```

SKILL.md says "read references/helper.py" → AI uses Read tool → file is in cwd → success.

For a pure SKILL.md skill (no resource dirs) → no copy, zero overhead, backward compatible.

## Edge Cases

- `workspace/` doesn't exist → error (same as current)
- `workspace/` has only SKILL.md → no copy, current behavior preserved
- `output/` doesn't exist → created on first run
- Hidden files (`.git`, `.DS_Store`) → excluded from copy
- `input_files/` content overwrites workspace copy if same filename → input_files wins (copy happens after)

## Testing

- Unit test: `should_copy_skill_dir()` returns True/False correctly
- Unit test: `copy_skill_dir()` copies files excluding hidden ones
- Integration test: executor can Read reference files from case_run_dir
- Existing tests: update paths for `output_dir` change

## Files to Modify

| File | Change |
|------|--------|
| `skill_optimizer/files.py` | Add `should_copy_skill_dir()`, `copy_skill_dir()` |
| `skill_optimizer/config.py` | Add `output_dir`, update defaults |
| `main.py` | Add `--output-dir` arg, update `_evaluate_cases()` flow |
| `skill_optimizer.json.example` | Add `output_dir` field |
| `tests/test_files.py` | Add tests for new functions |
| `tests/test_config.py` | Update for `output_dir` |
| `tests/test_main.py` | Update for new path structure |
