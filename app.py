import streamlit as st
from PIL import Image

# --- PAGE CONFIGURATION ---
# This sets the browser tab title and layout
st.set_page_config(
    page_title="PCB Defect Detection",
    page_icon="🔍",
    layout="centered"
)

# --- HEADER SECTION ---
st.title("PCB Defect Detection System")
st.markdown("Upload a PCB image to detect manufacturing defects across different assembly stages.")
st.divider()

# --- UPLOAD SECTION ---
# Create a drag-and-drop file uploader restricted to standard image formats
uploaded_file = st.file_uploader("Choose a PCB image...", type=["jpg", "jpeg", "png"])

# --- DISPLAY SECTION ---
# Check if the user has actually uploaded a file before trying to process it
if uploaded_file is not None:
    
    # Read the image file into memory
    image = Image.open(uploaded_file)
    
    # Display the raw uploaded image to the user
    st.subheader("Uploaded Image")
    st.image(image, caption="Ready for inspection", use_container_width=True)
    
    # Placeholder button for the future ML pipeline
    st.divider()
    if st.button("Run Inspection", type="primary"):
        # We use st.info to show a temporary UI message
        st.info("Machine Learning backend is not yet connected. This will trigger the routing pipeline in Phase 2.")

else:
    # Prompt the user to take action if the upload box is empty
    st.info("Please upload an image to begin.")