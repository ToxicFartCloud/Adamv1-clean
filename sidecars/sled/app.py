# FastAPI server for the SLED decoding pilot (offline-only).
# Start (from project root):
#   python -m sidecars.sled.app --model_path /path/to/local/model
# Optional:
#   --tokenizer_path (defaults to model_path)
#   --layers last_k|all
#   --k 8
#   --host 0.0.0.0
#   --port 8010
import argparse
import os
import json
import time
import logging
import torch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer

from .sled_decode import generate_sled, generate_baseline, fit_layer_weights

# Determinism (best-effort)
torch.manual_seed(42)
random_states = os.environ.get("PYTHONHASHSEED", "0")

app = FastAPI()


def json_logger(name: str, path: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.FileHandler(path)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    if logger.handlers:
        logger.handlers.clear()
    logger.addHandler(handler)
    return logger


srv_logger = json_logger("sled_server", "logs/sled_server.jsonl")


class ServerState:
    model = None
    tokenizer = None
    cfg = {
        "layers": "last_k",
        "k": 8,
        "weighting": "uniform",
        "weights_path": "sled_weights.npz",
    }


STATE = ServerState()


@app.post("/generate")
async def generate(req: Request):
    body = await req.json()
    mode = body.get("mode", "sled")
    prompt = body.get("prompt", "")
    gen_args = body.get("gen_args", {}) or {}
    weights_override = body.get("weights_path") or gen_args.pop("weights_path", None)
    weights_path = weights_override or STATE.cfg["weights_path"]
    if not prompt:
        return JSONResponse({"ok": False, "error": "Missing prompt"}, status_code=400)

    t0 = time.time()
    try:
        if mode == "baseline":
            text = generate_baseline(STATE.model, STATE.tokenizer, prompt, **gen_args)
            used = "baseline"
            meta = {"layers": None, "weights_info": "n/a", "weights_path": None}
        else:
            text, meta = generate_sled(
                STATE.model,
                STATE.tokenizer,
                prompt,
                layers=STATE.cfg["layers"],
                k=STATE.cfg["k"],
                weighting=STATE.cfg["weighting"],
                weights_path=weights_path,
                **gen_args,
            )
            used = "sled"
            meta.setdefault(
                "weights_path",
                weights_path if meta.get("weighting_applied") == "learned" else None,
            )
        dt = time.time() - t0
        out = {
            "ok": True,
            "data": {
                "answer": text,
                "used_mode": used,
                **meta,
                "latency_s": round(dt, 3),
            },
            "error": None,
        }
        srv_logger.info(
            json.dumps({"event": "generate", "mode": used, "latency_s": dt})
        )
        return JSONResponse(out)
    except Exception as e:
        srv_logger.info(
            json.dumps({"event": "error", "where": "generate", "error": str(e)})
        )
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.post("/calibrate")
async def calibrate(req: Request):
    body = await req.json()
    path = body.get("path", "eval/items.jsonl")
    out_path = body.get("out_path") or STATE.cfg["weights_path"]
    layers = body.get("layers", STATE.cfg["layers"])
    k = int(body.get("k", STATE.cfg["k"]))
    weighting_override = body.get("weighting")
    try:
        info = fit_layer_weights(
            STATE.model, STATE.tokenizer, path, layers=layers, k=k, out_path=out_path
        )
        ok = info.get("ok", False)
        data = info if ok else None
        err = None if ok else info.get("error", "unknown")
        if ok:
            STATE.cfg["layers"] = layers
            STATE.cfg["k"] = k
            STATE.cfg["weights_path"] = out_path
            if weighting_override:
                STATE.cfg["weighting"] = weighting_override
        srv_logger.info(json.dumps({"event": "calibrate", "ok": ok}))
        return JSONResponse({"ok": ok, "data": data, "error": err})
    except Exception as e:
        srv_logger.info(
            json.dumps({"event": "error", "where": "calibrate", "error": str(e)})
        )
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


def _parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_path", required=True, type=str)
    ap.add_argument("--tokenizer_path", default=None, type=str)
    ap.add_argument("--layers", default="last_k", choices=["last_k", "all"])
    ap.add_argument("--k", default=8, type=int)
    ap.add_argument(
        "--weighting",
        default="uniform",
        choices=["uniform", "depth_softmax", "learned"],
    )
    ap.add_argument("--weights_path", default="sled_weights.npz", type=str)
    ap.add_argument("--host", default="0.0.0.0", type=str)
    ap.add_argument("--port", default=8010, type=int)
    return ap.parse_args()


def load_model_tokenizer(model_path: str, tokenizer_path: str = None):
    tok_path = tokenizer_path or model_path
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(tok_path, local_files_only=True)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def main():
    args = _parse_args()
    STATE.model, STATE.tokenizer = load_model_tokenizer(
        args.model_path, args.tokenizer_path
    )
    STATE.cfg["layers"] = args.layers
    STATE.cfg["k"] = args.k
    STATE.cfg["weighting"] = args.weighting
    STATE.cfg["weights_path"] = args.weights_path

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
