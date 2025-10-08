from requests import get as requests_get


def check(url: str = "http://127.0.0.1:8002") -> dict:
    ok = True
    errs = []
    try:
        h = requests_get(url.rstrip("/") + "/admin/health", timeout=5).json()
        if not h.get("ok"):
            ok = False
            errs.append("health not ok")
    except Exception as e:
        ok = False
        errs.append(str(e))
    return {"ok": ok, "errors": errs}


def run(**kwargs):
    url = kwargs.get("url", "http://127.0.0.1:8002")
    result = check(url)
    ok = result.get("ok", False)
    errors = result.get("errors") or []
    error_msg = None if ok else "; ".join(errors) or "Unknown error"
    return {"ok": ok, "data": {"url": url, **result}, "error": error_msg}
