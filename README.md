# SKILL 优化器

用测试用例驱动的方式，自动迭代优化 Claude Code 的 `SKILL.md` 文件。

## 工作原理

```
┌─────────────┐     ┌───────────┐     ┌───────────┐
│  Executor   │ ──▶ │   Judge   │ ──▶ │  Reviser  │
│ 执行 SKILL  │     │ 评分结果  │     │ 修订 SKILL│
└─────────────┘     └───────────┘     └───────────┘
       │                   │                  │
       │         全部通过？ ◀── 是 ── 结束     │
       │              │ 否                    │
       │              └──────────────────────┘
       │                    迭代直到通过
       └── 使用修订后的 SKILL 重新执行 ──┘
```

三个角色各自使用独立的 Claude 模型，互不干扰：
- **Executor（执行者）**：SKILL 内容通过 `--system-prompt` 传入，用户 prompt 通过 stdin 传入，执行后产出文件
- **Judge（裁判）**：对比实际输出与期望输出，给出 0-1 分数（文本用 AI 评分，文件用 difflib + AI 混合评分）
- **Reviser（修订者）**：根据失败原因改进 SKILL.md。支持注入 [skill-creator](https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev) 的方法论作为 system prompt，通过 expected/actual 对比分析找到根因

## 项目结构

```
skill_optimizer/          核心模块
├── config.py             ModelConfig / Config 数据类，三层配置合并
├── cases.py              测试用例模板创建与加载
├── files.py              文件备份、目录创建、文件相似度评分（difflib）
├── runner.py             Claude CLI 调用（cwd 隔离、超时处理）
├── judge.py              评分解析（JSON 容错、difflib 捷径、文件 AI 评分）
├── optimizer.py          SKILL 修订校验、备份、expected/actual 对比 prompt 构建
main.py                   CLI 入口
tests/                    单元测试（85 个）
workspace/SKILL.md        示例 SKILL
test_cases/case_001/      示例用例
```

## 前置条件

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 已安装并可用（`claude --version` 可正常执行）

## 快速开始

### 1. 创建配置文件

复制示例配置并按需修改：

```bash
cp skill_optimizer.json.example skill_optimizer.json
```

配置文件中 `model` 字段使用 Claude CLI 支持的模型别名（如 `sonnet`、`opus`、`haiku`），而非完整模型 ID。详见[配置文件](#配置文件)章节。

### 2. 创建测试用例

```bash
# 纯文本比对（期望输出是文本）
python main.py init-case case_001 --type text

# 文件比对（期望输出是文件）
python main.py init-case case_002 --type files

# 混合比对（同时检查文本和文件）
python main.py init-case case_003 --type mixed
```

每个用例目录包含：

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

如果用例需要多轮追问，可以再放一个 `dialogue.json`：

```json
{
  "turns": [
    {
      "user": "Under $50"
    },
    {
      "user": "更偏实用"
    },
    {
      "user": "给办公场景用"
    }
  ]
}
```

这里不校验模型中间提问的原文，只脚本化后续的 `user` 回复。`turns` 写几条，就预留几轮追问。最后一轮仍然使用 `expected.txt` / `expected_files/` 做最终判定。

### 3. 编辑用例内容

编辑 `prompt.txt` 和 `expected.txt` 填入实际的测试内容：

**prompt.txt:**
```
Respond with exactly: hello skill
```

**expected.txt:**
```
hello skill
```

### 4. 准备待优化的 SKILL

编辑 `workspace/SKILL.md`，这是将被优化器反复修订的文件：

```markdown
---
name: sample-answer-skill
description: Answers simple test prompts
---

# Sample Answer Skill

When given a test prompt, answer directly.
```

**支持 reference 文件**：如果 SKILL 依赖 `references/`、`examples/`、`scripts/` 等子目录，将它们放在 `workspace/` 下即可。优化器会自动将整个 workspace 复制到执行目录，AI 可以用 Read 工具按需读取：

```
workspace/
├── SKILL.md
├── references/
│   ├── helper.py
│   └── config.yaml
└── examples/
    └── example.py
```

### 5. 运行优化

```bash
python main.py
```

优化器会：
1. 用 executor 模型执行每个用例
2. 用 judge 模型对结果评分
3. 如果全部通过 → 结束
4. 如果未通过 → 用 reviser 模型修订 SKILL.md → 回到步骤 1
5. 到达最大迭代次数仍未通过 → 退出并报告

每次迭代的结果保存在 `output/runs/iter_001/` 目录下。

## CLI 参数

```
python main.py [全局参数] [子命令] [子命令参数]
```

### 全局参数（适用于所有子命令）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--project-root` | 项目根目录，所有相对路径都基于此解析 | 脚本所在目录 |
| `--config` | 配置文件路径（JSON 格式） | `./skill_optimizer.json` |
| `--skill-path` | 待优化的 SKILL.md 文件路径 | `./workspace/SKILL.md` |
| `--test-cases-dir` | 测试用例目录 | `./test_cases` |
| `--workspace-dir` | 工作区目录（SKILL.md 所在目录） | `./workspace` |
| `--runs-dir` | 运行产物输出目录 | `./output/runs` |
| `--backups-dir` | SKILL.md 备份目录 | `./output/backups` |
| `--output-dir` | 输出根目录（runs 和 backups 的父目录） | `./output` |

**参数详解：**

- **`--project-root`**：设置项目根目录，所有相对路径（配置文件、SKILL 路径、用例目录等）都基于此目录解析。适用于在非项目根目录执行脚本的场景。
- **`--config`**：指定配置文件路径。用于维护多套配置（如不同模型组合、不同阈值），快速切换实验方案。
- **`--skill-path`**：指定待优化的 SKILL.md 文件位置。适用于 SKILL 文件不在默认 `workspace/` 目录的情况。
- **`--test-cases-dir`**：指定测试用例目录。可用于切换不同用例集进行对比实验。
- **`--workspace-dir`**：executor 执行时的工作区目录。SKILL 引用的文件应放在此目录下。
- **`--runs-dir`**：运行产物（stdout、stderr、评分结果等）的输出目录。
- **`--backups-dir`**：每次修订 SKILL.md 前的自动备份目录，文件名含时间戳便于回溯。
- **`--output-dir`**：输出根目录，`runs-dir` 和 `backups-dir` 默认在其下创建。用于将所有输出集中到一个目录，方便清理和管理。

### init-case 子命令

```bash
python main.py init-case <用例名> [--type text|files|mixed] [--min-score 0.85] [--timeout 300]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `case_name` | 用例名称（同时作为目录名） | 必填 |
| `--type` | 用例类型：`text`（文本比对）、`files`（文件比对）、`mixed`（混合比对） | `mixed` |
| `--min-score` | 通过的最低分数（0.0 ~ 1.0） | `0.85` |
| `--timeout` | 单次执行超时时间（秒） | `300` |
| `--with-input-files` | 创建 `input_files/` 目录，用于放置执行前复制到工作区的初始文件 | `False` |

**参数详解：**

- **`case_name`**：用例的唯一标识，同时也是 `test_cases/` 下的子目录名。建议使用描述性名称，如 `refactor-loop-to-comprehension`。
- **`--type`**：决定评分方式。`text` 仅比对 stdout 输出；`files` 仅比对生成的文件；`mixed` 两者都检查。
- **`--min-score`**：单个用例的通过阈值。分数 >= 此值视为通过。可针对不同用例设置不同难度。
- **`--timeout`**：executor 单次执行的超时时间。复杂任务（如生成多文件）建议增大到 600 秒。
- **`--with-input-files`**：启用后会创建 `input_files/` 目录。适用于需要提供初始代码/文件让 executor 基于其工作的场景。

### 配置优先级

```
CLI 参数 > 配置文件 (skill_optimizer.json) > 内置默认值
```

CLI 参数始终最高优先级，适合临时覆盖；配置文件适合持久化实验设置；未指定时使用内置默认值。

## 配置文件

复制 `skill_optimizer.json.example` 为 `skill_optimizer.json` 进行自定义配置：

```json
{
  "skill_path": "./workspace/SKILL.md",
  "test_cases_dir": "./test_cases",
  "workspace_dir": "./workspace",
  "output_dir": "./output",
  "runs_dir": "./output/runs",
  "backups_dir": "./output/backups",
  "skill_creator_path": null,
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
  },
  "score_threshold": 0.85,
  "max_iterations": 5,
  "default_case_timeout_seconds": 300
}
```

### Skill-Creator 集成

配置 `skill_creator_path` 后，reviser 会收到 [skill-creator](https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev) 的完整方法论作为 system prompt。skill-creator 的核心理念：

- **对比分析**：不只看分数，而是对比 expected vs actual 输出，找到 SKILL 指令导致的根因
- **解释 WHY**：不是盲目修改，而是分析为什么当前 SKILL 会导致错误输出
- **泛化改进**：从具体失败中提炼通用改进，避免过拟合到测试用例

配置方式：

```json
{
  "skill_creator_path": "C:/Users/admin/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md"
}
```

不配置（`null`）时使用内置的修订 prompt，行为不变。

### 模型配置

`model` 字段使用 Claude CLI 支持的模型别名，**不要**使用完整模型 ID：

| 别名 | 对应模型 |
|------|---------|
| `sonnet` | Claude Sonnet（推荐用于 executor，速度快） |
| `opus` | Claude Opus（推荐用于 judge/reviser，质量高） |
| `haiku` | Claude Haiku（轻量任务） |

> **注意：** 使用 `claude-sonnet-4-6` 等完整 ID 会导致 API 报错。

### 超时配置

`default_case_timeout_seconds` 控制每个用例和修订步骤的执行超时。建议设为 `300`（5 分钟），过短会导致 executor/reviser 未完成就被终止。单个用例也可在 `metadata.json` 中通过 `timeout_seconds` 单独设置。

配置优先级：**CLI 参数 > 配置文件 > 默认值**。

## 用例类型

### text（文本比对）
比较 executor 的 stdout 输出与 `expected.txt`：
- 期望文本 < 100 字符：直接用文本相似度（difflib）打分，不消耗 Claude API
- 期望文本 >= 100 字符：调用 judge 模型评分

### files（文件比对）
比较 executor 产出的文件与 `expected_files/` 目录：
- 用 difflib 计算文件内容相似度（0-1 分）
- 相似度 >= 0.8 直接使用 difflib 分数（零 token 消耗）
- 相似度 < 0.8 时调用 AI judge 评分（语义相似也算通过）
- 实际输出中的额外文件默认忽略
- 期望文件缺失 → 0 分

### mixed（混合比对）
同时进行文本比对和文件比对，两者必须同时通过。

## 运行产物

每次迭代的运行产物保存在 `output/runs/iter_NNN/`：

```
output/runs/iter_001/
├── case_001/
│   ├── prompt.txt       # 发送给 executor 的完整 prompt
│   ├── stdout.txt       # executor 的标准输出
│   ├── stderr.txt       # executor 的错误输出
│   ├── return_code.txt  # 退出码
│   └── judge/           # 裁判运行产物（仅在需要时）
├── case_002/
└── revision/            # 修订 prompt 与输出
```

SKILL.md 的每次修改都会备份到 `output/backups/SKILL_时间戳.md`。

## 最佳实践

### 1. 用例设计

- **一个用例只验证一个行为**：避免将多个独立功能塞进同一个用例，这样定位失败原因更精准。
- **用例名用描述性短语**：如 `loop-to-comprehension`、`add-error-handling`，而非 `case_001`。
- **从简单到复杂**：先建几个简单用例验证 SKILL 基本能力，再逐步增加边界条件和复杂场景。
- **合理设置 `--min-score`**：简单任务可设 0.95 要求精确匹配；创造性任务可放宽到 0.75。

### 2. 模型选择

```json
{
  "executor": { "command": "claude", "model": "sonnet" },
  "judge":    { "command": "claude", "model": "opus" },
  "reviser":  { "command": "claude", "model": "opus" }
}
```

- **Executor 用 Sonnet**：执行速度快、成本低，适合高频调用。
- **Judge/Reviser 用 Opus**：评分和修订需要更强的推理能力，Opus 质量更高。
- **预算有限时**：三个角色都用 Sonnet 也能工作，只是修订质量可能略低。

### 3. 迭代策略

- **`max_iterations` 设为 3~5**：通常 2~3 轮就能收敛，超过 5 轮说明 SKILL 或用例本身需要重新设计。
- **观察失败模式**：如果连续多轮在同一个用例上失败，说明 SKILL 的指导方向有误，应手动调整 SKILL 而非继续自动迭代。
- **及时中断**：发现修订方向偏离时，`Ctrl+C` 中断比让它跑满迭代更高效。

### 4. 超时设置

- **默认 300 秒**适用于大多数场景。
- **复杂任务（多文件生成、大量代码重构）**：建议增大到 600 秒。
- **简单文本输出任务**：可缩短到 120 秒，加快反馈循环。
- **单个用例超时**：在 `metadata.json` 中用 `timeout_seconds` 单独设置，不影响其他用例。

### 5. 目录管理

- **`--output-dir` 集中输出**：将 `runs/` 和 `backups/` 统一放到 `output/` 目录，方便 `.gitignore` 管理。
- **定期清理产物**：`output/runs/` 会随迭代快速增长，实验完成后及时清理。
- **备份不要删除**：`output/backups/` 中的备份是 SKILL 演进的历史记录，回溯时很有价值。

### 6. 配置管理

- **版本控制配置文件**：`skill_optimizer.json` 建议纳入 git，方便团队共享实验参数。
- **多配置对比实验**：用 `--config` 指定不同配置文件，对比不同模型组合的效果。

```bash
# Sonnet 全家桶（快速迭代）
python main.py --config config_sonnet.json

# Opus 全家桶（高质量）
python main.py --config config_opus.json
```

### 7. 常见陷阱

| 陷阱 | 解决方案 |
|------|---------|
| 用例过于模糊，评分随机 | 明确期望输出，减少歧义空间 |
| SKILL.md 过于冗长 | 精简到核心指令，避免信息过载 |
| 所有用例都通过但 SKILL 不通用 | 增加多样化用例覆盖不同场景 |
| executor 输出格式不稳定 | 在 SKILL 中明确指定输出格式要求 |
| 超时频繁 | 增大 `timeout` 或简化任务复杂度 |

## 运行测试

```bash
# 运行全部测试
python -m unittest discover -s tests -v

# 运行单个测试模块
python -m unittest tests/test_config.py -v
```

## 多轮测试用例

当 skill 需要先追问用户再给出答案时，在用例目录中加入 `dialogue.json`。

```json
{
  "turns": [
    {
      "user": "Under $50"
    },
    {
      "user": "更偏实用"
    },
    {
      "user": "给办公场景用"
    }
  ]
}
```

多轮用例最佳实践：

- `dialogue.json` 保持尽量短，内容要稳定、可复现。
- 只把中间追问写进 `dialogue.json`，最终结果仍由 `expected.txt` 或 `expected_files/` 判定。
- `turns` 按预期追问次数顺序排列，写几条就允许几轮继续问。
- `user` 回复要短而明确，避免引入不必要歧义。
- 调试对话流程时，查看 `output/runs/iter_NNN/case_XXX/transcript.json`。
