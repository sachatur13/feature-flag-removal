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
# UTILS
# -----------------------------
def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Command failed:\n{' '.join(cmd)}\n\n{result.stderr}")
        raise RuntimeError(result.stderr)
    return result.stdout


def setup_git():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        st.stop("❌ GitHub token not found. Set GITHUB_TOKEN.")

    run(["git", "config", "--global", "user.email", "streamlit-bot@internal"])
    run(["git", "config", "--global", "user.name", "streamlit-bot"])
    run([
        "git", "remote", "set-url", "origin",
        f"https://{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    ])


def load_flags():
    with open("feature_flags.yml") as f:
        return yaml.safe_load(f)["flags"]


def create_task(flag_name):
    os.makedirs(TASK_DIR, exist_ok=True)

    task = {
        "task_type": "remove_feature_flag",
        "flag_name": flag_name,
        "requested_by": "streamlit_ui",
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    task_file = f"{TASK_DIR}/remove_{flag_name}.yml"

    with open(task_file, "w") as f:
        yaml.safe_dump(task, f)

    run(["git", "checkout", DEFAULT_BRANCH])
    run(["git", "pull", "origin", DEFAULT_BRANCH])
    run(["git", "add", task_file])
    run(["git", "commit", "-m", f"Request removal of feature flag: {flag_name}"])
    run(["git", "push", "origin", DEFAULT_BRANCH])

    return task_file

# -----------------------------
# UI
# -----------------------------
st.set_page_config(
    page_title="Feature Flag Removal",
    layout="centered"
)

st.title("🚩 Feature Flag Removal")
st.caption("Internal tool • All changes go through Pull Requests")

# Git setup
setup_git()

# Load flags
flags = load_flags()
flag_names = sorted(flags.keys())

if not flag_names:
    st.info("No feature flags found.")
    st.stop()

# Flag selection
selected_flag = st.selectbox(
    "Select a feature flag",
    flag_names
)

flag_data = flags[selected_flag]

st.divider()

# Flag details (clean, readable)
st.subheader("📌 Feature Flag Details")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Flag name**")
    st.write(selected_flag)

    st.markdown("**Owner**")
    st.write(flag_data.get("owner", "Not specified"))

with col2:
    st.markdown("**Created on**")
    st.write(flag_data.get("created_at", "Unknown"))

    if "description" in flag_data:
        st.markdown("**Description**")
        st.write(flag_data["description"])

st.divider()

# Warning / explanation
st.warning(
    "This action does **not** delete code directly.\n\n"
    "It will:\n"
    "- Record a removal request in GitHub\n"
    "- Trigger automation to open a Pull Request\n"
    "- Require review and approval before merge"
)

# Confirmation
confirm = st.checkbox("I understand and want to proceed")

if confirm:
    if st.button("🚨 Trigger Feature Flag Removal", type="primary"):
        with st.spinner("Submitting removal request..."):
            task_file = create_task(selected_flag)

        st.success("✅ Removal request submitted successfully")

        st.markdown("**Request recorded as:**")
        st.code(task_file)

        st.markdown(
            "Devin will now process this request and create a pull request "
            "for review."
        )
