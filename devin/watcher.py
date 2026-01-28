import os
import yaml
import subprocess

TASK_DIR = "devin_tasks"

def process_task(task_path):
    with open(task_path) as f:
        task = yaml.safe_load(f)

    if task["status"] != "pending":
        return

    print(f"Processing task: {task_path}")

    subprocess.run([
        "python",
        "devin/execute_task.py",
        task_path
    ])

def main():
    for file in os.listdir(TASK_DIR):
        if file.endswith(".yaml"):
            process_task(os.path.join(TASK_DIR, file))

if __name__ == "__main__":
    main()
