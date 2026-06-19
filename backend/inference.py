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
    router_model = YOLO("models/router_classifier_best.pt")
    
    stage2_sahi_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        model_path="models/stage2_sahi_best.pt",
        confidence_threshold=0.25,
        device="cpu" 
    )
    print("[SYSTEM] All Object Detection, Segmentation, & Router models loaded.")
except Exception as e:
    print(f"[SYSTEM ERROR] Could not load models. Error: {e}")

# --- NEW: DETAILED EXTRACTION FUNCTION ---
def extract_detailed_results(results, model, is_segmentation=False):
    details = {}
    
    if results[0].boxes is not None:
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            details[class_name] = details.get(class_name, 0) + 1
            
    if is_segmentation and results[0].masks is not None:
        total_area = 0
        for mask in results[0].masks.data:
            pixel_area = mask.sum().item() 
            total_area += pixel_area
        details["Total_Defect_Area_Pixels"] = round(total_area)
        
    return details

# --- 2. STANDARD INFERENCE FUNCTION ---
def run_standard_yolo(image_pil, model, target_size, is_segmentation=False):
    if model is None:
        return {"status": "error", "message": "Model weights missing."}

    image_resized = image_pil.resize((target_size, target_size))
    results = model.predict(source=image_resized, imgsz=target_size, conf=0.25)
    
    result_bgr = results[0].plot()
    result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
    
    detailed_defects = extract_detailed_results(results, model, is_segmentation)
    total_defects = sum(count for key, count in detailed_defects.items() if key != "Total_Defect_Area_Pixels")

    if total_defects == 0:
        msg = "Board Pass: No defects detected."
    else:
        defect_str = ", ".join([f"{k}: {v}" for k, v in detailed_defects.items()])
        msg = f"Defects Found ({total_defects}) -> {defect_str}"

    return {
        "status": "success",
        "processed_image": Image.fromarray(result_rgb),
        "message": msg,
        "details_dict": detailed_defects,
        "total_defects": total_defects
    }

# --- 3. STAGE-SPECIFIC WRAPPERS ---
def run_stage1_inference(image_pil):
    return run_standard_yolo(image_pil, stage1_model, target_size=640)

def run_stage3_inference(image_pil):
    return run_standard_yolo(image_pil, stage3_model, target_size=600)

def run_stage4_top_inference(image_pil):
    return run_standard_yolo(image_pil, stage4_top, target_size=1024, is_segmentation=True)

def run_stage4_side_inference(image_pil):
    return run_standard_yolo(image_pil, stage4_side, target_size=1024, is_segmentation=True)

# --- 4. SAHI INFERENCE FUNCTION (Stage 2) ---
def run_stage2_sahi_inference(image_pil):
    if 'stage2_sahi_model' not in globals():
         return {"status": "error", "message": "SAHI Model missing."}
    
    image_array = np.array(image_pil)
    result = get_sliced_prediction(image_array, stage2_sahi_model, slice_height=640, slice_width=640)

    result_image_array = image_array.copy()
    detailed_defects = {}
    
    for obj in result.object_prediction_list:
        bbox = obj.bbox.to_xyxy()
        cv2.rectangle(result_image_array, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (255, 0, 0), 2)
        
        class_name = obj.category.name
        detailed_defects[class_name] = detailed_defects.get(class_name, 0) + 1

    total_defects = len(result.object_prediction_list)
    
    if total_defects == 0:
        msg = "Board Pass: No microscopic defects detected."
    else:
        defect_str = ", ".join([f"{k}: {v}" for k, v in detailed_defects.items()])
        msg = f"Micro-Defects Found ({total_defects}) -> {defect_str}"

    return {
        "status": "success",
        "processed_image": Image.fromarray(result_image_array),
        "message": msg,
        "details_dict": detailed_defects,
        "total_defects": total_defects
    }

# --- 5. ROUTER CLASSIFIER ---
def run_ai_classifier(image_pil):
    if 'router_model' not in globals():
        return "Stage 1: Inked Board"
        
    results = router_model.predict(source=image_pil, imgsz=224)
    raw_class_name = results[0].names[results[0].probs.top1]
    
    mapping = {
        "Stage_1_InkedBoard": "Stage 1: Inked Board",
        "Stage_2_AcidEtch": "Stage 2: Acid Batch (Etched)",
        "Stage_3_GreenCoating": "Stage 3: Green Coating",
        "Stage_4_WeldingTop": "Stage 4: Component Welding (Top View)",
        "Stage_4_WeldingSide": "Stage 4: Component Welding (Side View)"
    }
    return mapping.get(raw_class_name, "Stage 1: Inked Board")