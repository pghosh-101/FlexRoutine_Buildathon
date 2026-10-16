# FlexRoutine Planner

A small Streamlit app for Build-a-thon Option 1: maintain habits when schedules change.

## Setup

1. Make sure \`.env\` is a file in this folder, not a folder and not \`.env.txt\`.
2. Put the replacement Claude key in \`.env\`:

   ANTHROPIC_API_KEY=your_key_here

3. Open PowerShell in this folder and run:

   py -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python -m streamlit run app.py

The app reads the reusable FlexRoutine Planner skill from \`.agents/skills\` or \`skills\`, sends the student's habits and available time to Claude, and validates that the returned routine never exceeds the available minutes.

Never commit or share \`.env\`. The \`.gitignore\` file is configured to exclude it.

