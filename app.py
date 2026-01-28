import streamlit as st
import yaml
import os
import subprocess
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
REPO_OWNER = "sachatur13"
REPO_NAME = "feature-flag-removal"
DEFAULT_BRANCH = "main"
TASK_DIR = "devin_tasks"

# -----------------------------
# UTILITIES
# -----------------------------
def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Command failed:\n{' '.join(cmd)}\n\n{result.stderr}")
        raise RuntimeError(result.stderr)
    return result.stdout


def setup_git():
    """Configure git identity and auth for Streamlit"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        st.stop("❌ GITHUB_TOKEN not set")

    run(["git", "config", "--global", "user.email", "streamlit-bot@internal"])
    run(["git", "config", "--global", "user.name", "streamlit-bot"])

    run([
        "git", "remote", "set-url", "origin",
        f"https://{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    ])


def load_flags():
    with open("feature_flags.yaml") as f:
        return yaml.safe_load(f)["flags"]


def create_devin_task(flag_name):
    os.makedirs(TASK_DIR, exist_ok=True)

    task = {
        "task_type": "remove_feature_flag",
        "flag_name": flag_name,
        "requested_by": "streamlit_ui",
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    task_file = f"{TASK_DIR}/remove_{flag_name}.yaml"

    with open(task_file, "w") as f:
        yaml.safe_dump(task, f)

    run(["git", "checkout", DEFAULT_BRANCH])
    run(["git", "pull", "origin", DEFAULT_BRANCH])
    run(["git", "add", task_file])
    run(["git", "commit", "-m", f"Request removal of feature flag: {flag_name}"])
    run(["git", "push", "origin", DEFAULT_BRANCH])

    return task_file


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Feature Flag Removal", layout="centered")

st.title("🚩 Feature Flag Removal Dashboard")
st.caption("Internal tool – all changes go through a Pull Request")

# One-time git setup
try:
    setup_git()
except Exception:
    st.stop()

# Load flags
try:
    flags = load_flags()
except FileNotFoundError:
    st.stop("❌ feature_flags.yaml not found in repo")

flag_names = list(flags.keys())

if not flag_names:
    st.info("No feature flags found.")
    st.stop()

selected_flag = st.selectbox(
    "Select a feature flag to remove",
    flag_names
)

st.subheader("Flag Details")
st.json(flags[selected_flag])

st.warning(
    "⚠️ This action will:\n"
    "- Create a removal request in the repo\n"
    "- Trigger automation to open a Pull Request\n"
    "- Require human review before merge\n\n"
    "**Nothing is deleted directly.**"
)

confirm = st.checkbox("I understand and want to proceed")

if confirm:
    if st.button("🚨 Trigger Feature Flag Removal"):
        try:
            task_file = create_devin_task(selected_flag)
            st.success("✅ Removal request created successfully!")
            st.markdown("**Task file committed:**")
            st.code(task_file)
            st.markdown(
                "Devin (or another automation) will now process this task "
                "and create a Pull Request."
            )
        except Exception:
            st.stop()
