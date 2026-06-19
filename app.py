import streamlit as st
from PIL import Image

# Import our backend logic
from backend.router import mock_predict_stage

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PCB Defect Detection",
    page_icon="🔍",
    layout="centered"
)

st.title("PCB Defect Detection System")
st.markdown("Upload a PCB image to detect manufacturing defects across different assembly stages.")
st.divider()

# --- UPLOAD SECTION ---
uploaded_file = st.file_uploader("Choose a PCB image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.subheader("Uploaded Image")
    st.image(image, caption="Ready for inspection", use_container_width=True)
    st.divider()
    
    # --- PHASE 5: HYBRID ROUTER UI ---
    st.subheader("System Configuration")
    
    # UPDATED: Industrial stage names matching the real physical process
    stage_options = [
        "Auto-Detect Stage (AI)", 
        "Stage 1: Inked Board",
        "Stage 2: Acid Batch (Etched)",
        "Stage 3: Green Coating",
        "Stage 4: Component Welding (Top View)",
        "Stage 4: Component Welding (Side View)"
    ]
    selected_stage = st.selectbox("Pipeline Routing Mode:", stage_options)
    
    # --- EXECUTION BUTTON ---
    if st.button("Run Inspection", type="primary"):
        with st.spinner('Running AI Inference Pipeline...'):
            
            # Send the image and selection to our backend router
            result = mock_predict_stage(image, selected_stage)
            
            if result["status"] == "success":
                st.success(f"Successfully routed to: **{result['routed_to']}**")
                st.write(f"**Backend Message:** {result['message']}")
                
                # Display the processed image if it exists
                if result.get("processed_image") is not None:
                    st.subheader("Defect Analysis Result")
                    st.image(result["processed_image"], caption=f"Output from {result['routed_to']} Model", use_container_width=True)
            else:
                st.error(f"Error: {result['message']}")

else:
    st.info("Please upload an image to begin.")