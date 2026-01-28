import streamlit as st
import yaml
from backend.devin_task import submit_flag_removal

st.set_page_config(page_title="Feature Flag Removal")

st.title("🚩 Feature Flag Removal Dashboard")

with open("feature_flags.yml") as f:
    data = yaml.safe_load(f)

flags = data["flags"]
flag_names = list(flags.keys())

selected_flag = st.selectbox(
    "Select feature flag to remove",
    flag_names
)

st.subheader("Flag Details")
st.json(flags[selected_flag])

st.warning(
    "This action will:\n"
    "- Remove the feature flag\n"
    "- Remove all code usage\n"
    "- Create a GitHub Pull Request\n\n"
    "This cannot be undone."
)

confirm = st.checkbox("I understand and want to continue")

if confirm and st.button("🚨 Remove Feature Flag"):
    submit_flag_removal(selected_flag)
    st.success("Devin task started. PR will be created.")
