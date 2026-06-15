import streamlit as st
import pandas as pd
import time
from datetime import datetime, date

# ── Page config (must be first) ───────────────────────────────────────────────
st.set_page_config(
    page_title="FlowMind — ADHD Focus Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local imports ─────────────────────────────────────────────────────────────
from database import (
    init_db, add_task, get_tasks, update_task_status, delete_task,
    start_session, end_session, get_sessions, save_nudge, rate_nudge,
    get_nudges, get_daily_summary, get_hourly_productivity, get_procrastination_data
)
from ml_engine import (
    compute_procrastination_score, cluster_procrastination_patterns,
    predict_best_focus_hours, detect_nudge_triggers, calculate_streak
)
from ai_nudge import generate_nudge, generate_weekly_insight
from charts import (
    chart_daily_focus, chart_mood_vs_productivity, chart_procrastination_scores,
    chart_hourly_heatmap, chart_category_breakdown, chart_streak_calendar,
    chart_energy_mood_radar
)

# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0F0F1A; }

.metric-card {
    background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
    border: 1px solid #2D2D44;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-value { font-size: 2.2rem; font-weight: 700; color: #A78BFA; }
.metric-label { font-size: 0.85rem; color: #64748B; margin-top: 4px; }

.nudge-card {
    background: linear-gradient(135deg, #1E1B4B 0%, #1A1A2E 100%);
    border-left: 4px solid #7C3AED;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    font-size: 1.05rem;
    line-height: 1.6;
    color: #E2E8F0;
}

.task-chip {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
}

.status-pending   { background: #1E293B; color: #94A3B8; }
.status-progress  { background: #1E3A5F; color: #60A5FA; }
.status-completed { background: #064E3B; color: #34D399; }
.status-abandoned { background: #450A0A; color: #F87171; }

.section-header {
    font-size: 1.3rem; font-weight: 600;
    color: #A78BFA; margin-bottom: 12px;
    border-bottom: 1px solid #2D2D44;
    padding-bottom: 8px;
}

.stButton>button {
    border-radius: 10px;
    font-weight: 500;
    transition: all 0.2s;
}
.stButton>button:hover { transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "active_task_id" not in st.session_state:
    st.session_state.active_task_id = None
if "last_nudge" not in st.session_state:
    st.session_state.last_nudge = None
if "last_nudge_id" not in st.session_state:
    st.session_state.last_nudge_id = None


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🧠 FlowMind")
    st.markdown("*Work with your brain, not against it.*")
    st.divider()

    import os

    groq_key = st.text_input(
        "🔑 Groq API Key (optional - pre-loaded for demo)",
        type="password",
        placeholder="gsk_...",
        value=os.environ.get("GROQ_API_KEY", ""),
        help="Get a free key at console.groq.com"
    )

    ai_enabled = bool(groq_key and groq_key.startswith("gsk_"))
    st.caption(f"AI Nudges: {'✅ Active' if ai_enabled else '⚠️ Enter key to enable'}")

    st.divider()

    # Quick stats
    daily_df = get_daily_summary()
    streak = calculate_streak(daily_df)
    sessions_df = get_sessions(limit=100)
    total_sessions = len(sessions_df)
    completed_sessions = int(sessions_df["completed"].sum()) if not sessions_df.empty else 0

    st.markdown(f"🔥 **Streak:** {streak} day{'s' if streak != 1 else ''}")
    st.markdown(f"✅ **Completed:** {completed_sessions}/{total_sessions} sessions")
    if total_sessions > 0:
        st.progress(completed_sessions / total_sessions, text=f"{completed_sessions/total_sessions:.0%} completion rate")

    st.divider()
    page = st.radio("Navigate", ["🏠 Dashboard", "✅ Tasks", "⏱️ Focus Session", "🤖 AI Nudges", "📊 Analytics"])


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    st.markdown("# 🧠 FlowMind Dashboard")
    st.caption(f"Today is {datetime.now().strftime('%A, %d %B %Y')} — let's see how you're doing.")

    # ── Top Metrics ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    today_data = daily_df[daily_df["date"] == str(date.today())].iloc[0] if not daily_df.empty and str(date.today()) in daily_df["date"].values else None

    with col1:
        val = f"{int(today_data['total_focus_minutes'])} min" if today_data is not None else "0 min"
        st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">Focus Today</div></div>', unsafe_allow_html=True)
    with col2:
        val = f"{streak}🔥"
        st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">Day Streak</div></div>', unsafe_allow_html=True)
    with col3:
        rate = f"{completed_sessions/max(total_sessions,1):.0%}"
        st.markdown(f'<div class="metric-card"><div class="metric-value">{rate}</div><div class="metric-label">Completion Rate</div></div>', unsafe_allow_html=True)
    with col4:
        tasks_df = get_tasks(status="pending")
        val = len(tasks_df)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">Pending Tasks</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts Row 1 ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_daily_focus(daily_df), use_container_width=True)
    with col2:
        st.plotly_chart(chart_mood_vs_productivity(sessions_df), use_container_width=True)

    # ── ML Insights ────────────────────────────────────────────────────────────
    proc_raw = get_procrastination_data()
    if not proc_raw.empty:
        proc_df = compute_procrastination_score(proc_raw)
        proc_df, _, pattern_msg = cluster_procrastination_patterns(proc_df)

        st.markdown("### 🎯 Your Procrastination Pattern")
        st.info(pattern_msg)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_procrastination_scores(proc_df), use_container_width=True)
        with col2:
            st.plotly_chart(chart_streak_calendar(daily_df), use_container_width=True)

    # ── AI Weekly Insight ──────────────────────────────────────────────────────
    if ai_enabled and not daily_df.empty:
        st.markdown("### 🤖 Weekly AI Insight")
        hourly_df = get_hourly_productivity()
        focus_result = predict_best_focus_hours(hourly_df)
        cat_df = proc_raw.groupby("category")["delay_count"].mean() if not proc_raw.empty else pd.Series()

        stats = {
            "total_sessions": total_sessions,
            "completion_rate": completed_sessions / max(total_sessions, 1),
            "avg_session_minutes": sessions_df["actual_minutes"].mean() if not sessions_df.empty else 0,
            "avg_mood": sessions_df["mood"].mean() if not sessions_df.empty else 3,
            "avg_energy": sessions_df["energy"].mean() if not sessions_df.empty else 3,
            "best_hour": f"{focus_result['best_hour']}:00" if focus_result else "unknown",
            "most_delayed_category": cat_df.idxmax() if not cat_df.empty else "unknown",
        }
        with st.spinner("Generating weekly insight..."):
            insight = generate_weekly_insight(groq_key, stats)
        st.markdown(f'<div class="nudge-card">💡 {insight}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TASKS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "✅ Tasks":
    st.markdown("# ✅ Task Manager")

    with st.expander("➕ Add New Task", expanded=False):
        with st.form("add_task_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Task title *", placeholder="e.g. Complete EDA notebook")
                category = st.selectbox("Category", ["Work", "Study", "Personal", "Health", "Creative", "Admin", "General"])
            with col2:
                priority = st.select_slider("Priority", options=[1, 2, 3], value=2,
                                            format_func=lambda x: {1:"🔴 High", 2:"🟡 Medium", 3:"🟢 Low"}[x])
                est_min = st.number_input("Estimated minutes", min_value=5, max_value=300, value=30, step=5)
            due = st.date_input("Due date (optional)", value=None)
            submitted = st.form_submit_button("Add Task", use_container_width=True, type="primary")
            if submitted and title:
                add_task(title, category, priority, est_min, str(due) if due else None)
                st.success(f"✅ Task '{title}' added!")
                st.rerun()

    st.markdown("---")

    # Filter
    status_filter = st.segmented_control(
        "Filter by status", ["All", "Pending", "In Progress", "Completed", "Abandoned"],
        default="All"
    )
    status_map = {"All": None, "Pending": "pending", "In Progress": "in_progress",
                  "Completed": "completed", "Abandoned": "abandoned"}
    tasks_df = get_tasks(status=status_map.get(status_filter))

    if tasks_df.empty:
        st.info("No tasks here yet. Add one above!")
    else:
        priority_label = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}
        status_badge = {
            "pending": "status-pending", "in_progress": "status-progress",
            "completed": "status-completed", "abandoned": "status-abandoned"
        }

        for _, row in tasks_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1.5, 1, 1])
                with col1:
                    badge = status_badge.get(row["status"], "status-pending")
                    st.markdown(f"""
                    **{row['title']}**
                    <span class="task-chip {badge}">{row['status'].replace('_',' ').title()}</span>
                    <span class="task-chip" style="background:#1E1B4B;color:#A78BFA;">{row['category']}</span>
                    <span class="task-chip" style="background:#1A1A2E;color:#94A3B8;">{priority_label.get(int(row['priority']), '🟡')}</span>
                    """, unsafe_allow_html=True)
                    if row["delay_count"] > 0:
                        st.caption(f"⚠️ Delayed {int(row['delay_count'])} time(s) · Est. {row['estimated_minutes']} min")
                with col2:
                    new_status = st.selectbox("", ["pending","in_progress","completed","abandoned"],
                                              index=["pending","in_progress","completed","abandoned"].index(row["status"]),
                                              key=f"status_{row['id']}", label_visibility="collapsed")
                    if new_status != row["status"]:
                        update_task_status(row["id"], new_status)
                        st.rerun()
                with col3:
                    if st.button("▶ Focus", key=f"focus_{row['id']}", use_container_width=True):
                        st.session_state.active_task_id = row["id"]
                        st.session_state._jump_to_session = True
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_{row['id']}", use_container_width=True):
                        delete_task(row["id"])
                        st.rerun()
                st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: FOCUS SESSION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⏱️ Focus Session":
    st.markdown("# ⏱️ Focus Session")

    tasks_df = get_tasks()
    pending_tasks = tasks_df[tasks_df["status"].isin(["pending", "in_progress"])]

    if pending_tasks.empty:
        st.warning("No pending tasks. Add tasks first!")
        st.stop()

    # ── No active session — show start form ────────────────────────────────────
    if st.session_state.active_session_id is None:
        st.markdown("### 🎯 Start a Focus Session")

        col1, col2 = st.columns(2)
        with col1:
            task_options = {row["title"]: row["id"] for _, row in pending_tasks.iterrows()}
            default_idx = 0
            if st.session_state.active_task_id:
                ids = list(task_options.values())
                if st.session_state.active_task_id in ids:
                    default_idx = ids.index(st.session_state.active_task_id)

            selected_title = st.selectbox("Which task?", list(task_options.keys()), index=default_idx)
            selected_task_id = task_options[selected_title]
            planned_min = st.slider("Planned session length (minutes)", 5, 90, 25, step=5)

        with col2:
            mood = st.select_slider(
                "Current mood 😊", options=[1,2,3,4,5],
                format_func=lambda x: {1:"😞 Very Low",2:"😕 Low",3:"😐 Neutral",4:"🙂 Good",5:"😄 Great"}[x],
                value=3
            )
            energy = st.select_slider(
                "Current energy ⚡", options=[1,2,3,4,5],
                format_func=lambda x: {1:"🪫 Drained",2:"😴 Tired",3:"😐 Okay",4:"⚡ Alert",5:"🚀 Energized"}[x],
                value=3
            )

        if st.button("🚀 Start Session", type="primary", use_container_width=True):
            sid = start_session(selected_task_id, mood, energy, planned_min)
            st.session_state.active_session_id = sid
            st.session_state.active_task_id = selected_task_id

            # AI start nudge
            if ai_enabled:
                nudge = generate_nudge(groq_key, "session_start", {
                    "task": selected_title, "mood": mood, "energy": energy
                })
                st.session_state.last_nudge = nudge
                nid = save_nudge(sid, selected_task_id, "session_start", nudge)
                st.session_state.last_nudge_id = nid

            st.rerun()

    # ── Active session ─────────────────────────────────────────────────────────
    else:
        sid = st.session_state.active_session_id
        tid = st.session_state.active_task_id

        task_row = tasks_df[tasks_df["id"] == tid]
        task_name = task_row["title"].values[0] if not task_row.empty else "Your Task"

        # Show nudge if present
        if st.session_state.last_nudge:
            st.markdown(f'<div class="nudge-card">🤖 {st.session_state.last_nudge}</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Helpful", key="rate_yes"):
                    if st.session_state.last_nudge_id:
                        rate_nudge(st.session_state.last_nudge_id, True)
                    st.session_state.last_nudge = None
                    st.rerun()
            with col2:
                if st.button("👎 Not helpful", key="rate_no"):
                    if st.session_state.last_nudge_id:
                        rate_nudge(st.session_state.last_nudge_id, False)
                    st.session_state.last_nudge = None
                    st.rerun()

        st.markdown(f"### 🎯 Focusing on: **{task_name}**")
        st.success("⏳ Session in progress... work on your task and come back when done.")

        # Live timer display
        sessions_df_live = get_sessions(limit=10)
        session_row = sessions_df_live[sessions_df_live["id"] == sid]
        if not session_row.empty:
            start_str = session_row["start_time"].values[0]
            try:
                start_dt = datetime.strptime(str(start_str), "%Y-%m-%d %H:%M:%S")
                elapsed = (datetime.now() - start_dt).total_seconds()
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                st.metric("⏱️ Time Elapsed", f"{mins}m {secs:02d}s")
            except:
                pass

        st.markdown("---")
        st.markdown("### 🏁 End Session")
        notes = st.text_area("Notes (optional)", placeholder="What did you accomplish? What blocked you?")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Completed!", type="primary", use_container_width=True):
                actual = end_session(sid, tid, completed=True, notes=notes)
                st.balloons()
                st.success(f"🎉 Great work! You focused for {actual:.0f} minutes.")

                if ai_enabled:
                    sessions_latest = get_sessions(20)
                    tasks_latest = get_tasks()
                    triggers = detect_nudge_triggers(sessions_latest, tasks_latest)
                    if triggers:
                        reason, ctx = triggers[0]
                        nudge = generate_nudge(groq_key, reason, ctx)
                        nid = save_nudge(sid, tid, reason, nudge)
                        st.session_state.last_nudge = nudge
                        st.session_state.last_nudge_id = nid

                st.session_state.active_session_id = None
                st.session_state.active_task_id = None
                time.sleep(1.5)
                st.rerun()

        with col2:
            if st.button("❌ Abandoned", use_container_width=True):
                actual = end_session(sid, tid, completed=False, notes=notes)
                st.warning(f"Session ended after {actual:.0f} minutes. That's okay — let's regroup.")

                if ai_enabled:
                    sessions_latest = get_sessions(20)
                    tasks_latest = get_tasks()
                    triggers = detect_nudge_triggers(sessions_latest, tasks_latest)
                    reason = triggers[0][0] if triggers else "short_abandon"
                    ctx = triggers[0][1] if triggers else {"task": task_name, "minutes": actual}
                    nudge = generate_nudge(groq_key, reason, ctx)
                    nid = save_nudge(sid, tid, reason, nudge)
                    st.session_state.last_nudge = nudge
                    st.session_state.last_nudge_id = nid

                st.session_state.active_session_id = None
                st.session_state.active_task_id = None
                time.sleep(1)
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: AI NUDGES
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Nudges":
    st.markdown("# 🤖 AI Nudge History")

    if not ai_enabled:
        st.warning("Enter your Groq API key in the sidebar to enable AI nudges.")

    # Manual nudge trigger
    st.markdown("### 💬 Request a Nudge Now")
    col1, col2 = st.columns(2)
    with col1:
        nudge_type = st.selectbox("Nudge type", [
            "session_start", "low_mood", "high_prio_delayed",
            "consecutive_fails", "end_of_day", "pattern_insight"
        ])
    with col2:
        manual_mood = st.slider("Your mood right now", 1, 5, 3)

    if st.button("⚡ Generate Nudge", type="primary", disabled=not ai_enabled):
        with st.spinner("Asking your ADHD coach..."):
            ctx = {"mood": manual_mood, "energy": manual_mood, "task": "your current focus"}
            nudge = generate_nudge(groq_key, nudge_type, ctx)
        st.markdown(f'<div class="nudge-card">🤖 {nudge}</div>', unsafe_allow_html=True)
        save_nudge(None, None, nudge_type, nudge)

    st.markdown("---")
    st.markdown("### 📜 Nudge Log")
    nudges_df = get_nudges()

    if nudges_df.empty:
        st.info("No nudges yet. Start a focus session to get your first AI coaching message!")
    else:
        helpful_count = int((nudges_df["was_helpful"] == 1).sum())
        not_helpful = int((nudges_df["was_helpful"] == 0).sum())
        st.caption(f"👍 {helpful_count} helpful · 👎 {not_helpful} not helpful · {len(nudges_df)} total nudges")

        for _, row in nudges_df.iterrows():
            with st.container():
                trigger_emoji = {
                    "session_start": "🚀", "short_abandon": "⏸️",
                    "consecutive_fails": "🔁", "high_prio_delayed": "⚠️",
                    "low_mood": "💙", "end_of_day": "🌙", "pattern_insight": "🎯"
                }.get(row["trigger_reason"], "💬")

                helpfulness = {1: "👍", 0: "👎", -1: "—"}.get(row["was_helpful"], "—")
                ts = str(row["timestamp"])[:16]

                st.markdown(f"""
                <div class="nudge-card">
                {trigger_emoji} <strong>{row['trigger_reason'].replace('_',' ').title()}</strong>
                <span style="float:right;color:#64748B;font-size:0.8rem;">{ts} · {helpfulness}</span><br>
                {row['nudge_text']}
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.markdown("# 📊 Deep Analytics")

    sessions_df = get_sessions(limit=500)
    daily_df = get_daily_summary()
    hourly_df = get_hourly_productivity()
    proc_raw = get_procrastination_data()

    if sessions_df.empty:
        st.info("No session data yet. Start using the Focus Session tab!")
        st.stop()

    # Focus Hours
    focus_result = predict_best_focus_hours(hourly_df)
    predictions = focus_result["predictions"] if focus_result else None

    if focus_result:
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🌟 Your best focus hour: **{focus_result['best_hour']}:00**")
        with col2:
            st.error(f"⚠️ Least productive hour: **{focus_result['worst_hour']}:00**")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_hourly_heatmap(hourly_df, predictions), use_container_width=True)
    with col2:
        st.plotly_chart(chart_energy_mood_radar(sessions_df), use_container_width=True)

    # Procrastination deep dive
    if not proc_raw.empty:
        proc_df = compute_procrastination_score(proc_raw)
        proc_df, _, pattern_msg = cluster_procrastination_patterns(proc_df)

        st.markdown("### 🚨 Procrastination Intelligence")
        st.info(pattern_msg)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_procrastination_scores(proc_df), use_container_width=True)
        with col2:
            st.plotly_chart(chart_category_breakdown(proc_df), use_container_width=True)

        st.markdown("### 📋 Full Procrastination Table")
        display_cols = ["title", "category", "delay_count", "procrastination_score",
                        "risk_level", "completion_rate", "avg_mood"]
        available_cols = [c for c in display_cols if c in proc_df.columns]
        st.dataframe(
            proc_df[available_cols].sort_values("procrastination_score", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    # Raw session log
    with st.expander("📄 Raw Session Log"):
        show_cols = ["task_title", "category", "mood", "energy",
                     "start_time", "actual_minutes", "completed", "notes"]
        available = [c for c in show_cols if c in sessions_df.columns]
        st.dataframe(sessions_df[available], use_container_width=True, hide_index=True)
