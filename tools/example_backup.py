def run(**kwargs):
    target = kwargs.get("target", "default_target")
    return {
        "ok": True,
        "data": f"Backup completed for: {target}",
        "error": None,
    }
