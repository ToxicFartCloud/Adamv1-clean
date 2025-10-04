#!/usr/bin/env python3
# Compare baseline vs SLED by calling the local server.
import argparse
import json
import time
from typing import Dict, Any
import urllib.request


def _post(url: str, payload: Dict[str, Any]):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _score(pred: str, target: str) -> float:
    # Very simple proxy: exact substring match -> 1 else 0
    return 1.0 if target.strip().lower() in pred.strip().lower() else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8010", type=str)
    ap.add_argument("--path", default="eval/items.jsonl", type=str)
    args = ap.parse_args()

    with open(args.path, "r", encoding="utf-8") as f:
        items = [json.loads(l) for l in f if l.strip()]

    def run_mode(mode: str):
        latencies = []
        scores = []
        for it in items:
            t0 = time.time()
            out = _post(
                args.server + "/generate",
                {
                    "mode": mode,
                    "prompt": it["prompt"],
                    "gen_args": {"max_new_tokens": 48},
                },
            )
            dt = time.time() - t0
            if not out.get("ok"):
                latencies.append(dt)
                scores.append(0.0)
                continue
            ans = out["data"]["answer"]
            latencies.append(dt)
            scores.append(_score(ans, it.get("answer", "")))
        return latencies, scores

    base_lat, base_scores = run_mode("baseline")
    sled_lat, sled_scores = run_mode("sled")

    def summary(name, lat, sc):
        print(
            f"{name:9s}  n={len(sc):2d}  avg_latency={sum(lat) / len(lat):.3f}s  acc={sum(sc) / len(sc):.2f}"
        )

    summary("baseline", base_lat, base_scores)
    summary("sled", sled_lat, sled_scores)


if __name__ == "__main__":
    main()
