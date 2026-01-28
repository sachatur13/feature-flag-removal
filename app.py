import streamlit as st
import yaml
import os
from datetime import datetime

TASK_DIR = "devin_tasks"

st.title("🚩 Feature Flag Removal Dashboard")

with open("feature_flags.yml") as f:
    flags = yaml.safe_load(f)["flags"]

flag_name = st.selectbox(
    "Select feature flag to remove",
    list(flags.keys())
)

st.json(flags[flag_name])

confirm = st.checkbox("I understand this will create a PR")

if confirm and st.button("Remove Feature Flag"):
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

    st.success("✅ Task created. Devin will pick this up.")
    st.code(task_file)
