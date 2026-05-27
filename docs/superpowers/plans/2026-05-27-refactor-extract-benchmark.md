# 代码提取重构 Benchmark — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个中文"代码提取重构"SKILL + 3 个 files 类型测试用例，作为 SKILL 优化器框架的基准测试。

**Architecture:** 纯数据创建，不修改框架代码。仅覆盖 `workspace/SKILL.md`（初始有缺陷的 SKILL）和 `test_cases/case_001~003/`（3 个渐进难度用例），每个用例包含 `input_files/source.py` 和 `expected_files/source.py` 用于精确文件比对。

**Tech Stack:** 无代码逻辑，纯文件创建。Python 源文件仅作为测试数据。

---

## 文件结构

```
F:\testprogram\better_Skill\workspace\SKILL.md    # 替换为中文重构 SKILL（有规则但不完善）
F:\testprogram\better_Skill\test_cases\
├── case_001\                                       # 清除旧内容后重建
│   ├── prompt.txt                                  # "读取 source.py，重构提取代码块..."
│   ├── input_files\source.py                       # calculate_invoice 源文件
│   ├── expected_files\source.py                    # 重构后正确结果
│   └── metadata.json                               # type: files, min_score: 0.85
├── case_002\                                       # 新建
│   └── ...同上 (export_user_report)
└── case_003\                                       # 新建
    └── ...同上 (migrate_database)
```

---

### Task 1: 替换初始 SKILL.md

**Files:**
- Modify: `F:\testprogram\better_Skill\workspace\SKILL.md`

- [ ] **Step 1: 覆盖写入中文重构 SKILL**

将 `F:\testprogram\better_Skill\workspace\SKILL.md` 替换为以下内容：

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

- [ ] **Step 2: 提交**

```bash
git add F:/testprogram/better_Skill/workspace/SKILL.md
git commit -m "$(cat <<'EOF'
feat: 替换 SKILL.md 为中文代码提取重构 SKILL（初始有缺陷版本）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: 清除旧测试用例并创建 case_001（简单提取：无参数代码块）

**Files:**
- Delete: `F:\testprogram\better_Skill\test_cases\case_001\` (existing sample)
- Create: `F:\testprogram\better_Skill\test_cases\case_001\metadata.json`
- Create: `F:\testprogram\better_Skill\test_cases\case_001\prompt.txt`
- Create: `F:\testprogram\better_Skill\test_cases\case_001\input_files\source.py`
- Create: `F:\testprogram\better_Skill\test_cases\case_001\expected_files\source.py`

- [ ] **Step 1: 删除旧 case_001 目录**

```bash
rm -rf F:/testprogram/better_Skill/test_cases/case_001
```

- [ ] **Step 2: 创建目录结构**

```bash
mkdir -p F:/testprogram/better_Skill/test_cases/case_001/input_files
mkdir -p F:/testprogram/better_Skill/test_cases/case_001/expected_files
```

- [ ] **Step 3: 创建 metadata.json**

写入 `F:\testprogram\better_Skill\test_cases\case_001\metadata.json`：

```json
{
  "name": "case_001",
  "type": "files",
  "min_score": 0.85,
  "timeout_seconds": 120
}
```

- [ ] **Step 4: 创建 prompt.txt**

写入 `F:\testprogram\better_Skill\test_cases\case_001\prompt.txt`：

```
读取 source.py 文件，将其中的长函数重构，提取合适的代码块为独立函数。将重构后的代码写回 source.py。
```

- [ ] **Step 5: 创建 input_files/source.py**

写入 `F:\testprogram\better_Skill\test_cases\case_001\input_files\source.py`：

```python
def calculate_invoice(orders):
    """Calculate total invoice amount from orders."""
    subtotal = 0
    tax_total = 0
    shipping_total = 0
    for order in orders:
        if order.get("status") == "cancelled":
            continue
        items = order.get("items", [])
        order_subtotal = 0
        for item in items:
            price = item.get("price", 0)
            quantity = item.get("quantity", 1)
            discount = item.get("discount", 0)
            order_subtotal += price * quantity * (1 - discount)
        subtotal += order_subtotal
        tax_rate = order.get("tax_rate", 0.08)
        order_tax = order_subtotal * tax_rate
        tax_total += order_tax
        if order_subtotal < 50:
            shipping_total += 5.99
        elif order_subtotal < 100:
            shipping_total += 3.99
        else:
            shipping_total += 0
    total = subtotal + tax_total + shipping_total
    return {
        "subtotal": round(subtotal, 2),
        "tax": round(tax_total, 2),
        "shipping": round(shipping_total, 2),
        "total": round(total, 2)
    }
```

- [ ] **Step 6: 创建 expected_files/source.py**

写入 `F:\testprogram\better_Skill\test_cases\case_001\expected_files\source.py`：

```python
def _calculate_shipping(order_subtotal):
    """Calculate shipping cost based on order subtotal."""
    if order_subtotal < 50:
        return 5.99
    elif order_subtotal < 100:
        return 3.99
    else:
        return 0


def calculate_invoice(orders):
    """Calculate total invoice amount from orders."""
    subtotal = 0
    tax_total = 0
    shipping_total = 0
    for order in orders:
        if order.get("status") == "cancelled":
            continue
        items = order.get("items", [])
        order_subtotal = 0
        for item in items:
            price = item.get("price", 0)
            quantity = item.get("quantity", 1)
            discount = item.get("discount", 0)
            order_subtotal += price * quantity * (1 - discount)
        subtotal += order_subtotal
        tax_rate = order.get("tax_rate", 0.08)
        order_tax = order_subtotal * tax_rate
        tax_total += order_tax
        shipping_total += _calculate_shipping(order_subtotal)
    total = subtotal + tax_total + shipping_total
    return {
        "subtotal": round(subtotal, 2),
        "tax": round(tax_total, 2),
        "shipping": round(shipping_total, 2),
        "total": round(total, 2)
    }
```

- [ ] **Step 7: 提交**

```bash
git add F:/testprogram/better_Skill/test_cases/case_001/
git commit -m "$(cat <<'EOF'
feat: 创建 case_001 — 简单提取（无参数代码块）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 创建 case_002（带参数提取）

**Files:**
- Create: `F:\testprogram\better_Skill\test_cases\case_002\metadata.json`
- Create: `F:\testprogram\better_Skill\test_cases\case_002\prompt.txt`
- Create: `F:\testprogram\better_Skill\test_cases\case_002\input_files\source.py`
- Create: `F:\testprogram\better_Skill\test_cases\case_002\expected_files\source.py`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p F:/testprogram/better_Skill/test_cases/case_002/input_files
mkdir -p F:/testprogram/better_Skill/test_cases/case_002/expected_files
```

- [ ] **Step 2: 创建 metadata.json**

写入 `F:\testprogram\better_Skill\test_cases\case_002\metadata.json`：

```json
{
  "name": "case_002",
  "type": "files",
  "min_score": 0.85,
  "timeout_seconds": 120
}
```

- [ ] **Step 3: 创建 prompt.txt**

写入 `F:\testprogram\better_Skill\test_cases\case_002\prompt.txt`：

```
读取 source.py 文件，分析其中的长函数，将可复用的代码块提取为独立函数，并写回 source.py。注意正确推断新函数的参数和返回值。
```

- [ ] **Step 4: 创建 input_files/source.py**

写入 `F:\testprogram\better_Skill\test_cases\case_002\input_files\source.py`：

```python
import json
import os


def export_user_report(user_id, output_dir, include_private=False):
    """Generate a user activity report and export to JSON."""
    user_data_path = os.path.join(output_dir, f"user_{user_id}.json")
    with open(user_data_path, "r") as f:
        user = json.load(f)

    profile = {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "created_at": user.get("created_at"),
    }

    sessions = user.get("sessions", [])
    total_duration = 0
    active_days = set()
    device_types = {}
    for session in sessions:
        total_duration += session.get("duration", 0)
        day = session.get("date", "")[:10]
        if day:
            active_days.add(day)
        device = session.get("device", "unknown")
        device_types[device] = device_types.get(device, 0) + 1

    most_used_device = max(device_types, key=device_types.get) if device_types else "none"

    permissions = user.get("permissions", [])
    role_labels = {
        "admin": "Administrator",
        "editor": "Content Editor",
        "viewer": "Read-Only Viewer",
    }
    role_descriptions = []
    for perm in permissions:
        label = role_labels.get(perm, perm)
        role_descriptions.append(label)

    report = {
        "profile": profile,
        "activity": {
            "total_sessions": len(sessions),
            "total_duration_minutes": round(total_duration / 60, 2),
            "active_days": len(active_days),
            "most_used_device": most_used_device,
        },
    }
    if include_private:
        report["roles"] = role_descriptions

    report_path = os.path.join(output_dir, f"report_{user_id}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_path
```

- [ ] **Step 5: 创建 expected_files/source.py**

写入 `F:\testprogram\better_Skill\test_cases\case_002\expected_files\source.py`：

```python
import json
import os


def _analyze_sessions(sessions):
    """Analyze session data — returns total_duration, active_days, device_types."""
    total_duration = 0
    active_days = set()
    device_types = {}
    for session in sessions:
        total_duration += session.get("duration", 0)
        day = session.get("date", "")[:10]
        if day:
            active_days.add(day)
        device = session.get("device", "unknown")
        device_types[device] = device_types.get(device, 0) + 1
    return total_duration, active_days, device_types


def _describe_roles(permissions):
    """Convert permission codes to human-readable role labels."""
    role_labels = {
        "admin": "Administrator",
        "editor": "Content Editor",
        "viewer": "Read-Only Viewer",
    }
    role_descriptions = []
    for perm in permissions:
        label = role_labels.get(perm, perm)
        role_descriptions.append(label)
    return role_descriptions


def export_user_report(user_id, output_dir, include_private=False):
    """Generate a user activity report and export to JSON."""
    user_data_path = os.path.join(output_dir, f"user_{user_id}.json")
    with open(user_data_path, "r") as f:
        user = json.load(f)

    profile = {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "created_at": user.get("created_at"),
    }

    sessions = user.get("sessions", [])
    total_duration, active_days, device_types = _analyze_sessions(sessions)
    most_used_device = max(device_types, key=device_types.get) if device_types else "none"

    report = {
        "profile": profile,
        "activity": {
            "total_sessions": len(sessions),
            "total_duration_minutes": round(total_duration / 60, 2),
            "active_days": len(active_days),
            "most_used_device": most_used_device,
        },
    }
    if include_private:
        report["roles"] = _describe_roles(user.get("permissions", []))

    report_path = os.path.join(output_dir, f"report_{user_id}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_path
```

- [ ] **Step 6: 提交**

```bash
git add F:/testprogram/better_Skill/test_cases/case_002/
git commit -m "$(cat <<'EOF'
feat: 创建 case_002 — 带参数提取（多参数多返回值）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 创建 case_003（保留 docstring/注释）

**Files:**
- Create: `F:\testprogram\better_Skill\test_cases\case_003\metadata.json`
- Create: `F:\testprogram\better_Skill\test_cases\case_003\prompt.txt`
- Create: `F:\testprogram\better_Skill\test_cases\case_003\input_files\source.py`
- Create: `F:\testprogram\better_Skill\test_cases\case_003\expected_files\source.py`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p F:/testprogram/better_Skill/test_cases/case_003/input_files
mkdir -p F:/testprogram/better_Skill/test_cases/case_003/expected_files
```

- [ ] **Step 2: 创建 metadata.json**

写入 `F:\testprogram\better_Skill\test_cases\case_003\metadata.json`：

```json
{
  "name": "case_003",
  "type": "files",
  "min_score": 0.85,
  "timeout_seconds": 120
}
```

- [ ] **Step 3: 创建 prompt.txt**

写入 `F:\testprogram\better_Skill\test_cases\case_003\prompt.txt`：

```
读取 source.py 文件，重构其中的长函数，提取合适的代码块为独立辅助函数。要求保留所有原有的 docstring 和注释。将结果写回 source.py。
```

- [ ] **Step 4: 创建 input_files/source.py**

写入 `F:\testprogram\better_Skill\test_cases\case_003\input_files\source.py`：

```python
def migrate_database(connection, migrations_dir, dry_run=False):
    """Apply pending database migrations in order.

    Scans the migrations directory for .sql files, determines which ones
    have not yet been applied, and executes them in version order. Supports
    a dry-run mode that prints what would happen without making changes.
    """
    import os
    import re

    # --- Discover migration files ---
    all_files = []
    version_pattern = re.compile(r"^(\d{3})_.*\.sql$")
    for entry in os.listdir(migrations_dir):
        match = version_pattern.match(entry)
        if match:
            version = int(match.group(1))
            filepath = os.path.join(migrations_dir, entry)
            all_files.append((version, filepath))
    # Sort by version number to ensure correct order
    all_files.sort(key=lambda x: x[0])

    # --- Determine which migrations are pending ---
    cursor = connection.cursor()
    cursor.execute(
        "SELECT version FROM migrations ORDER BY version"
    )
    applied_versions = {row[0] for row in cursor.fetchall()}
    pending = [
        (ver, path) for ver, path in all_files
        if ver not in applied_versions
    ]

    if not pending:
        return {"status": "up_to_date", "applied": 0}

    # --- Execute pending migrations ---
    applied = []
    for version, filepath in pending:
        sql = open(filepath, "r").read()
        if dry_run:
            applied.append(
                {"version": version, "file": os.path.basename(filepath)}
            )
        else:
            cursor.execute("BEGIN")
            try:
                # Split on semicolons to handle multi-statement files
                statements = [s.strip() for s in sql.split(";") if s.strip()]
                for stmt in statements:
                    cursor.execute(stmt)
                cursor.execute(
                    "INSERT INTO migrations (version, filename) VALUES (?, ?)",
                    (version, os.path.basename(filepath)),
                )
                cursor.execute("COMMIT")
                applied.append(
                    {"version": version, "file": os.path.basename(filepath)}
                )
            except Exception:
                cursor.execute("ROLLBACK")
                return {
                    "status": "failed",
                    "applied": applied,
                    "failed_at": version,
                }

    return {"status": "ok", "applied": applied}
```

- [ ] **Step 5: 创建 expected_files/source.py**

写入 `F:\testprogram\better_Skill\test_cases\case_003\expected_files\source.py`：

```python
def _apply_single_migration(cursor, version, filepath, dry_run):
    """Apply a single migration file. Returns a dict with version and file."""
    import os

    if dry_run:
        return {"version": version, "file": os.path.basename(filepath)}

    sql = open(filepath, "r").read()
    cursor.execute("BEGIN")
    # Split on semicolons to handle multi-statement files
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        cursor.execute(stmt)
    cursor.execute(
        "INSERT INTO migrations (version, filename) VALUES (?, ?)",
        (version, os.path.basename(filepath)),
    )
    cursor.execute("COMMIT")
    return {"version": version, "file": os.path.basename(filepath)}


def migrate_database(connection, migrations_dir, dry_run=False):
    """Apply pending database migrations in order.

    Scans the migrations directory for .sql files, determines which ones
    have not yet been applied, and executes them in version order. Supports
    a dry-run mode that prints what would happen without making changes.
    """
    import os
    import re

    # --- Discover migration files ---
    all_files = []
    version_pattern = re.compile(r"^(\d{3})_.*\.sql$")
    for entry in os.listdir(migrations_dir):
        match = version_pattern.match(entry)
        if match:
            version = int(match.group(1))
            filepath = os.path.join(migrations_dir, entry)
            all_files.append((version, filepath))
    # Sort by version number to ensure correct order
    all_files.sort(key=lambda x: x[0])

    # --- Determine which migrations are pending ---
    cursor = connection.cursor()
    cursor.execute(
        "SELECT version FROM migrations ORDER BY version"
    )
    applied_versions = {row[0] for row in cursor.fetchall()}
    pending = [
        (ver, path) for ver, path in all_files
        if ver not in applied_versions
    ]

    if not pending:
        return {"status": "up_to_date", "applied": 0}

    # --- Execute pending migrations ---
    applied = []
    for version, filepath in pending:
        try:
            result = _apply_single_migration(cursor, version, filepath, dry_run)
            applied.append(result)
        except Exception:
            cursor.execute("ROLLBACK")
            return {
                "status": "failed",
                "applied": applied,
                "failed_at": version,
            }

    return {"status": "ok", "applied": applied}
```

- [ ] **Step 6: 提交**

```bash
git add F:/testprogram/better_Skill/test_cases/case_003/
git commit -m "$(cat <<'EOF'
feat: 创建 case_003 — 保留 docstring/注释的提取重构

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: 验证

- [ ] **Step 1: 确认目录结构完整**

```bash
ls -R F:/testprogram/better_Skill/test_cases/
```

期望：三个 case_001/002/003 目录各含 prompt.txt、input_files/source.py、expected_files/source.py、metadata.json。

- [ ] **Step 2: 确认 SKILL.md 内容**

```bash
head -5 F:/testprogram/better_Skill/workspace/SKILL.md
```

期望：frontmatter 包含 `name: refactor-extract`。

- [ ] **Step 3: 运行框架预检**

```bash
python F:/testprogram/better_Skill/main.py
```

期望：加载 3 个用例，若 Claude CLI 可用则开始迭代优化；若不可用则清晰报错而非崩溃。

## 自查

- **Spec 覆盖**：Task 1 覆盖初始 SKILL；Task 2-4 覆盖 3 个用例；Task 5 覆盖验收验证
- **占位扫描**：无 TBD/TODO/留空
- **类型一致性**：全部使用 `files` 类型，metadata 格式统一，无代码逻辑需类型校验
- **范围检查**：不修改框架代码，纯创建测试数据文件
