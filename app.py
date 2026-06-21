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
    # Adding a sleek tech image to the top of the sidebar
    st.image("https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
    st.markdown("<h2 style='text-align: center; color: #00E5FF;'>AOI Control Panel</h2>", unsafe_allow_html=True)
    
    st.markdown("### Navigation")
    app_mode = st.radio("Select View:", ["Live Inspection", "Database Explorer", "AI Assistant"], label_visibility="collapsed")
    st.divider()
    
    if app_mode == "Live Inspection":
        stage_options = [
            "Auto-Detect Stage (AI)", "Stage 1: Inked Board", "Stage 2: Acid Batch (Etched)",
            "Stage 3: Green Coating", "Stage 4: Component Welding (Top View)", "Stage 4: Component Welding (Side View)"
        ]
        st.markdown("<p style='color: #A0AEC0; font-size: 0.9rem;'>Active Routing Mode</p>", unsafe_allow_html=True)
        selected_stage = st.selectbox("Routing Mode:", stage_options, label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        run_button = st.button("🚀 Run Inspection", type="primary", use_container_width=True)

# ==========================================
# PAGE 1: LIVE INSPECTION
# ==========================================
if app_mode == "Live Inspection":
    
    # Animated Shimmering Title
    st.markdown('<h1 class="shimmer-text">PCB Defect Detection System</h1>', unsafe_allow_html=True)
    
    # Pulsing Status Indicator
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <span class="status-dot"></span>
            <span style="color: #94A3B8; font-family: 'JetBrains Mono'; font-size: 0.9rem;">SYSTEM ONLINE AND READY FOR UPLOAD</span>
        </div>
    """, unsafe_allow_html=True)

    # Standard Streamlit Uploader
    uploaded_file = st.file_uploader("Drop board scan here...", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    # --- ADVANCED RAW HTML LANDING PAGE ---
    if uploaded_file is None:
        
        # 1. FETCH LIVE TELEMETRY DATA
        df = fetch_all_logs()
        total_scans = len(df)
        
        # FIX: We now filter the dataframe to count only the images that actually have defects
        total_defected_images = len(df[df['total_defects'] > 0]) if not df.empty else 0
        
        # 2. HELPER FUNCTION: Convert local images to Base64 HTML strings
        def get_img_string(filepath):
            if os.path.exists(filepath):
                with open(filepath, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode()
                mime_type = "image/png" if filepath.lower().endswith('.png') else "image/jpeg"
                return f"data:{mime_type};base64,{encoded_string}"
            return ""

        # 3. LOAD YOUR TWO EXAMPLE IMAGES
        img_original = get_img_string("assets/original.jpg")
        img_detected = get_img_string("assets/detected.jpg")
        
        # 4. BULLETPROOF HTML CONSTRUCTION
        landing_page_html = (
            # --- SECTION 1: LIVE TELEMETRY ---
            '<div class="section-header">Live System Telemetry</div>'
            '<div class="telemetry-row">'
                '<div class="tel-card">'
                    '<div class="tel-value" style="color: #10B981;">ON</div>'
                    '<div class="tel-label">Database Status</div>'
                '</div>'
                '<div class="tel-card">'
                    '<div class="tel-value">5/5</div>'
                    '<div class="tel-label">Active Models</div>'
                '</div>'
                '<div class="tel-card">'
                    f'<div class="tel-value">{total_scans}</div>'
                    '<div class="tel-label">Total Scanned Images</div>'
                '</div>'
                '<div class="tel-card">'
                    f'<div class="tel-value">{total_defected_images}</div>'
                    '<div class="tel-label">Total Defected Images</div>'
                '</div>'
            '</div>'
            
            # --- SECTION 2: DEFECT TYPOLOGY (TEXT ONLY) ---
            '<div class="section-header">Bare-Board Defect Typology (Stages 1-3)</div>'
            '<div class="typology-grid">'
                '<div class="typ-card">'
                    '<div class="typ-title">⚡ 1. Short Circuit</div>'
                    '<div class="typ-desc">Unintended conductive pathway between two adjacent copper traces.</div>'
                '</div>'
                '<div class="typ-card">'
                    '<div class="typ-title">🔗 2. Open Circuit</div>'
                    '<div class="typ-desc">A complete break or gap in a trace, disrupting electrical flow.</div>'
                '</div>'
                '<div class="typ-card">'
                    '<div class="typ-title">🕳️ 3. Mousebite</div>'
                    '<div class="typ-desc">Irregular, jagged missing chunks of copper along the edge of a trace.</div>'
                '</div>'
                '<div class="typ-card">'
                    '<div class="typ-title">🔪 4. Spur</div>'
                    '<div class="typ-desc">An unwanted microscopic protrusion of copper extending outward.</div>'
                '</div>'
                '<div class="typ-card">'
                    '<div class="typ-title">🎯 5. Pin Hole</div>'
                    '<div class="typ-desc">Tiny circular indentations or missing copper spots within a solid pad.</div>'
                '</div>'
                '<div class="typ-card">'
                    '<div class="typ-title">🧩 6. Spurious Copper</div>'
                    '<div class="typ-desc">Excess, un-etched copper fragments left behind on the bare substrate.</div>'
                '</div>'
            '</div>'

            # --- SECTION 3: LIVE INFERENCE EXAMPLE (IMAGES) ---
            '<div class="section-header">System Capability Demonstration</div>'
            '<div class="comparison-container">'
                '<div class="img-box">'
                    '<div class="img-label">Input: Original Image</div>'
                    f'<img src="{img_original}" class="demo-img" alt="Original PCB">'
                '</div>'
                '<div class="img-box">'
                    '<div class="img-label">Output: Detected Image</div>'
                    f'<img src="{img_detected}" class="demo-img" alt="Detected PCB">'
                '</div>'
            '</div>'
        )
        
        st.markdown(landing_page_html, unsafe_allow_html=True)


    # --- INFERENCE EXECUTION ---
    if uploaded_file is not None:
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
                    st.info("Awaiting execution command. Click 'Run Inspection' in the sidebar.")
                else:
                    progress_bar = st.progress(0, text="Executing Deep Learning Inference...")
                    result = mock_predict_stage(image, selected_stage)
                    progress_bar.progress(100, text="Scan Complete.")
                    time.sleep(0.3)
                    progress_bar.empty() 
                    
                    if result.get("processed_image") is not None:
                        st.image(result["processed_image"], use_container_width=True)

                        log_inspection(
                            stage=result['routed_to'], 
                            total_defects=result.get('total_defects', 0), 
                            details_dict=result.get('details_dict', {}), 
                            image_pil=result["processed_image"]
                        )
                    else:
                        st.error("Image processing failed.")

        if run_button and result["status"] == "success":
            st.divider()
            st.subheader("System Telemetry")
            
            st.metric(label="Active Neural Network", value=result['routed_to'])
            clean_message = result['message'].replace("Inference complete. ", "")
            st.info(f"**Inspection Result:** {clean_message}", icon="🔍")
            
            if result.get("processed_image") is not None:
                buf = BytesIO()
                result["processed_image"].save(buf, format="JPEG")
                st.download_button(
                    label="💾 Download Defect Report Image",
                    data=buf.getvalue(),
                    file_name="pcb_defect_report.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )

# ==========================================
# PAGE 2: DATABASE EXPLORER
# ==========================================
elif app_mode == "Database Explorer":
    st.title("🗄️ Database Explorer")
    st.markdown("View historical inspection logs and granular defect data.")
    
    # We must import the new delete function at the top of app.py! 
    # (Make sure to add `delete_log` to your import statement at the top: `from backend.database import log_inspection, fetch_all_logs, delete_log`)
    from backend.database import delete_log 

    df = fetch_all_logs()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader("Quick Analytics")
        col1, col2 = st.columns(2)
        col1.metric("Total Inspections", len(df))
        col2.metric("Total Defects Found (All Time)", df['total_defects'].sum())

        # --- NEW: DELETE RECORD UI ---
        st.divider()
        st.subheader("🗑️ Manage Records")
        del_col1, del_col2 = st.columns([3, 1])
        
        with del_col1:
            # Create a dropdown containing all the current IDs in the database
            record_to_delete = st.selectbox("Select Record ID to Delete:", df['id'].tolist())
            
        with del_col2:
            st.markdown("<br>", unsafe_allow_html=True) # Adds spacing to align button with dropdown
            if st.button("Delete Record", type="secondary", use_container_width=True):
                if delete_log(record_to_delete):
                    st.success(f"Record {record_to_delete} successfully deleted!")
                    time.sleep(1)
                    st.rerun() # Instantly refreshes the page to show the updated table
    else:
        st.info("The database is currently empty. Run an inspection first!")

# ==========================================
# PAGE 3: AI ASSISTANT
# ==========================================
elif app_mode == "AI Assistant":
    st.title("🤖 Database AI Assistant")
    st.markdown("Chat with your inspection data using natural language.")
    
    st.markdown("### ⚙️ Engine Configuration")
    engine_choice = st.radio(
        "Select AI Engine:", 
        ["Cloud Engine (Gemini)", "Local Engine (Gemma)"], 
        horizontal=True
    )
    
    api_key = ""
    if engine_choice == "Cloud Engine (Gemini)":
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("Cloud Engine Online: Secured API Key loaded.", icon="🔒")
        except KeyError:
            st.error("Error: GEMINI_API_KEY not found in secrets.toml.")
    else:
        st.info("Running locally via Ollama.")

    st.divider()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your PCB Database Assistant. Ask me anything about your inspection logs.", "sql": None}
        ]

    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # If the assistant has SQL saved in history, render the expander
            if msg.get("sql"):
                with st.expander("🔍 View Database Query"):
                    code_ticks = "`" * 3
                    st.markdown(f"{code_ticks}sql\n{msg['sql']}\n{code_ticks}")
                    st.markdown(f"**Raw Data:** `{msg.get('raw', '')}`")

    # --- 3. Chat Input & Execution ---
    if prompt := st.chat_input("Ask a question about your database..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing data..."):
                response = ask_database(prompt, engine=engine_choice, api_key=api_key)
                
                # If the AI returned a dictionary (success)
                if isinstance(response, dict):
                    friendly_text = response['friendly_answer']
                    
                    # Print ONLY the friendly human text
                    st.markdown(friendly_text)
                    
                    # Save only the conversational text to memory
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": friendly_text
                    })
                
                # If the AI returned a string (Error)
                else:
                    st.error(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})