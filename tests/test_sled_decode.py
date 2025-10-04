import os
import numpy as np
import torch
import pytest

# Import from sidecars path
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sidecars", "sled"))
)
from sled_decode import (
    _combine_layer_logits,
    _load_learned_weights,
    _select_layer_indices,
)


def test_combine_uniform_and_depth():
    logits = [torch.zeros(10), torch.ones(10), torch.arange(10.0)]
    out_u = _combine_layer_logits(logits, "uniform")
    out_d = _combine_layer_logits(logits, "depth_softmax")
    assert out_u.shape == torch.Size([10])
    assert out_d.shape == torch.Size([10])
    # depth_softmax should put more weight on deeper layers -> last layer gets highest coefficient
    assert torch.argmax(out_d) >= torch.argmax(out_u)


def test_learned_fallback(tmp_path):
    # Missing file -> returns None inside loader, combine falls back to uniform in caller.
    w = _load_learned_weights(3, str(tmp_path / "missing.npz"))
    assert w is None


def test_learned_mismatch_layers(tmp_path):
    path = tmp_path / "weights.npz"
    np.savez(
        path,
        layer_weights=np.array([0.5, 0.5], dtype=np.float32),
        chosen=np.array([0, 1], dtype=np.int32),
    )
    w = _load_learned_weights(2, str(path), chosen=[1, 2])
    assert w is None


def test_select_last_k():
    assert _select_layer_indices(12, "last_k", 4) == list(range(8, 12))
    assert _select_layer_indices(3, "last_k", 8) == [0, 1, 2]
    assert _select_layer_indices(5, "all", 8) == [0, 1, 2, 3, 4]


@pytest.mark.skipif(
    os.environ.get("MODEL_DIR") is None,
    reason="MODEL_DIR not set; skipping local-model test",
)
def test_hidden_layer_capture_with_local_model():
    # Smoke test: ensure model can return hidden states without downloads.
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_path = os.environ["MODEL_DIR"]
    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    mdl = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True)
    ids = tok("hello", return_tensors="pt").input_ids
    out = mdl(input_ids=ids, output_hidden_states=True, use_cache=True)
    assert isinstance(out.hidden_states, tuple)
    assert len(out.hidden_states) > 1
