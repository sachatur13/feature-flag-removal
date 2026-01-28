import yaml
import sys
import subprocess
from pathlib import Path

task_file = sys.argv[1]

with open(task_file) as f:
    task = yaml.safe_load(f)

flag = task["flag_name"]
branch = f"remove-flag-{flag}"

def run(cmd):
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)

# 1. Create branch
run(["git", "checkout", "-b", branch])

# 2. Remove flag from feature_flags.yaml
flags_file = Path("feature_flags.yaml")
data = yaml.safe_load(flags_file.read_text())
data["flags"].pop(flag)
flags_file.write_text(yaml.safe_dump(data))

# 3. Remove usages (example: simple case)
run(["rg", flag, "--files-with-matches"])

# NOTE:
# Real implementation would modify files programmatically.
# This is where Devin applies judgment.

# 4. Commit changes
run(["git", "add", "."])
run(["git", "commit", "-m", f"Remove feature flag: {flag}"])

# 5. Push branch
run(["git", "push", "origin", branch])

# 6. Create PR
run([
    "gh", "pr", "create",
    "--title", f"Remove feature flag: {flag}",
    "--body", "Automated feature flag removal"
])

# 7. Mark task complete
task["status"] = "completed"
Path(task_file).write_text(yaml.safe_dump(task))
