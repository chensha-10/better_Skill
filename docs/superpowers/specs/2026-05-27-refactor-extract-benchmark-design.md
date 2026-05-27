# 代码提取重构 Benchmark — 设计文档

## 目标

创建一个 SKILL + 配套测试用例，验证 SKILL 优化器框架能否将一个"有规则但不完善"的 SKILL 逐步改进到通过所有测试用例。

## 被测对象

### 初始 SKILL（workspace/SKILL.md）

一个中文编写的代码提取重构 SKILL，有基本规则但存在以下缺陷：

- 未说明如何判断新函数的插入位置（函数前/后、类内部？）
- 未说明如何处理作用域变量（闭包 vs 传参）
- 未规定提取后函数的命名规范
- 未要求保留注释和 docstring
- 未指定输入/输出文件的读取写入方式

```markdown
---
name: refactor-extract
description: 提取长函数中的代码块为独立函数
---

# 代码提取重构

## 规则
- 读取用户指定的源文件
- 找到函数中超过 10 行的连续代码块
- 将其提取为独立函数
- 在合适的位置插入新函数
- 将重构后的代码写入同路径文件
```

## 测试用例

三个用例均为 `files` 类型，只比对输出源文件正确性。min_score 统一 0.85，timeout 120s。

### case_001 — 简单提取（无参数代码块）

- **源文件**：`calculate_invoice(orders)` 函数，约 35 行
- **提取目标**：运费计算块（`if order_subtotal < 50` 分支链）
  - 不依赖外部变量，只使用参数 `order_subtotal`
  - 提取为 `_calculate_shipping(order_subtotal)`
- **期望**：在源函数上方插入新函数，原处替换为 `_calculate_shipping(order_subtotal)` 调用

### case_002 — 带参数提取

- **源文件**：`export_user_report(user_id, output_dir, include_private)` 函数，约 50 行
- **提取目标 1**：会话分析块（遍历 sessions）
  - 依赖 1 个入参 `sessions`，产生 3 个返回值（total_duration, active_days, device_types）
  - 提取为 `_analyze_sessions(sessions)`
- **提取目标 2**：角色描述转换块
  - 依赖 `permissions` 参数
  - 提取为 `_describe_roles(permissions)`
- **期望**：正确推断参数和返回值，import 保持在文件顶部

### case_003 — 保留 docstring/注释

- **源文件**：`migrate_database(connection, migrations_dir, dry_run)` 函数，约 55 行
- **提取目标**：单条迁移执行块（事务 + SQL 执行逻辑）
  - 依赖 `cursor`, `version`, `filepath`, `dry_run`
  - 提取为 `_apply_single_migration(cursor, version, filepath, dry_run)`
- **期望**：保留原有注释（如 `# Split on semicolons to handle multi-statement files`），新函数带有 docstring，`try/except` 事务回滚逻辑正确保留在原处

### 用例目录结构

```
test_cases/
├── case_001/
│   ├── prompt.txt
│   ├── input_files/
│   │   └── source.py          # calculate_invoice
│   ├── expected_files/
│   │   └── source.py          # 重构后正确结果
│   └── metadata.json
├── case_002/
│   └── ...同上
└── case_003/
    └── ...同上
```

每个用例的 prompt.txt 描述任务目标，expected_files/source.py 为预期的重构结果。

## 难度梯度

| 用例 | 难度 | 挑战点 |
|------|------|--------|
| case_001 | 低 | 无参数依赖，单块提取，简单返回值 |
| case_002 | 中 | 多参数多返回值，两块提取，import 保持 |
| case_003 | 高 | 需保留注释和 docstring，事务上下文，异常处理边界 |

## 验收标准

运行 `python main.py` 后，优化器应从初始 SKILL 出发，通过多轮 Executor → Judge → Reviser 迭代，最终：

1. 所有 3 个用例通过（files 比对一致）
2. 平均分 >= 0.85
3. 优化后的 SKILL.md 比初始版本包含更完整的提取规则
