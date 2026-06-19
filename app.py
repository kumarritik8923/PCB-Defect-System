import streamlit as st
from PIL import Image
import time
from io import BytesIO

# Import backend logic
from backend.router import mock_predict_stage
from backend.database import log_inspection, fetch_all_logs, delete_log

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AOI Defect Dashboard", page_icon="🤖", layout="wide")

# --- SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1706/1706196.png", width=60)
    st.title("AOI Control Panel")
    
    # MULTI-PAGE NAVIGATION
    st.markdown("### Navigation")
    app_mode = st.radio("Select View:", ["Live Inspection", "Database Explorer", "AI Assistant (Coming Soon)"])
    st.divider()
    
    if app_mode == "Live Inspection":
        stage_options = [
            "Auto-Detect Stage (AI)", "Stage 1: Inked Board", "Stage 2: Acid Batch (Etched)",
            "Stage 3: Green Coating", "Stage 4: Component Welding (Top View)", "Stage 4: Component Welding (Side View)"
        ]
        selected_stage = st.selectbox("Routing Mode:", stage_options)
        run_button = st.button("🚀 Run Inspection", type="primary", use_container_width=True)

# ==========================================
# PAGE 1: LIVE INSPECTION
# ==========================================
if app_mode == "Live Inspection":
    st.title("PCB Defect Detection System")
    st.markdown("Upload a high-resolution board scan to initiate the deep learning pipeline.")

    uploaded_file = st.file_uploader("Drop board scan here...", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

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

                        # --- DATABASE LOGGING TRIGGER ---
                        log_inspection(
                            stage=result['routed_to'], 
                            total_defects=result.get('total_defects', 0), 
                            details_dict=result.get('details_dict', {}), 
                            image_pil=result["processed_image"]
                        )
                    else:
                        st.error("Image processing failed.")

        # --- UI FIX: CLEAN TELEMETRY ROW ---
        if run_button and result["status"] == "success":
            st.divider()
            st.subheader("System Telemetry")
            
            # Use a metric for the stage, and a wide box for the long text to prevent clipping
            st.metric(label="Active Neural Network", value=result['routed_to'])
            st.info(f"**Inspection Result:** {result['message']}", icon="🔍")
            
            # Export Button
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
elif app_mode == "AI Assistant (Coming Soon)":
    st.title("🤖 Database AI Assistant")
    st.warning("Phase 3: The Dual-LLM (Gemini/Gemma) Text-to-SQL integration will go here.")