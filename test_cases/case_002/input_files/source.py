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
