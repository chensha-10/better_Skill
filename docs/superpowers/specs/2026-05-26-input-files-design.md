# 输入文件支持 (input_files) 设计文档

## 背景

SKILL 优化器当前支持三种用例类型：`text`（文本比对）、`files`（文件比对）、`mixed`（混合比对）。但现有的 `files` 类型只能验证 executor **从零创建**的文件 — executor 在空的工作目录中运行，创建输出文件后与 `expected_files/` 比对。

实际场景中，很多 skill 需要**修改已有文件**（如编辑代码、更新配置）。当前框架缺少为 executor 提供初始文件的能力。

## 目标

为所有用例类型增加可选的 `input_files/` 目录支持，使 executor 能够在已有文件基础上进行修改，验证修改后的文件内容是否正确。

## 设计决策

选择**方案 A：扩展现有用例类型**（而非新增 `modify` 类型）。

理由：
- 改动最小，完全向后兼容
- `input_files/` 是可选数据源，不增加概念复杂度
- 与所有现有用例类型（text/files/mixed）自然组合

## 目录结构

```
test_cases/case_001/
├── prompt.txt          # 测试 prompt
├── expected.txt        # 期望文本输出（text/mixed 类型）
├── expected_files/     # 期望文件（files/mixed 类型）
├── input_files/        # [NEW] 可选：执行前复制到工作目录的初始文件
└── metadata.json       # 用例元数据
```

## 数据模型

`TestCase` 增加一个字段：

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

加载时自动检测 `case_dir / "input_files"` 目录是否存在。

## 执行流程

对每个用例，在 executor 运行前增加复制步骤：

1. 创建 `case_run_dir`
2. **若 `input_files_dir` 存在，递归复制其内容到 `case_run_dir`**
3. 构建 execution prompt
4. `run_claude_prompt(cwd=case_run_dir)` — executor 在已有文件上工作
5. 比对 stdout 与 expected.txt（现有逻辑不变）
6. 比对 case_run_dir 产物与 expected_files/（现有逻辑不变）

## 新增函数

`skill_optimizer/files.py`：

```python
def copy_input_files(input_dir: Path, target_dir: Path) -> None:
    """将 input_dir 下所有文件递归复制到 target_dir"""
```

使用 `shutil.copy2` 保留文件元数据，自动创建目标父目录。

## CLI 变更

`init-case` 子命令增加 `--with-input-files` 参数：

```bash
python main.py init-case case_004 --type files --with-input-files
```

设置为 `True` 时在用例目录下创建空的 `input_files/` 目录。默认 `False`，向后兼容。

## 配置文件

无需变更。`input_files/` 是纯用例级别的概念，由目录存在与否自动探测。

## 改动文件清单

| 文件 | 改动 |
|------|------|
| `skill_optimizer/cases.py` | `TestCase` 加字段、`load_cases` 检测、`create_case_template` 支持新参数 |
| `skill_optimizer/files.py` | 新增 `copy_input_files` 函数 |
| `main.py` | `_evaluate_cases` 执行前复制输入文件、`init-case` 加 `--with-input-files` |
| `tests/test_cases.py` | 新用例加载和创建测试 |
| `tests/test_files.py` | `copy_input_files` 单元测试 |
| `README.md` | 文档补充 |
