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
