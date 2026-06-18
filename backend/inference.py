# backend/inference.py

from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import os

# Load the model globally so it doesn't reload from the hard drive on every single click
MODEL_PATH = "models/stage1_best.pt"

try:
    # Initialize the YOLO model
    stage1_model = YOLO(MODEL_PATH)
    print("[SYSTEM] Stage 1 Model loaded successfully.")
except Exception as e:
    stage1_model = None
    print(f"[SYSTEM ERROR] Could not load Stage 1 Model. Error: {e}")

def run_stage1_inference(image_pil):
    """
    Takes a PIL Image, runs Stage 1 YOLO inference, and returns the processed image.
    """
    if stage1_model is None:
        return {"status": "error", "message": "Model weights not found. Please place 'stage1_best.pt' in the models/ folder."}

    # 1. Resize the image to 640x640 as required by Stage 1 architecture
    image_resized = image_pil.resize((640, 640))
    
    # 2. Run the YOLO inference. conf=0.25 ignores very low-confidence predictions
    results = stage1_model.predict(source=image_resized, imgsz=640, conf=0.25)
    
    # 3. Extract the image array with the bounding boxes already drawn on it
    # YOLO returns images in BGR format (OpenCV standard)
    result_bgr_array = results[0].plot()
    
    # 4. Convert BGR back to RGB so Streamlit (which uses PIL) displays colors correctly
    result_rgb_array = cv2.cvtColor(result_bgr_array, cv2.COLOR_BGR2RGB)
    
    # 5. Convert the numpy array back to a PIL Image object
    final_processed_image = Image.fromarray(result_rgb_array)
    
    # Count how many defects were found (number of bounding boxes)
    defect_count = len(results[0].boxes)

    return {
        "status": "success",
        "processed_image": final_processed_image,
        "message": f"Inference complete. Detected {defect_count} potential defects.",
        "defect_count": defect_count
    }