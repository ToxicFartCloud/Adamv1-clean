# Minimal SLED decoding pilot for local HF Transformers models.
# Offline-only: do not attempt any downloads. All paths must be local.
# Author: Adam Project SLED Pilot
#
# This module exposes:
#   - generate_baseline(model, tokenizer, prompt, max_new_tokens=256, temperature=0.7, top_p=0.95)
#   - generate_sled(model, tokenizer, prompt, max_new_tokens=256, layers="last_k", k=8,
#                   weighting="uniform", weights_path="sled_weights.npz",
#                   temperature=0.7, top_p=0.95)
#   - fit_layer_weights(model, tokenizer, jsonl_path, layers="last_k", k=8, alpha=1.0,
#                       max_items=200, max_new_tokens=32, out_path="sled_weights.npz")
#
# Approach:
# For SLED ("use all layers"), we forward with output_hidden_states=True and at each decode
# step we take the chosen hidden layer states for the *last token*, optionally pass them
# through the model's final norm (if present), project each to the vocab using the tied
# output head, and blend the per-layer logits with a weighting strategy:
#   - "uniform": equal weights
#   - "depth_softmax": softmax over (1..L); deeper layers get slightly higher weights
#   - "learned": load a vector of per-layer weights from sled_weights.npz if available.
#
# Notes:
# - We never train the model itself. The optional calibration only fits a mixing vector.
# - CPU/GPU agnostic. We auto-detect device.

from typing import List, Tuple, Dict, Any, Optional
import json
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def _get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _nucleus_sample(logits: torch.Tensor, top_p: float, temperature: float) -> int:
    # logits: [vocab_size]
    if temperature <= 0:
        # Greedy
        return int(torch.argmax(logits).item())
    # Temperature scale
    logits = logits / max(1e-6, temperature)
    probs = F.softmax(logits, dim=-1)
    # Sort by prob desc
    sorted_probs, sorted_idx = torch.sort(probs, descending=True)
    cumsum = torch.cumsum(sorted_probs, dim=-1)
    cutoff = cumsum > top_p
    # Keep smallest set that sums to >= top_p
    cutoff_idx = torch.where(cutoff)[0]
    if cutoff_idx.numel() == 0:
        keep = sorted_probs
        keep_idx = sorted_idx
    else:
        last = cutoff_idx[0].item()
        keep = sorted_probs[: last + 1]
        keep_idx = sorted_idx[: last + 1]
    keep = keep / keep.sum()
    choice = torch.multinomial(keep, num_samples=1)
    return int(keep_idx[choice].item())


def _select_layer_indices(num_layers: int, layers: str, k: int) -> List[int]:
    if layers == "all":
        return list(range(num_layers))
    # default: last_k
    k = max(1, min(k, num_layers))
    return list(range(num_layers - k, num_layers))


def _depth_weights(n: int) -> torch.Tensor:
    # softmax over depth scores 1..n (higher depth => higher weight)
    scores = torch.arange(1, n + 1, dtype=torch.float32)
    return torch.softmax(scores, dim=0)


def _load_learned_weights(
    n: int, weights_path: str = "sled_weights.npz", chosen: Optional[List[int]] = None
) -> Optional[torch.Tensor]:
    try:
        if os.path.exists(weights_path):
            data = np.load(weights_path)
            if "layer_weights" in data:
                w = torch.tensor(data["layer_weights"], dtype=torch.float32)
                if w.numel() == n:
                    saved_layers = data.get("chosen")
                    if chosen is not None and saved_layers is not None:
                        try:
                            if len(saved_layers) != n or any(
                                int(a) != int(b)
                                for a, b in zip(saved_layers.tolist(), chosen)
                            ):
                                return None
                        except Exception:
                            return None
                    if w.sum().abs() > 0:
                        w = w / w.sum()
                    else:
                        w = torch.ones(n) / n
                    return w
    except Exception:
        pass
    return None


def _get_output_head(model) -> nn.Module:
    if hasattr(model, "lm_head") and getattr(model, "lm_head") is not None:
        return model.lm_head
    if hasattr(model, "get_output_embeddings"):
        head = model.get_output_embeddings()
        if head is not None:
            return head
    raise ValueError(
        "Model does not expose an output head compatible with logits projection."
    )


def _find_norm_module(model) -> Optional[nn.Module]:
    candidate_paths = [
        ("model", "norm"),
        ("model", "final_layer_norm"),
        ("model", "ln_f"),
        ("model", "layer_norm"),
        ("model", "norm_f"),
        ("model", "gpt_neox", "final_layer_norm"),
        ("model", "decoder", "layer_norm"),
        ("model", "decoder", "final_layer_norm"),
        ("transformer", "ln_f"),
        ("transformer", "final_layer_norm"),
        ("transformer", "norm_f"),
        ("decoder", "layer_norm"),
        ("decoder", "final_layer_norm"),
        ("final_layer_norm",),
        ("ln_f",),
    ]
    for path in candidate_paths:
        module = model
        for attr in path:
            module = getattr(module, attr, None)
            if module is None:
                break
        if module is not None:
            return module
    return None


def _project_layers_to_logits(
    hidden_states: Tuple[torch.Tensor, ...],
    chosen: List[int],
    head: nn.Module,
    norm_module: Optional[nn.Module],
    gather_id: Optional[int] = None,
) -> List[Any]:
    outputs: List[Any] = []
    for layer_idx in chosen:
        h = hidden_states[layer_idx + 1][:, -1:, :]
        if norm_module is not None:
            h = norm_module(h)
        logits = head(h)
        if gather_id is not None:
            outputs.append(float(logits[0, 0, gather_id].item()))
        else:
            outputs.append(logits.squeeze(0).squeeze(0))
    return outputs


def _combine_layer_logits(
    layer_logits: List[torch.Tensor], weighting: str
) -> torch.Tensor:
    # layer_logits: list of [vocab_size] tensors
    n = len(layer_logits)
    if n == 1:
        return layer_logits[0]

    if weighting == "depth_softmax":
        w = _depth_weights(n)
    elif weighting == "learned":
        # if learned missing, fallback to uniform handled by caller via passing 'uniform'
        w = None
    else:
        w = torch.ones(n) / n

    if w is None:
        # "learned" requested but caller couldn't load -> fallback uniform
        w = torch.ones(n) / n

    # Stack and weight-sum
    L = torch.stack(layer_logits, dim=0)  # [n, vocab]
    w = w.to(device=L.device, dtype=L.dtype).unsqueeze(-1)
    return (w * L).sum(dim=0)


@torch.no_grad()
def generate_baseline(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.95,
) -> str:
    device = _get_device()
    model = model.to(device)
    model.eval()

    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    prompt_len = input_ids.size(1)
    # Simple sampling loop to avoid internet-dependence of generate()
    # (also ensures we can hook hidden states similarly if needed)
    past = None
    out_ids = input_ids.clone()
    for _ in range(max_new_tokens):
        step_input = out_ids[:, -1:] if past is not None else out_ids
        outputs = model(
            input_ids=step_input,
            past_key_values=past,
            use_cache=True,
            output_hidden_states=False,
        )
        logits = outputs.logits[:, -1, :].squeeze(0)
        past = outputs.past_key_values
        next_id = _nucleus_sample(logits, top_p=top_p, temperature=temperature)
        out_ids = torch.cat([out_ids, torch.tensor([[next_id]], device=device)], dim=1)
        if tokenizer.eos_token_id is not None and next_id == tokenizer.eos_token_id:
            break
    completion_ids = out_ids[0, prompt_len:].tolist()
    return tokenizer.decode(completion_ids, skip_special_tokens=True)


@torch.no_grad()
def generate_sled(
    model,
    tokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    layers: str = "last_k",
    k: int = 8,
    weighting: str = "uniform",
    weights_path: str = "sled_weights.npz",
    temperature: float = 0.7,
    top_p: float = 0.95,
) -> Tuple[str, Dict[str, Any]]:
    device = _get_device()
    model = model.to(device)
    model.eval()

    # Prepare inputs
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    prompt_len = input_ids.size(1)

    # Discover layer count & dims by a dry run with hidden states
    dry = model(input_ids=input_ids, use_cache=True, output_hidden_states=True)
    all_h = dry.hidden_states  # tuple: [emb] + L layers => len = L+1
    num_layers = len(all_h) - 1

    chosen = _select_layer_indices(num_layers, layers, k)
    k_eff = len(chosen)

    lm_head = _get_output_head(model)
    norm_module = _find_norm_module(model)

    weighting_requested = weighting
    weighting_applied = weighting_requested
    learned_w = None
    if weighting_requested == "learned":
        learned_w = _load_learned_weights(
            k_eff, weights_path=weights_path, chosen=chosen
        )
        if learned_w is None:
            weighting_applied = "uniform"
        else:
            learned_w = learned_w.to(device)

    past = dry.past_key_values
    out_ids = input_ids.clone()

    for _ in range(max_new_tokens):
        # Forward last token with cache and request hidden states
        outputs = model(
            input_ids=out_ids[:, -1:],
            past_key_values=past,
            use_cache=True,
            output_hidden_states=True,
        )
        past = outputs.past_key_values
        hs = outputs.hidden_states  # len = L+1 (index 0 is embeddings)
        # Take last token across chosen layers, project to vocab
        layer_logits = _project_layers_to_logits(hs, chosen, lm_head, norm_module)

        # Combine per weighting
        if weighting_applied == "learned" and learned_w is not None:
            Lstack = torch.stack(layer_logits, dim=0)  # [k, vocab]
            logits = (
                learned_w.to(Lstack.device, dtype=Lstack.dtype).unsqueeze(-1) * Lstack
            ).sum(dim=0)
        else:
            logits = _combine_layer_logits(layer_logits, weighting_applied)

        next_id = _nucleus_sample(logits, top_p=top_p, temperature=temperature)
        out_ids = torch.cat([out_ids, torch.tensor([[next_id]], device=device)], dim=1)
        if tokenizer.eos_token_id is not None and next_id == tokenizer.eos_token_id:
            break

    completion_ids = out_ids[0, prompt_len:].tolist()
    text = tokenizer.decode(completion_ids, skip_special_tokens=True)
    if weighting_requested == "learned" and learned_w is None:
        weights_info = "learned_missing_fallback_uniform"
    elif weighting_applied == "learned":
        weights_info = "learned"
    else:
        weights_info = weighting_applied
    meta = {
        "layers": layers,
        "k": k_eff,
        "chosen_indices": chosen,
        "weighting_requested": weighting_requested,
        "weighting_applied": weighting_applied,
        "weights_info": weights_info,
        "weights_path": weights_path if weighting_applied == "learned" else None,
    }
    return text, meta


@torch.no_grad()
def _collect_step_features(
    model,
    tokenizer,
    prompt: str,
    target: str,
    chosen: List[int],
    head: nn.Module,
    norm_module: Optional[nn.Module],
    max_new_tokens: int = 32,
    device=None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (X, y) where X is [steps, k] per-layer logits for the correct next-token,
    and y is [steps] the baseline logits for the same correct token. Used for ridge fit.
    """
    device = device or _get_device()
    # Encode concatenated prompt+target to produce targets step-by-step
    pt_ids = tokenizer(prompt + target, return_tensors="pt").input_ids.to(device)
    prompt_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    # We'll decode from prompt_ids to match target tokens sequentially
    out_ids = prompt_ids.clone()
    past = None
    X_rows = []
    y_rows = []

    # We will only look at up to max_new_tokens of the actual target tokens
    target_ids = pt_ids[:, prompt_ids.size(1) :][:, :max_new_tokens]
    steps = target_ids.size(1)

    for t in range(steps):
        outputs = model(
            input_ids=out_ids[:, -1:] if past is not None else out_ids,
            past_key_values=past,
            use_cache=True,
            output_hidden_states=True,
        )
        past = outputs.past_key_values
        hs = outputs.hidden_states  # list length L+1
        baseline_logits = outputs.logits[:, -1, :].squeeze(0)  # [vocab]
        correct_id = int(target_ids[0, t].item())

        # Per-layer projected logit for the correct token
        layer_vals = _project_layers_to_logits(
            hs, chosen, head, norm_module, gather_id=correct_id
        )

        X_rows.append(layer_vals)
        y_rows.append(baseline_logits[correct_id].item())

        # Teacher-forcing: append the *true* token to continue alignment
        out_ids = torch.cat([out_ids, target_ids[:, t : t + 1]], dim=1)

    X = np.asarray(X_rows, dtype=np.float32)  # [steps, k]
    y = np.asarray(y_rows, dtype=np.float32)  # [steps]
    return X, y


def fit_layer_weights(
    model,
    tokenizer,
    jsonl_path: str,
    layers: str = "last_k",
    k: int = 8,
    alpha: float = 1.0,
    max_items: int = 200,
    max_new_tokens: int = 32,
    out_path: str = "sled_weights.npz",
) -> Dict[str, Any]:
    """Tiny ridge regression fit for per-layer mixing weights.
    We reuse the model's output head to project hidden states from selected layers to vocab
    space and collect features X (per-layer logits for the correct next token) and targets y
    (baseline logits for the same token). Then solve a ridge regression to obtain
        w = (X^T X + alpha I)^{-1} X^T y
    We normalize w to sum to 1 (clip >=0) and persist as numpy array 'layer_weights'.
    """
    device = _get_device()
    model = model.to(device).eval()

    # Dry run to discover layer count
    dummy_ids = tokenizer("hi", return_tensors="pt").input_ids.to(device)
    dry = model(input_ids=dummy_ids, use_cache=True, output_hidden_states=True)
    num_layers = len(dry.hidden_states) - 1

    chosen = _select_layer_indices(num_layers, layers, k)
    if not chosen:
        return {"ok": False, "error": "No layers selected for calibration."}

    lm_head = _get_output_head(model)
    norm_module = _find_norm_module(model)

    # Stream JSONL and accumulate X,y up to limits
    total_X = []
    total_y = []
    items_used = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            prompt = item.get("prompt", "")
            target = item.get("answer", "") or item.get("completion", "")
            if not prompt or not target:
                continue
            X, y = _collect_step_features(
                model,
                tokenizer,
                prompt,
                target,
                chosen,
                lm_head,
                norm_module,
                max_new_tokens=max_new_tokens,
                device=device,
            )
            if X.size == 0:
                continue
            total_X.append(X)
            total_y.append(y)
            items_used += 1
            if items_used >= max_items:
                break

    if not total_X:
        return {"ok": False, "error": "No usable calibration items found."}

    X = np.concatenate(total_X, axis=0)  # [N, k]
    y = np.concatenate(total_y, axis=0)  # [N]

    # Ridge: (X^T X + alpha I)^{-1} X^T y
    k_eff = X.shape[1]
    XtX = X.T @ X
    XtX += alpha * np.eye(k_eff, dtype=np.float32)
    Xty = X.T @ y
    try:
        w = np.linalg.solve(XtX, Xty)
    except np.linalg.LinAlgError:
        w = np.linalg.lstsq(XtX, Xty, rcond=None)[0]

    # Make non-negative and normalize
    w = np.maximum(w, 0.0)
    s = w.sum()
    if s <= 0:
        w = np.ones_like(w) / len(w)
    else:
        w = w / s

    np.savez(
        out_path,
        layer_weights=w.astype(np.float32),
        chosen=np.array(chosen, dtype=np.int32),
    )
    return {
        "ok": True,
        "k": k_eff,
        "out_path": out_path,
        "items_used": items_used,
        "steps_collected": int(X.shape[0]),
    }
