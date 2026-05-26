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
- **Executor（执行者）**：用当前 SKILL 响应测试 prompt
- **Judge（裁判）**：对比实际输出与期望输出，给出 0-1 分数
- **Reviser（修订者）**：根据失败原因改进 SKILL.md

## 项目结构

```
skill_optimizer/          核心模块
├── config.py             ModelConfig / Config 数据类，三层配置合并
├── cases.py              测试用例模板创建与加载
├── files.py              文件备份、目录创建、期望文件比对
├── runner.py             Claude CLI 调用（cwd 隔离、超时处理）
├── judge.py              评分解析（JSON 容错、difflib 捷径）
├── optimizer.py          SKILL 修订校验、备份、prompt 构建
main.py                   CLI 入口
tests/                    单元测试（54 个）
workspace/SKILL.md        示例 SKILL
test_cases/case_001/      示例用例
```

## 前置条件

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 已安装并可用

## 快速开始

### 1. 创建测试用例

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
└── metadata.json       # 用例元数据
```

### 2. 编辑用例内容

编辑 `prompt.txt` 和 `expected.txt` 填入实际的测试内容：

**prompt.txt:**
```
Respond with exactly: hello skill
```

**expected.txt:**
```
hello skill
```

### 3. 准备待优化的 SKILL

编辑 `workspace/SKILL.md`，这是将被优化器反复修订的文件：

```markdown
---
name: sample-answer-skill
description: Answers simple test prompts
---

# Sample Answer Skill

When given a test prompt, answer directly.
```

### 4. 运行优化

```bash
python main.py
```

优化器会：
1. 用 executor 模型执行每个用例
2. 用 judge 模型对结果评分
3. 如果全部通过 → 结束
4. 如果未通过 → 用 reviser 模型修订 SKILL.md → 回到步骤 1
5. 到达最大迭代次数仍未通过 → 退出并报告

每次迭代的结果保存在 `workspace/runs/iter_001/` 目录下。

## CLI 参数

```
python main.py [全局参数] [子命令] [子命令参数]
```

### 全局参数（适用于所有子命令）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--project-root` | 项目根目录 | 脚本所在目录 |
| `--config` | 配置文件路径 | `./skill_optimizer.json` |
| `--skill-path` | SKILL.md 路径 | `./workspace/SKILL.md` |
| `--test-cases-dir` | 用例目录 | `./test_cases` |
| `--workspace-dir` | 工作区目录 | `./workspace` |
| `--runs-dir` | 运行产物目录 | `./workspace/runs` |
| `--backups-dir` | 备份目录 | `./workspace/backups` |

### init-case 子命令

```bash
python main.py init-case <用例名> [--type text|files|mixed] [--min-score 0.85] [--timeout 120]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `case_name` | 用例名称（目录名） | 必填 |
| `--type` | 用例类型 | `mixed` |
| `--min-score` | 通过的最低分数 | `0.85` |
| `--timeout` | 执行超时（秒） | `120` |

## 配置文件

复制 `skill_optimizer.json.example` 为 `skill_optimizer.json` 进行自定义配置：

```json
{
  "skill_path": "./workspace/SKILL.md",
  "test_cases_dir": "./test_cases",
  "workspace_dir": "./workspace",
  "runs_dir": "./workspace/runs",
  "backups_dir": "./workspace/backups",
  "executor": {
    "command": "claude",
    "model": "claude-sonnet-4-6"
  },
  "judge": {
    "command": "claude",
    "model": "claude-opus-4-7"
  },
  "reviser": {
    "command": "claude",
    "model": "claude-opus-4-7"
  },
  "score_threshold": 0.85,
  "max_iterations": 5,
  "default_case_timeout_seconds": 120
}
```

配置优先级：**CLI 参数 > 配置文件 > 默认值**。

## 用例类型

### text（文本比对）
比较 executor 的 stdout 输出与 `expected.txt`：
- 期望文本 < 100 字符：直接用文本相似度（difflib）打分，不消耗 Claude API
- 期望文本 >= 100 字符：调用 judge 模型评分

### files（文件比对）
比较 executor 产出的文件与 `expected_files/` 目录：
- 精确字节比对
- 实际输出中的额外文件默认忽略
- 期望文件缺失或内容不一致 → 0 分

### mixed（混合比对）
同时进行文本比对和文件比对，两者必须同时通过。

## 运行产物

每次迭代的运行产物保存在 `workspace/runs/iter_NNN/`：

```
runs/iter_001/
├── case_001/
│   ├── prompt.txt       # 发送给 executor 的完整 prompt
│   ├── stdout.txt       # executor 的标准输出
│   ├── stderr.txt       # executor 的错误输出
│   ├── return_code.txt  # 退出码
│   └── judge/           # 裁判运行产物（仅在需要时）
├── case_002/
└── revision/            # 修订 prompt 与输出
```

SKILL.md 的每次修改都会备份到 `workspace/backups/SKILL_时间戳.md`。

## 运行测试

```bash
# 运行全部测试
python -m unittest discover -s tests -v

# 运行单个测试模块
python -m unittest tests/test_config.py -v
```
