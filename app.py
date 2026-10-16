import html
import json
import os
from pathlib import Path
from urllib.parse import quote

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
SKILL_PATHS = [
    PROJECT_ROOT / ".agents" / "skills" / "flexroutine-planner" / "SKILL.md",
    PROJECT_ROOT / "skills" / "flexroutine-planner" / "SKILL.md",
]


def safe_text(value: object) -> str:
    """Escape user/model text before placing it in a styled HTML card."""
    return html.escape(str(value or ""))


def build_share_text(plan: dict) -> str:
    """Create a friendly, non-technical summary for email or text drafts."""
    lines = [
        "FlexRoutine Planner — Today's adjusted routine",
        "",
        f"Planned: {plan.get('total_minutes', 0)} minutes",
        f"Available: {plan.get('available_minutes', 0)} minutes",
        f"Remaining: {plan.get('remaining_minutes', 0)} minutes",
        "",
        "Routine:",
    ]
    routine = plan.get("adjusted_routine", [])
    if routine:
        for item in routine:
            version = "shortened" if item.get("version") != "full" else "full"
            lines.append(f"- {item.get('habit', 'Habit')}: {item.get('minutes', 0)} min ({version})")
    else:
        lines.append("- No habits fit in the available time today.")

    skipped = plan.get("skipped_habits", [])
    if skipped:
        lines.extend(["", "Skipped for today:"])
        for item in skipped:
            lines.append(f"- {item.get('habit', 'Habit')}")

    explanation = str(plan.get("explanation", "")).strip()
    if explanation:
        lines.extend(["", explanation])
    return "\n".join(lines)


def load_skill_instructions() -> str:
    """Load the reusable FlexRoutine Planner skill from the project."""
    for path in SKILL_PATHS:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return "Use the user's priorities, fit the routine to available minutes, and return JSON only."


def extract_json(text: str) -> dict:
    """Accept JSON returned directly or inside a Markdown code fence."""
    cleaned = text.strip()
    fence = chr(96) * 3
    if cleaned.startswith(fence):
        cleaned = cleaned.removeprefix(fence).removeprefix("json").strip()
        cleaned = cleaned.removesuffix(fence).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Claude did not return a JSON object.")
    return json.loads(cleaned[start : end + 1])


def validate_plan(plan: dict, available_minutes: int) -> None:
    """Enforce the app's safety rule even if the model makes a mistake."""
    if plan.get("status") != "ok":
        return
    routine = plan.get("adjusted_routine", [])
    total = sum(int(item.get("minutes", 0)) for item in routine)
    if total > available_minutes:
        raise ValueError("The returned routine exceeds the available time.")
    if int(plan.get("total_minutes", -1)) != total:
        raise ValueError("The returned total does not match the routine.")
    if int(plan.get("available_minutes", -1)) != available_minutes:
        raise ValueError("The returned available time does not match the input.")


def request_json(client: Anthropic, system_prompt: str, user_message: str) -> dict:
    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    response_text = "".join(
        block.text for block in message.content if getattr(block, "type", "") == "text"
    )
    return extract_json(response_text)


def ask_claude(available_minutes: int, schedule_change: str, habits: list[dict]) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing from .env.")

    client = Anthropic(api_key=api_key)
    user_input = {
        "available_minutes": available_minutes,
        "schedule_change": schedule_change,
        "habits": habits,
        "preferences": {"order_ties_by": "original input order"},
    }
    system_prompt = f"""You are the FlexRoutine Planner agent.
Follow the reusable skill instructions below exactly.

<reusable_skill>
{load_skill_instructions()}
</reusable_skill>

Return JSON only. Do not include Markdown fences or extra commentary outside the JSON.
"""
    first_error = None
    draft = None
    try:
        draft = request_json(client, system_prompt, json.dumps(user_input))
        validate_plan(draft, available_minutes)
        return draft
    except ValueError as error:
        first_error = str(error)

    correction_request = {
        "original_input": user_input,
        "first_draft": draft,
        "validation_issue": first_error,
        "instruction": (
            "Correct the draft using the reusable skill. Shorten or skip lower-priority habits "
            "as needed. Recalculate every total. Return a valid JSON object only, and never exceed "
            "available_minutes."
        ),
    }
    corrected = request_json(client, system_prompt, json.dumps(correction_request))
    validate_plan(corrected, available_minutes)
    return corrected


st.set_page_config(page_title="FlexRoutine Planner", page_icon="🗓️", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #f7f9fc; }
    [data-testid="stHeader"] { background: rgba(247, 249, 252, 0.85); }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        font-family: "Aptos", "Inter", "Segoe UI", system-ui, -apple-system, sans-serif !important;
    }
    h1, h2, h3, h4 {
        font-family: "Aptos Display", "Aptos", "Inter", "Segoe UI", sans-serif !important;
        letter-spacing: -0.025em;
        font-weight: 750 !important;
        color: #172554;
    }
    p, li, label, [data-testid="stMetricLabel"] {
        letter-spacing: 0.005em;
    }
    strong, b { font-weight: 750; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #172554 0%, #1e3a8a 55%, #2563eb 100%);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p { color: #eef2ff !important; }
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {
        background: #ffffff !important; color: #172554 !important;
        border-radius: 10px !important;
    }
    .hero {
        padding: 2rem 2.2rem; margin: 0 0 1.5rem 0; border-radius: 24px;
        background: linear-gradient(120deg, #172554, #2563eb 62%, #38bdf8);
        color: white; box-shadow: 0 16px 35px rgba(37, 99, 235, 0.20);
    }
    .hero-kicker { text-transform: uppercase; letter-spacing: .14em; font-size: .75rem; opacity: .78; }
    .hero-title { font-size: 2.35rem; font-weight: 800; margin: .25rem 0 .35rem 0; }
    .hero-subtitle { font-size: 1.05rem; opacity: .9; margin: 0; }
    .section-kicker { color: #2563eb; text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; font-weight: 800; margin-top: .8rem; }
    .routine-card {
        background: white; border: 1px solid #e5e7eb; border-left: 6px solid #2563eb;
        border-radius: 14px; padding: 1rem 1.1rem; margin: .6rem 0;
        box-shadow: 0 5px 15px rgba(15, 23, 42, .05);
    }
    .routine-card.shortened { border-left-color: #f59e0b; }
    .routine-name { font-weight: 800; color: #172554; font-size: 1.02rem; }
    .routine-meta { color: #64748b; font-size: .83rem; margin-top: .25rem; }
    .time-pill {
        display: inline-block; background: #dbeafe; color: #1d4ed8; border-radius: 999px;
        padding: .3rem .7rem; font-weight: 800; white-space: nowrap;
    }
    .short-pill { background: #fef3c7; color: #b45309; }
    .skip-card {
        background: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px;
        padding: .85rem 1rem; margin: .55rem 0; color: #7c2d12;
    }
    [data-testid="stMetric"] { background: white; border: 1px solid #e5e7eb; padding: .8rem; border-radius: 14px; box-shadow: 0 5px 15px rgba(15, 23, 42, .04); }
    .stButton > button { border-radius: 12px; font-weight: 800; min-height: 3rem; }
    </style>
    <div class="hero">
        <div class="hero-kicker">Adaptive routine planner</div>
        <div class="hero-title">FlexRoutine Planner</div>
        <p class="hero-subtitle">Keep the habits that matter—even when the schedule changes.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("🧭 Build your plan")
    st.caption("Tell us what changed and how much time you have. Claude will protect your highest priorities first.")
    st.markdown("---")
    st.subheader("Today's constraints")
    available_minutes = st.number_input(
        "Minutes available",
        min_value=0,
        value=45,
        step=5,
        help="The routine will never be longer than this number.",
    )
    schedule_change = st.text_area(
        "What changed?",
        value="I have a longer work shift today.",
        help="For example: class ran late, an appointment was added, or a shift changed.",
    )
    habit_count = st.number_input("Number of habits", min_value=1, max_value=8, value=4, step=1)

st.markdown('<div class="section-kicker">Step 1 · Your inputs</div>', unsafe_allow_html=True)
st.subheader("Your habits")
st.write("Use priority labels such as **essential**, **important**, or **optional**.")

defaults = [
    ("Study review", "essential", 30, 10, "Prepare for tomorrow's quiz"),
    ("Exercise", "important", 30, 10, "A walk is an acceptable shortened version"),
    ("Meditation", "important", 10, 3, ""),
    ("Read for fun", "optional", 20, 5, ""),
]
priority_options = ["essential", "important", "optional"]

habits: list[dict] = []
for index in range(int(habit_count)):
    default = defaults[index] if index < len(defaults) else ("", "optional", 10, 5, "")
    with st.expander(f"Habit {index + 1}", expanded=True):
        col1, col2, col3, col4 = st.columns([2.2, 1.2, 1, 1])
        name = col1.text_input("Habit name", value=default[0], key=f"name_{index}")
        priority = col2.selectbox(
            "Priority",
            options=priority_options,
            index=priority_options.index(default[1]) if default[1] in priority_options else 2,
            format_func=lambda option: option.capitalize(),
            key=f"priority_{index}",
        )
        full_minutes = col3.number_input(
            "Full minutes", min_value=1, value=default[2], step=1, key=f"full_{index}"
        )
        minimum_minutes = col4.number_input(
            "Minimum minutes", min_value=0, value=default[3], step=1, key=f"minimum_{index}"
        )
        details = st.text_input(
            "Details or constraints (optional)", value=default[4], key=f"details_{index}"
        )
        habits.append(
            {
                "name": name.strip(),
                "priority": priority.strip(),
                "full_minutes": int(full_minutes),
                "minimum_minutes": int(minimum_minutes),
                "details": details.strip(),
            }
        )

if st.button("Adjust my routine", type="primary", use_container_width=True):
    invalid = [
        habit["name"] or f"Habit {index + 1}"
        for index, habit in enumerate(habits)
        if not habit["name"]
        or not habit["priority"]
        or habit["minimum_minutes"] > habit["full_minutes"]
    ]
    if invalid:
        st.error(
            "Please provide a name and priority for every habit, and ensure minimum minutes do not exceed full minutes."
        )
    else:
        with st.spinner("Adjusting your routine with Claude…"):
            try:
                plan = ask_claude(int(available_minutes), schedule_change.strip(), habits)
            except Exception as error:
                st.error(f"Could not create the routine: {error}")
            else:
                st.success(
                    "Routine adjusted—shortening or skipping a habit is an adaptation, not a failure."
                )
                if plan.get("status") != "ok":
                    st.warning("More information is needed before a routine can be created.")
                    st.write(plan.get("explanation", "Please review the missing information."))
                    if plan.get("missing_fields"):
                        st.write("Missing: " + ", ".join(plan["missing_fields"]))
                else:
                    total_minutes = int(plan.get("total_minutes", 0))
                    remaining_minutes = int(plan.get("remaining_minutes", 0))
                    routine = plan.get("adjusted_routine", [])
                    skipped = plan.get("skipped_habits", [])

                    metric1, metric2, metric3 = st.columns(3)
                    metric1.metric("Planned", f"{total_minutes} min")
                    metric2.metric("Available", f"{available_minutes} min")
                    metric3.metric("Remaining", f"{remaining_minutes} min")
                    progress = min(total_minutes / available_minutes, 1.0) if available_minutes else 0.0
                    st.progress(progress, text=f"{total_minutes} of {available_minutes} minutes planned")

                    st.info(plan.get("explanation", "Your routine was adjusted to fit today's time."))

                    st.markdown('<div class="section-kicker">Step 2 · Your flexible plan</div>', unsafe_allow_html=True)
                    st.subheader("Today's routine")
                    if routine:
                        for item in routine:
                            shortened = item.get("version") != "full"
                            card_class = "routine-card shortened" if shortened else "routine-card"
                            pill_class = "time-pill short-pill" if shortened else "time-pill"
                            version = "Shortened version" if shortened else "Full version"
                            st.markdown(
                                f"""
                                <div class="{card_class}">
                                    <div style="display:flex; justify-content:space-between; gap:1rem; align-items:center;">
                                        <div>
                                            <div class="routine-name">{safe_text(item.get('habit', 'Habit'))}</div>
                                            <div class="routine-meta">{safe_text(version)} · {safe_text(item.get('priority', 'unranked'))} priority · {safe_text(item.get('reason', ''))}</div>
                                        </div>
                                        <span class="{pill_class}">{safe_text(item.get('minutes', 0))} min</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("No habits fit today, but that does not mean you failed. You can try again when time opens up.")

                    if skipped:
                        st.subheader("Skipped for today")
                        for item in skipped:
                            st.markdown(
                                f"""
                                <div class="skip-card">
                                    <b>{safe_text(item.get('habit', 'Habit'))}</b>
                                    <span> · {safe_text(item.get('priority', 'unranked'))} priority</span><br>
                                    <span>{safe_text(item.get('reason', 'Not enough time'))}.</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    st.markdown('<div class="section-kicker">Step 3 · Take it with you</div>', unsafe_allow_html=True)
                    st.subheader("Share your adjusted routine")
                    st.caption("Email and message buttons open a draft for you to review. The app never sends anything automatically.")
                    share_text = build_share_text(plan)
                    email_url = (
                        "mailto:?subject="
                        + quote("My FlexRoutine plan")
                        + "&body="
                        + quote(share_text)
                    )
                    message_url = "sms:?body=" + quote(share_text)
                    share_col1, share_col2, share_col3 = st.columns(3)
                    with share_col1:
                        st.link_button("✉️ Open email draft", email_url, use_container_width=True)
                    with share_col2:
                        st.link_button("💬 Open message draft", message_url, use_container_width=True)
                    with share_col3:
                        st.download_button(
                            "⬇️ Download JSON",
                            data=json.dumps(plan, indent=2),
                            file_name="flexroutine-plan.json",
                            mime="application/json",
                            use_container_width=True,
                        )

                    with st.expander("View raw JSON"):
                        st.json(plan)

