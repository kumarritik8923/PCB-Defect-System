import streamlit as st
from PIL import Image
import time
from io import BytesIO
import os
import base64

# Import backend logic
from backend.router import mock_predict_stage
from backend.database import log_inspection, fetch_all_logs, delete_log
from backend.ai_agent import ask_database
from frontend_utils import apply_enterprise_css

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AOI Defect Dashboard", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

apply_enterprise_css()

# --- SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
    st.markdown("<h2 style='text-align: center; color: #00E5FF;'>AOI Control Panel</h2>", unsafe_allow_html=True)
    
    st.markdown("### Navigation")
    app_mode = st.radio("Select View:", ["Live Inspection", "Database Explorer"], label_visibility="collapsed")
    
    if app_mode == "Live Inspection":
        st.divider()
        stage_options = [
            "Auto-Detect Stage (AI)", "Stage 1: Inked Board", "Stage 2: Acid Batch (Etched)",
            "Stage 3: Green Coating", "Stage 4: Component Welding (Top View)", "Stage 4: Component Welding (Side View)"
        ]
        st.markdown("<p style='color: #A0AEC0; font-size: 0.9rem;'>Active Routing Mode</p>", unsafe_allow_html=True)
        selected_stage = st.selectbox("Routing Mode:", stage_options, label_visibility="collapsed")
        
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
        except KeyError:
            st.error("Error: GEMINI_API_KEY not found in secrets.toml.")

# --- UNIVERSAL CHAT WIDGET FUNCTION ---
def render_chat_widget():
    st.divider()
    st.subheader("💬 Engineering Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your PCB Engineering Assistant. Ask me about your database logs or what to do with defective boards."}
        ]

    # Render history (SQL rendering removed)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about database trends, defect protocols, etc..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = ask_database(prompt, engine=engine_choice, api_key=api_key)
                
                if isinstance(response, dict):
                    friendly_text = response['friendly_answer']
                    st.markdown(friendly_text)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": friendly_text
                    })
                else:
                    st.error(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

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
    
    # Track the inserted ID globally for this page load
    inserted_id = None 

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

    else:
        image = Image.open(uploaded_file)
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
                    result = mock_predict_stage(image, selected_stage)
                    progress_bar.progress(100, text="Scan Complete.")
                    time.sleep(0.3)
                    progress_bar.empty() 
                    
                    if result.get("processed_image") is not None:
                        st.image(result["processed_image"], use_container_width=True)
                        
                        # Save to database AND capture the newly generated ID
                        inserted_id = log_inspection(
                            stage=result['routed_to'], 
                            total_defects=result.get('total_defects', 0), 
                            details_dict=result.get('details_dict', {}), 
                            image_pil=result["processed_image"]
                        )
                    else:
                        st.error("Image processing failed.")

        if run_button and result["status"] == "success":
            st.divider()
            # Displaying both the network and the new ID clearly
            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric(label="Active Neural Network", value=result['routed_to'])
            
            if inserted_id:
                metric_col2.metric(label="Database Inspection ID", value=f"#{inserted_id}")
                
            st.info(f"**Inspection Result:** {result['message']}", icon="🔍")

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
        col2.metric("Total Defects Found (All Time)", df['total_defects'].sum())

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