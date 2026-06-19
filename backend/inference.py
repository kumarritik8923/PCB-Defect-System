# backend/inference.py

from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

# --- 1. GLOBAL MODEL LOADING ---
try:
    stage1_model = YOLO("models/stage1_best.pt")
    stage3_model = YOLO("models/stage3_best.pt")
    stage4_top = YOLO("models/stage4_top_best.pt")
    stage4_side = YOLO("models/stage4_side_best.pt")
    
    # SAHI requires a special wrapper around the YOLO model
    stage2_sahi_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        model_path="models/stage2_sahi_best.pt",
        confidence_threshold=0.25,
        device="cpu" # Change to "cuda:0" if you have a GPU
    )
    print("[SYSTEM] All standard and SAHI models loaded successfully.")
except Exception as e:
    print(f"[SYSTEM ERROR] Could not load all models. Check your models/ folder. Error: {e}")

# --- 2. STANDARD INFERENCE FUNCTION (Used for Stage 1, 3, and 4) ---
def run_standard_yolo(image_pil, model, target_size):
    """A reusable function for standard YOLO inference."""
    if model is None:
        return {"status": "error", "message": "Model weights missing."}

    # Resize
    image_resized = image_pil.resize((target_size, target_size))
    
    # Predict
    results = model.predict(source=image_resized, imgsz=target_size, conf=0.25)
    
    # Format Image
    result_bgr = results[0].plot()
    result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
    
    defect_count = len(results[0].boxes)

    return {
        "status": "success",
        "processed_image": Image.fromarray(result_rgb),
        "message": f"Inference complete. Detected {defect_count} potential defects.",
    }

# --- 3. STAGE-SPECIFIC WRAPPERS ---
def run_stage1_inference(image_pil):
    return run_standard_yolo(image_pil, stage1_model, target_size=640)

def run_stage3_inference(image_pil):
    return run_standard_yolo(image_pil, stage3_model, target_size=600)

def run_stage4_top_inference(image_pil):
    return run_standard_yolo(image_pil, stage4_top, target_size=1024)

def run_stage4_side_inference(image_pil):
    return run_standard_yolo(image_pil, stage4_side, target_size=1024)

# --- 4. SAHI INFERENCE FUNCTION (Stage 2) ---
def run_stage2_sahi_inference(image_pil):
    """Specialized function executing the Slicing Aided Hyper Inference."""
    if 'stage2_sahi_model' not in globals():
         return {"status": "error", "message": "SAHI Model weights missing."}
    
    # Convert PIL to Numpy array (RGB) for SAHI and drawing
    image_array = np.array(image_pil)

    # Execute SAHI Slicing (Chops into 640x640 tiles with 20% overlap)
    result = get_sliced_prediction(
        image_array,
        stage2_sahi_model,
        slice_height=640,
        slice_width=640,
        overlap_height_ratio=0.2,
        overlap_width_ratio=0.2
    )

    # THE FIX: Create a fresh copy of our original NumPy array to draw on
    result_image_array = image_array.copy()
    
    # Draw SAHI bounding boxes manually using OpenCV
    for object_prediction in result.object_prediction_list:
        bbox = object_prediction.bbox.to_xyxy()
        cv2.rectangle(result_image_array, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 0, 0), 2)
        cv2.putText(result_image_array, object_prediction.category.name, (int(bbox[0]), int(bbox[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)

    defect_count = len(result.object_prediction_list)

    return {
        "status": "success",
        "processed_image": Image.fromarray(result_image_array),
        "message": f"SAHI Inference complete. Detected {defect_count} microscopic defects.",
    }


# --- 5. PHASE 5 ROUTER CLASSIFIER (Placeholder) ---

# When you train your classifier, you will uncomment this:
# router_model = YOLO("models/router_classifier_best.pt")

def run_ai_classifier(image_pil):
    """
    Predicts which of the 5 stages the image belongs to.
    Currently acts as a placeholder until the model is trained.
    """
    # TODO: Replace this block with real YOLO classification logic later
    # results = router_model.predict(image_pil)
    # predicted_class_name = results[0].names[results[0].probs.top1]
    # return predicted_class_name
    
    # For testing right now, we will just force it to predict Stage 1
    # so we can verify the Auto-Detect logic works.
    print("[SYSTEM] Running AI Classifier Placeholder...")
    dummy_prediction = "Stage 1: Bare Board"
    return dummy_prediction