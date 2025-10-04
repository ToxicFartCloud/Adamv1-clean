from huggingface_hub import hf_hub_download
import os


def run(**kwargs):
    repo_id = kwargs.get("repo_id")
    filename = kwargs.get("filename")
    local_dir = kwargs.get("local_dir", "models")

    if not repo_id or not filename:
        return {"ok": False, "error": "repo_id and filename required"}

    try:
        os.makedirs(local_dir, exist_ok=True)
        path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir)
        return {"ok": True, "data": path, "error": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}
