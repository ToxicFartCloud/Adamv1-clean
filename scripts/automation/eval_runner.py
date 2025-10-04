import json
import os

EVAL_FILE = "eval/director_eval.jsonl"
RESULTS_DIR = "eval/results/"


def run_eval():
    """
    Replays the evaluation file and writes results.
    """
    print("Running evaluation...")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(EVAL_FILE, "r") as f:
        for line in f:
            task = json.loads(line)
            task_id = task.get("task_id")
            print(f"  - Processing task: {task_id}")
            # Placeholder for actual evaluation logic
            result = {"task_id": task_id, "status": "completed", "output": "stub"}
            with open(os.path.join(RESULTS_DIR, f"{task_id}.json"), "w") as out_f:
                json.dump(result, out_f, indent=2)
    print("Evaluation complete.")
    # Placeholder for summary and proposal generation
    print("Generating summary and proposals...")


if __name__ == "__main__":
    run_eval()
