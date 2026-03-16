"""LifeOS Frontend - Streamlit Chat UI with debug panel."""

import streamlit as st
import httpx

API_BASE = "http://localhost:12345/api"

st.set_page_config(page_title="LifeOS", page_icon="🧠", layout="wide")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🧠 LifeOS")
    show_debug = st.toggle("Show debug panel", value=False)
    st.divider()

    # Proactive messages section
    st.subheader("Proactive Messages")
    if st.button("Trigger Morning Briefing"):
        try:
            resp = httpx.post(f"{API_BASE}/proactive/trigger?user_id=default_user", timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            st.success("Briefing generated!")
            st.markdown(data.get("briefing", ""))
        except Exception as e:
            st.error(f"Failed: {e}")

    # Fetch proactive messages
    try:
        resp = httpx.get(f"{API_BASE}/proactive/messages?user_id=default_user&limit=5", timeout=5.0)
        if resp.status_code == 200:
            msgs = resp.json().get("messages", [])
            unread = [m for m in msgs if not m.get("read")]
            if unread:
                st.info(f"{len(unread)} new notification(s)")
                for m in unread[:3]:
                    with st.expander(f"📬 {m.get('type', 'notification')} — {m.get('created_at', '')[:16]}"):
                        st.markdown(m.get("content", ""))
    except Exception:
        pass  # Backend might not be running yet

    st.divider()

    # System info
    if show_debug:
        st.subheader("System Info")
        try:
            resp = httpx.get(f"{API_BASE}/debug/system", timeout=5.0)
            if resp.status_code == 200:
                info = resp.json()
                st.json(info)
        except Exception:
            st.caption("Backend not reachable")

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
col_chat, col_debug = st.columns([3, 2] if show_debug else [1, 0.001])

with col_chat:
    st.title("LifeOS Chat")

    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask LifeOS anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = httpx.post(
                        f"{API_BASE}/chat",
                        json={
                            "user_id": "default_user",
                            "session_id": "default_session",
                            "message": prompt,
                        },
                        timeout=600.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    reply = data["reply"]
                    debug_data = {
                        "intent": data.get("intent"),
                        "trace": data.get("trace", []),
                        "plan": data.get("plan"),
                        "tool_logs": data.get("tool_logs", []),
                        "trace_id": data.get("trace_id"),
                        "duration_ms": data.get("duration_ms", 0),
                    }
                except Exception as e:
                    reply = f"Error connecting to backend: {e}"
                    debug_data = None

            st.markdown(reply)

        msg_data = {"role": "assistant", "content": reply}
        if debug_data:
            msg_data["debug"] = debug_data
        st.session_state.messages.append(msg_data)

# ---------------------------------------------------------------------------
# Debug panel (right column)
# ---------------------------------------------------------------------------
if show_debug:
    with col_debug:
        st.subheader("Debug Panel")

        # Show latest request trace
        latest_debug = None
        for msg in reversed(st.session_state.get("messages", [])):
            if msg.get("debug"):
                latest_debug = msg["debug"]
                break

        if latest_debug:
            # Trace flow visualization
            st.caption("**Trace Flow**")
            trace_steps = latest_debug.get("trace", [])
            if trace_steps:
                for i, step in enumerate(trace_steps):
                    icon = "✅" if i == len(trace_steps) - 1 else "➡️"
                    st.text(f"  {icon} {step}")
            else:
                st.text("  No trace data")

            st.divider()

            # Intent
            st.caption("**Intent**")
            st.code(latest_debug.get("intent", "unknown"))

            # Duration
            dur = latest_debug.get("duration_ms", 0)
            if dur:
                st.caption(f"**Duration:** {dur}ms")

            # Plan
            plan = latest_debug.get("plan")
            if plan:
                st.caption("**Execution Plan**")
                st.json(plan)

            # Tool logs
            tool_logs = latest_debug.get("tool_logs", [])
            if tool_logs:
                st.caption(f"**Tool Calls** ({len(tool_logs)})")
                for tl in tool_logs:
                    with st.expander(f"🔧 {tl.get('tool', '?')} (step {tl.get('step_id', '?')})"):
                        st.json(tl)
        else:
            st.info("Send a message to see debug info here.")

        st.divider()

        # Recent traces from DB
        st.caption("**Recent Traces**")
        try:
            resp = httpx.get(
                f"{API_BASE}/debug/traces?user_id=default_user&limit=5",
                timeout=5.0,
            )
            if resp.status_code == 200:
                traces = resp.json().get("traces", [])
                for t in traces:
                    label = f"{t.get('intent', '?')} — {t.get('user_message', '')[:30]}… ({t.get('duration_ms', 0)}ms)"
                    with st.expander(label):
                        st.json({
                            "trace": t.get("trace_json", []),
                            "plan": t.get("plan_json", {}),
                            "tool_logs": t.get("tool_logs_json", []),
                        })
        except Exception:
            st.caption("Could not fetch traces")
