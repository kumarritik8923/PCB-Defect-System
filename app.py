import streamlit as st
from PIL import Image
import time
from io import BytesIO

# Import our backend logic
from backend.router import mock_predict_stage

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AOI Defect Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1706/1706196.png", width=60)
    st.title("AOI Control Panel")
    st.markdown("Automated Optical Inspection")
    st.divider()
    
    stage_options = [
        "Auto-Detect Stage (AI)", 
        "Stage 1: Inked Board",
        "Stage 2: Acid Batch (Etched)",
        "Stage 3: Green Coating",
        "Stage 4: Component Welding (Top View)",
        "Stage 4: Component Welding (Side View)"
    ]
    selected_stage = st.selectbox("Routing Mode:", stage_options, help="Leave on Auto-Detect for the AI to classify the board.")
    
    st.divider()
    run_button = st.button("🚀 Run Inspection", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("System Status: **Online**")
    st.caption("Active Models: **5/5**")

# --- 3. MAIN DASHBOARD AREA ---
st.title("PCB Defect Detection System")
st.markdown("Upload a high-resolution board scan to initiate the deep learning pipeline.")

uploaded_file = st.file_uploader("Drop board scan here...", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    # --- UI FIX: PERFECTLY PARALLEL IMAGES ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Input")
        with st.container(border=True):
            st.image(image, use_container_width=True)
            
    with col2:
        st.subheader("Defect Analysis")
        with st.container(border=True):
            if not run_button:
                # Show a placeholder message to maintain height alignment
                st.info("Awaiting execution command. Click 'Run Inspection' in the sidebar.")
            else:
                # --- ADVANCED FEATURE: ANIMATED PROGRESS BAR ---
                progress_bar = st.progress(0, text="Initializing Model Weights...")
                time.sleep(0.2)
                progress_bar.progress(30, text="Preprocessing Image Dimensions...")
                
                # --- ADVANCED FEATURE: INFERENCE TIMER ---
                start_time = time.time()
                progress_bar.progress(60, text="Executing Deep Learning Inference...")
                result = mock_predict_stage(image, selected_stage)
                end_time = time.time()
                
                progress_bar.progress(90, text="Drawing Bounding Boxes...")
                time.sleep(0.2)
                progress_bar.progress(100, text="Scan Complete.")
                time.sleep(0.3)
                progress_bar.empty() # Remove progress bar once done
                
                # Display the image right here so it stays perfectly parallel
                if result.get("processed_image") is not None:
                    st.image(result["processed_image"], use_container_width=True)
                else:
                    st.error("Image processing failed.")

    # --- NEW TELEMETRY ROW (Below Images) ---
    if run_button and result["status"] == "success":
        st.divider()
        st.subheader("System Telemetry")
        
        # Clean up the message string exactly as requested
        clean_message = result['message'].replace("Inference complete. ", "")
        inference_speed = end_time - start_time
        
        # Create a 3-column metric row without the AI confidence section
        met1, met2, met3 = st.columns(3)
        met1.metric(label="Active Neural Network", value=result['routed_to'])
        met2.metric(label="Inspection Result", value=clean_message)
        met3.metric(label="Inference Time", value=f"{inference_speed:.2f} seconds")
        
        # --- ADVANCED FEATURE: ONE-CLICK EXPORT ---
        if result.get("processed_image") is not None:
            buf = BytesIO()
            result["processed_image"].save(buf, format="JPEG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="💾 Download Defect Report Image",
                data=byte_im,
                file_name="pcb_defect_report.jpg",
                mime="image/jpeg",
                use_container_width=True
            )