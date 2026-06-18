# app.py

import streamlit as st
from PIL import Image

# Import our backend logic
from backend.router import mock_predict_stage

st.set_page_config(
    page_title="PCB Defect Detection",
    page_icon="🔍",
    layout="centered"
)

st.title("PCB Defect Detection System")
st.markdown("Upload a PCB image to detect manufacturing defects across different assembly stages.")
st.divider()

uploaded_file = st.file_uploader("Choose a PCB image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.subheader("Uploaded Image")
    st.image(image, caption="Ready for inspection", use_container_width=True)
    st.divider()
    
    # --- PHASE 2: MOCK ROUTER UI ---
    st.subheader("System Configuration")
    st.info("The 5-class Router CNN is currently bypassed. Please manually select the stage to test the backend routing.")
    
    # Dropdown menu to simulate the AI prediction
    stage_options = [
        "Stage 1: Bare Board",
        "Stage 2: Solder Paste (SAHI)",
        "Stage 3: Component Placement",
        "Stage 4: Final Assembly (Top View)",
        "Stage 4: Final Assembly (Side View)"
    ]
    selected_stage = st.selectbox("Mock AI Prediction (Select Stage):", stage_options)
    
    # --- EXECUTION BUTTON ---
    if st.button("Run Inspection", type="primary"):
        with st.spinner('Running AI Inference Pipeline...'):
            
            result = mock_predict_stage(image, selected_stage)
            
            if result["status"] == "success":
                st.success(f"Successfully routed to: **{result['routed_to']}**")
                st.write(f"**Backend Message:** {result['message']}")
                
                # NEW: If the backend returned a processed image, display it!
                if result.get("processed_image") is not None:
                    st.subheader("Defect Analysis Result")
                    st.image(result["processed_image"], caption=f"Output from {result['routed_to']} Model", use_container_width=True)
            else:
                st.error(f"Error: {result['message']}")

else:
    st.info("Please upload an image to begin.")