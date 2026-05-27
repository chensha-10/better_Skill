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
