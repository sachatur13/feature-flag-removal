def submit_flag_removal(flag_name: str):
    """
    This function delegates all engineering work to Devin.
    """

    devin_instructions = f"""
You are an autonomous software engineer.

OBJECTIVE:
Safely remove the feature flag `{flag_name}`.

STEPS:
1. Create a new git branch named: remove-flag-{flag_name}

2. Edit feature_flags.yaml:
   - Remove `{flag_name}` from the flags list

3. Search the entire repository for `{flag_name}`

4. For each usage:
   - Remove conditional logic
   - Keep the default behavior
   - Do NOT delete business logic

5. Update or remove tests related to `{flag_name}`

6. Run all tests or scripts if available

7. If tests fail, stop and report failure

8. Push the branch to GitHub

9. Create a Pull Request:
   - Title: Remove feature flag: {flag_name}
   - Description:
     - Summary of changes
     - Files modified
     - Test status

RULES:
- Do NOT merge the PR
- Do NOT remove unclear logic
- Leave TODO comments if uncertain
"""

    # In real Devin integration, this is where the task is sent.
    print("=== DEVIN TASK STARTED ===")
    print(devin_instructions)
