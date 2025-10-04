import json
from dotenv import load_dotenv
from adam_tools.plugins.github_publisher_plugin.sidecars.github_publisher.plugin import (
    main_rpc,
)


def call(payload: dict) -> dict:
    # Expecting a plain dict; stringify for the RPC, parse result back to dict.
    load_dotenv()  # keep token/org local via .env
    try:
        raw = main_rpc(json.dumps(payload))
        data = json.loads(raw) if isinstance(raw, str) else raw
        # Normalize shape
        return (
            data
            if isinstance(data, dict)
            else {"ok": False, "error": "bad response type"}
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}
