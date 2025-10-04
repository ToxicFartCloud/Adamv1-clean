# SLED Pilot (Offline)

**What is SLED?**  
"SLED" here means combining **S**ignals across **L**ayers for **E**mission (token) **D**ecoding. Instead of using only the final layer's logits, we take hidden states from multiple layers, map each through a small linear head to vocab space, and **mix** these logits to pick the next token. This pilot provides a lightweight, offline approximation to try the idea on local Hugging Face models.

## Run the server
```bash
python sidecars/sled/app.py --model_path /models/your-local-model --layers last_k --k 8 --weighting uniform
```

## Quick curl test
```bash
curl -s http://127.0.0.1:8010/generate -X POST \
  -H 'Content-Type: application/json' \
  -d '{"mode":"baseline","prompt":"Hello"}' | jq
```

## Optional: calibrate per-layer weights
Provide a small JSONL at `eval/items.jsonl` (included). Then:
```bash
curl -s http://127.0.0.1:8010/calibrate -X POST \
  -H 'Content-Type: application/json' \
  -d '{"path":"eval/items.jsonl"}' | jq
```
This learns a **layer mixing vector** (not projection matrices) via simple ridge regression and saves `sled_weights.npz`. Switch the server `--weighting learned` to use it.

## Generate (SLED vs baseline)
```bash
curl -s http://127.0.0.1:8010/generate -X POST \
  -H 'Content-Type: application/json' \
  -d '{"mode":"sled","prompt":"Write a haiku about snow.", "gen_args":{"max_new_tokens":64}}' | jq
```
Change `"mode":"baseline"` to compare.

## Offline notes
- Models/tokenizers must already be on disk. We load with `local_files_only=True`.
- Choosing `last_k`: start with `k=8` on mid-sized models. On smaller models, try `k=4`. For more signal, use `all` layers, but it’s slower.
- CPU/GPU auto-detected; projection heads are created on-the-fly each run.
