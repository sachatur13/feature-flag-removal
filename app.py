import streamlit as st
import yaml
import os
import subprocess
import requests
import time
from datetime import datetime

# ==================================================
# CONFIG
# ==================================================
REPO_OWNER = "sachatur13"
REPO_NAME = "feature-flag-removal"
DEFAULT_BRANCH = "main"
TASK_DIR = "devin_tasks"
POLL_INTERVAL_SECONDS = 5

# ==================================================
# SESSION STATE
# ==================================================
if "waiting_for_pr" not in st.session_state:
    st.session_state.waiting_for_pr = False

if "triggered_at" not in st.session_state:
    st.session_state.triggered_at = None

if "last_flag_triggered" not in st.session_state:
    st.session_state.last_flag_triggered = None

# ==================================================
# UTILITIES
# ==================================================
def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(
            f"Command failed:\n{' '.join(cmd)}\n\n{result.stderr}"
        )
        raise RuntimeError(result.stderr)
    return result.stdout


def setup_git():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        st.stop("❌ GITHUB_TOKEN not found. Please configure it.")

    run(["git", "config", "--global", "user.email", "streamlit-bot@internal"])
    run(["git", "config", "--global", "user.name", "streamlit-bot"])
    run([
        "git", "remote", "set-url", "origin",
        f"https://{token}@github.com/{REPO_OWNER}/{REPO_NAME}.git"
    ])


def load_flags():
    with open("feature_flags.yml") as f:
        return yaml.safe_load(f)["flags"]


def create_removal_task(flag_name):
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


def fetch_recent_prs(limit=10):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    params = {"state": "all", "per_page": limit}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# ==================================================
# UI
# ==================================================
st.set_page_config(
    page_title="Feature Flag Removal",
    layout="centered"
)

st.title("🚩 Feature Flag Removal Dashboard")
st.caption(
    "Internal tool • All changes are reviewed via GitHub Pull Requests"
)

# One-time git setup
setup_git()

# ==================================================
# FEATURE FLAGS
# ==================================================
flags = load_flags()
flag_names = sorted(flags.keys())

if not flag_names:
    st.info("No feature flags found.")
    st.stop()

selected_flag = st.selectbox(
    "Select a feature flag",
    flag_names
)

flag = flags[selected_flag]

st.divider()
st.subheader("📌 Feature Flag Details")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Flag name**")
    st.write(selected_flag)

    st.markdown("**Owner**")
    st.write(flag.get("owner", "Not specified"))

with col2:
    st.markdown("**Created on**")
    st.write(flag.get("created_at", "Unknown"))

    if flag.get("description"):
        st.markdown("**Description**")
        st.write(flag["description"])

# ==================================================
# TRIGGER REMOVAL
# ==================================================
st.divider()

st.warning(
    "This action does **not** delete code directly.\n\n"
    "It will:\n"
    "- Record a removal request in GitHub\n"
    "- Trigger automated cleanup by Devin\n"
    "- Create a Pull Request for human review"
)

confirm = st.checkbox("I understand and want to proceed")

if confirm:
    if st.button("🚨 Trigger Feature Flag Removal", type="primary"):
        with st.spinner("Submitting removal request to GitHub..."):
            task_file = create_removal_task(selected_flag)

        st.session_state.waiting_for_pr = True
        st.session_state.triggered_at = time.time()
        st.session_state.last_flag_triggered = selected_flag

        st.success("✅ Removal request submitted")
        st.markdown("**Request recorded as:**")
        st.code(task_file)

        time.sleep(1)
        st.rerun()

# ==================================================
# PR MONITORING (AUTO REFRESH)
st.divider()
st.subheader("📄 Feature Flag Removal Pull Requests (Open)")

try:
    prs = fetch_recent_prs(limit=10)
    pr_found = False

    for pr in prs:
        # ✅ only open PRs
        if pr["state"] != "open":
            continue

        title = pr["title"]

        # only feature flag PRs
        if "Remove feature flag" not in title:
            continue

        status = pr["state"].capitalize()
        author = pr["user"]["login"]
        created = pr["created_at"][:10]
        url = pr["html_url"]

        if (
            st.session_state.last_flag_triggered
            and f"Remove feature flag: {st.session_state.last_flag_triggered}" in title
        ):
            pr_found = True

        with st.container():
            st.markdown(f"**{title}**")
            st.write(f"Status: {status}")
            st.write(f"Created by: {author} on {created}")
            st.markdown(f"[View Pull Request →]({url})")
            st.divider()

    # ----------------------------------------------
    # Background activity indicator
    # ----------------------------------------------
    if st.session_state.waiting_for_pr:
        elapsed = int(time.time() - st.session_state.triggered_at)

        if pr_found:
            st.session_state.waiting_for_pr = False
            st.success("🎉 Pull request created by Devin")
        else:
            st.info(f"⏳ Devin is working… ({elapsed}s elapsed)")
            time.sleep(POLL_INTERVAL_SECONDS)
            st.rerun()

except Exception:
    st.error("Unable to load pull requests from GitHub.")
