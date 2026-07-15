import streamlit as st
from PIL import Image
import time
import json
import os
import base64
import pandas as pd

# Import backend logic
from backend.router import predict_stage
from backend.database import log_inspection, fetch_all_logs, delete_log
from backend.ai_agent import ask_database
from frontend_utils import apply_enterprise_css

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AOI Defect Dashboard", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

apply_enterprise_css()

# Sidebar banner image.
SIDEBAR_IMAGE = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2070&auto=format&fit=crop"


# --- ANALYTICS HELPERS ---
def build_defect_type_distribution(df):
    """Aggregate granular_details JSON across all logs into per-class counts."""
    counts = {}
    if df is None or df.empty or "granular_details" not in df.columns:
        return pd.DataFrame(columns=["Defect Type", "Count"])
    for raw in df["granular_details"].dropna():
        try:
            details = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        for k, v in details.items():
            if k == "Total_Defect_Area_Pixels":
                continue
            if isinstance(v, (int, float)):
                counts[k] = counts.get(k, 0) + v
    if not counts:
        return pd.DataFrame(columns=["Defect Type", "Count"])
    return (
        pd.DataFrame(sorted(counts.items(), key=lambda x: -x[1]), columns=["Defect Type", "Count"])
    )


def build_defects_over_time(df):
    """Total defects grouped by calendar day."""
    if df is None or df.empty or "timestamp" not in df.columns:
        return pd.DataFrame(columns=["Date", "Defects"])
    tmp = df.copy()
    tmp["Date"] = pd.to_datetime(tmp["timestamp"], errors="coerce").dt.date
    tmp = tmp.dropna(subset=["Date"])
    if tmp.empty:
        return pd.DataFrame(columns=["Date", "Defects"])
    grouped = tmp.groupby("Date")["total_defects"].sum().reset_index()
    grouped.columns = ["Date", "Defects"]
    return grouped


def render_dashboard_charts(df):
    """Render the two requested visuals: defect-type distribution + defects over time."""
    dist = build_defect_type_distribution(df)
    trend = build_defects_over_time(df)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='section-header'>Defect-Type Distribution</div>", unsafe_allow_html=True)
        if dist.empty:
            st.caption("No defects recorded yet.")
        else:
            st.bar_chart(dist.set_index("Defect Type"), color="#00E5FF", use_container_width=True)
    with c2:
        st.markdown("<div class='section-header'>Defects Over Time</div>", unsafe_allow_html=True)
        if trend.empty:
            st.caption("No time-series data yet.")
        else:
            st.area_chart(trend.set_index("Date"), color="#b829ea", use_container_width=True)


def _img_data_uri(path):
    """Return a base64 data URI for a local image, or None if missing."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def render_example_showcase():
    """Show the original -> detected sample comparison on the landing page."""
    original = _img_data_uri("assets/original.jpg")
    detected = _img_data_uri("assets/detected.jpg")
    if not original or not detected:
        return
    st.markdown("<div class='section-header'>Example: Input &rarr; Detected Output</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="comparison-container">
            <div class="img-box">
                <div class="img-label">Original Input</div>
                <img src="{original}" class="demo-img"/>
            </div>
            <div class="img-box">
                <div class="img-label">Detected Output</div>
                <img src="{detected}" class="demo-img"/>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --- SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
    st.image(SIDEBAR_IMAGE, use_container_width=True)
    st.markdown("<h2 style='text-align: center; color: #00E5FF;'>AOI Control Panel</h2>", unsafe_allow_html=True)

    st.markdown("### Navigation")
    app_mode = st.radio("Select View:", ["Live Inspection", "Database Explorer"], label_visibility="collapsed")

    selected_stage = None
    run_button = False
    conf_threshold = 0.25

    if app_mode == "Live Inspection":
        st.divider()
        stage_options = [
            "Auto-Detect Stage (AI)", "Stage 1: Inked Board", "Stage 2: Acid Batch (Etched)",
            "Stage 3: Green Coating", "Stage 4: Component Welding (Top View)", "Stage 4: Component Welding (Side View)"
        ]
        st.markdown("<p style='color: #A0AEC0; font-size: 0.9rem;'>Active Routing Mode</p>", unsafe_allow_html=True)
        selected_stage = st.selectbox("Routing Mode:", stage_options, label_visibility="collapsed")

        st.markdown("<p style='color: #A0AEC0; font-size: 0.9rem;'>Detection Confidence</p>", unsafe_allow_html=True)
        conf_threshold = st.slider("Confidence:", min_value=0.05, max_value=0.95, value=0.25, step=0.05, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        run_button = st.button("🚀 Run Inspection", type="primary", use_container_width=True)

    # --- GLOBAL AI CONFIGURATION ---
    st.divider()
    st.markdown("### 🤖 Engine Configuration")
    engine_choice = st.radio("Active Engine:", ["Cloud Engine (Gemini)", "Local Engine (Llama 3)"], label_visibility="collapsed")

    api_key = ""
    if engine_choice == "Cloud Engine (Gemini)":
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (KeyError, FileNotFoundError):
            st.error("Error: GEMINI_API_KEY not found in secrets.toml.")


# --- UNIVERSAL CHAT WIDGET FUNCTION ---
def _process_chat_turn(prompt):
    """Append the user's prompt, call the agent, and store the reply."""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            response = ask_database(prompt, engine=engine_choice, api_key=api_key)
            if isinstance(response, dict):
                friendly_text = response["friendly_answer"]
                st.markdown(friendly_text)
                st.session_state.messages.append({"role": "assistant", "content": friendly_text})
            else:
                st.error(response)
                st.session_state.messages.append({"role": "assistant", "content": response})


def render_chat_widget():
    st.divider()
    st.subheader("💬 Engineering Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your PCB Engineering Assistant. Ask me about your database logs (e.g. 'how many defects in image #3, keep or scrap?') or what to do with defective boards."}
        ]

    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # A queued prompt (e.g. from the "Ask about Image #N" button) runs first.
    pending = st.session_state.pop("pending_chat_prompt", None)
    if pending:
        _process_chat_turn(pending)

    if prompt := st.chat_input("Ask about database trends, defect protocols, etc..."):
        _process_chat_turn(prompt)


# ==========================================
# PAGE 1: LIVE INSPECTION
# ==========================================
if app_mode == "Live Inspection":
    st.markdown('<h1 class="shimmer-text">PCB Defect Detection System</h1>', unsafe_allow_html=True)
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <span class="status-dot"></span>
            <span style="color: #94A3B8; font-family: 'JetBrains Mono'; font-size: 0.9rem;">SYSTEM ONLINE AND READY</span>
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop board scan here...", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    if uploaded_file is None:
        df = fetch_all_logs()
        total_scans = len(df)
        total_defected = len(df[df['total_defects'] > 0]) if not df.empty else 0

        landing_page_html = f"""
            <div class="section-header">Live System Telemetry</div>
            <div class="telemetry-row">
                <div class="tel-card"><div class="tel-value" style="color: #10B981;">ON</div><div class="tel-label">Database Status</div></div>
                <div class="tel-card"><div class="tel-value">5/5</div><div class="tel-label">Active Models</div></div>
                <div class="tel-card"><div class="tel-value">{total_scans}</div><div class="tel-label">Total Scanned Images</div></div>
                <div class="tel-card"><div class="tel-value">{total_defected}</div><div class="tel-label">Total Defected Images</div></div>
            </div>
        """
        st.markdown(landing_page_html, unsafe_allow_html=True)
        render_example_showcase()

    else:
        image = Image.open(uploaded_file)
        result = None
        inserted_id = None

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original Input")
            with st.container(border=True):
                st.image(image, use_container_width=True)

        with col2:
            st.subheader("Defect Analysis")
            with st.container(border=True):
                if not run_button:
                    st.info("Awaiting execution command. Click 'Run Inspection'.")
                else:
                    progress_bar = st.progress(0, text="Executing Deep Learning Inference...")
                    try:
                        result = predict_stage(image, selected_stage, conf=conf_threshold)
                    except Exception as e:
                        result = {"status": "error", "message": f"Inference failed: {e}"}
                    progress_bar.progress(100, text="Scan Complete.")
                    time.sleep(0.3)
                    progress_bar.empty()

                    if result.get("status") == "success" and result.get("processed_image") is not None:
                        st.image(result["processed_image"], use_container_width=True)
                        inserted_id = log_inspection(
                            stage=result['routed_to'],
                            total_defects=result.get('total_defects', 0),
                            details_dict=result.get('details_dict', {}),
                            image_pil=result["processed_image"]
                        )
                    else:
                        st.error(result.get("message", "Image processing failed."))

        # Only render the results block when we actually ran and succeeded.
        if run_button and result is not None and result.get("status") == "success":
            st.divider()
            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric(label="Active Neural Network", value=result['routed_to'])
            if inserted_id:
                metric_col2.metric(label="Database Inspection ID", value=f"#{inserted_id}")

            st.info(f"**Inspection Result:** {result['message']}", icon="🔍")

            # Per-image defect breakdown chart.
            details = result.get("details_dict", {}) or {}
            chart_data = {k: v for k, v in details.items() if k != "Total_Defect_Area_Pixels" and isinstance(v, (int, float))}
            if chart_data:
                st.markdown("<div class='section-header'>This Board — Defect Breakdown</div>", unsafe_allow_html=True)
                st.bar_chart(pd.Series(chart_data, name="Count"), color="#00E5FF", use_container_width=True)

            # Direct-chat affordance for this specific image.
            if inserted_id:
                st.markdown(f"<p style='color:#94A3B8;'>You can chat with the assistant about this scan below (Image <b>#{inserted_id}</b>).</p>", unsafe_allow_html=True)
                if st.button(f"💬 Ask assistant about Image #{inserted_id}", use_container_width=True):
                    st.session_state.pending_chat_prompt = (
                        f"Analyze inspection image #{inserted_id}: how many and which defects were found, "
                        f"and should I ACCEPT, REWORK, or SCRAP it? Include prevention advice."
                    )
                    st.rerun()

    render_chat_widget()

# ==========================================
# PAGE 2: DATABASE EXPLORER
# ==========================================
elif app_mode == "Database Explorer":
    st.title("🗄️ Database Explorer")

    df = fetch_all_logs()

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Quick Analytics")
        col1, col2 = st.columns(2)
        col1.metric("Total Inspections", len(df))
        col2.metric("Total Defects Found (All Time)", int(df['total_defects'].sum()))

        render_dashboard_charts(df)

        st.divider()
        st.subheader("🗑️ Manage Records")
        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            record_to_delete = st.selectbox("Select Record ID to Delete:", df['id'].tolist())
        with del_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Delete Record", type="secondary", use_container_width=True):
                if delete_log(record_to_delete):
                    st.success(f"Record {record_to_delete} successfully deleted!")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("The database is currently empty. Run an inspection first!")

    render_chat_widget()
