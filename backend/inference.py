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
    
    # Load the real Image Classification model
    router_model = YOLO("models/router_classifier_best.pt")
    
    stage2_sahi_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        model_path="models/stage2_sahi_best.pt",
        confidence_threshold=0.25,
        device="cpu" 
    )
    print("[SYSTEM] All Object Detection & Router models loaded successfully.")
except Exception as e:
    print(f"[SYSTEM ERROR] Could not load all models. Check your models/ folder. Error: {e}")

# --- 2. STANDARD INFERENCE FUNCTION (Used for Stage 1, 3, and 4) ---
def run_standard_yolo(image_pil, model, target_size):
    if model is None:
        return {"status": "error", "message": "Model weights missing."}

    image_resized = image_pil.resize((target_size, target_size))
    results = model.predict(source=image_resized, imgsz=target_size, conf=0.25)
    
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
    if 'stage2_sahi_model' not in globals():
         return {"status": "error", "message": "SAHI Model weights missing."}
    
    image_array = np.array(image_pil)

    result = get_sliced_prediction(
        image_array,
        stage2_sahi_model,
        slice_height=640,
        slice_width=640,
        overlap_height_ratio=0.2,
        overlap_width_ratio=0.2
    )

    result_image_array = image_array.copy()
    
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

# --- 5. PHASE 5 REAL ROUTER CLASSIFIER ---
def run_ai_classifier(image_pil):
    """
    Predicts which of the 5 stages the image belongs to using YOLO11-cls.
    """
    if 'router_model' not in globals():
        print("[WARNING] Router model missing. Defaulting to Stage 1.")
        return "Stage 1: Inked Board"
        
    results = router_model.predict(source=image_pil, imgsz=224)
    predicted_idx = results[0].probs.top1
    raw_class_name = results[0].names[predicted_idx]
    
    print(f"[SYSTEM] AI Raw Prediction: {raw_class_name}")
    
    mapping = {
        "Stage_1_InkedBoard": "Stage 1: Inked Board",
        "Stage_2_AcidEtch": "Stage 2: Acid Batch (Etched)",
        "Stage_3_GreenCoating": "Stage 3: Green Coating",
        "Stage_4_WeldingTop": "Stage 4: Component Welding (Top View)",
        "Stage_4_WeldingSide": "Stage 4: Component Welding (Side View)"
    }
    
    return mapping.get(raw_class_name, "Stage 1: Inked Board")