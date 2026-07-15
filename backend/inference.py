from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

# Default detection confidence (overridable per request from the UI).
DEFAULT_CONF = 0.25

# --- 1. GLOBAL MODEL LOADING ---
# Initialize to None so a failed load degrades gracefully instead of NameError.
stage1_model = None
stage3_model = None
stage4_top = None
stage4_side = None
router_model = None
stage2_sahi_model = None

try:
    stage1_model = YOLO("models/stage1_best.pt")
    stage3_model = YOLO("models/stage3_best.pt")
    stage4_top = YOLO("models/stage4_top_best.pt")
    stage4_side = YOLO("models/stage4_side_best.pt")
    router_model = YOLO("models/router_classifier_best.pt")

    stage2_sahi_model = AutoDetectionModel.from_pretrained(
        model_type='yolov8',
        model_path="models/stage2_sahi_best.pt",
        confidence_threshold=DEFAULT_CONF,
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
def run_standard_yolo(image_pil, model, target_size, is_segmentation=False, conf=DEFAULT_CONF):
    if model is None:
        return {"status": "error", "message": "Model weights missing."}

    # Convert to RGB (handles RGBA/grayscale) and let YOLO letterbox internally
    # instead of force-squishing to a square, which distorts aspect ratio.
    image_rgb = image_pil.convert("RGB")
    results = model.predict(source=image_rgb, imgsz=target_size, conf=conf)

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
def run_stage1_inference(image_pil, conf=DEFAULT_CONF):
    return run_standard_yolo(image_pil, stage1_model, target_size=640, conf=conf)

def run_stage3_inference(image_pil, conf=DEFAULT_CONF):
    return run_standard_yolo(image_pil, stage3_model, target_size=600, conf=conf)

def run_stage4_top_inference(image_pil, conf=DEFAULT_CONF):
    return run_standard_yolo(image_pil, stage4_top, target_size=1024, is_segmentation=True, conf=conf)

def run_stage4_side_inference(image_pil, conf=DEFAULT_CONF):
    return run_standard_yolo(image_pil, stage4_side, target_size=1024, is_segmentation=True, conf=conf)

# Distinct BGR colors reused for per-class SAHI boxes.
_SAHI_COLORS = [
    (255, 0, 0), (0, 200, 0), (0, 128, 255), (255, 0, 255),
    (0, 255, 255), (255, 128, 0), (128, 0, 255),
]

# --- 4. SAHI INFERENCE FUNCTION (Stage 2) ---
def run_stage2_sahi_inference(image_pil, conf=DEFAULT_CONF):
    if stage2_sahi_model is None:
        return {"status": "error", "message": "SAHI Model missing."}

    # SAHI expects a numpy array; ensure 3-channel RGB.
    image_array = np.array(image_pil.convert("RGB"))
    result = get_sliced_prediction(image_array, stage2_sahi_model, slice_height=640, slice_width=640)

    result_image_array = image_array.copy()
    detailed_defects = {}
    class_colors = {}

    kept = []
    for obj in result.object_prediction_list:
        score_val = getattr(getattr(obj, "score", None), "value", None)
        if isinstance(score_val, (int, float)) and score_val < conf:
            continue  # honor the per-request confidence slider
        kept.append(obj)

    for obj in kept:
        bbox = obj.bbox.to_xyxy()
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

        class_name = obj.category.name
        if class_name not in class_colors:
            class_colors[class_name] = _SAHI_COLORS[len(class_colors) % len(_SAHI_COLORS)]
        color = class_colors[class_name]

        score = getattr(getattr(obj, "score", None), "value", None)
        label = f"{class_name} {score:.2f}" if isinstance(score, (int, float)) else class_name

        cv2.rectangle(result_image_array, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        ty = max(y1, th + 4)
        cv2.rectangle(result_image_array, (x1, ty - th - 4), (x1 + tw + 2, ty), color, -1)
        cv2.putText(result_image_array, label, (x1 + 1, ty - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        detailed_defects[class_name] = detailed_defects.get(class_name, 0) + 1

    total_defects = len(kept)

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
    if router_model is None:
        return "Stage 1: Inked Board"

    results = router_model.predict(source=image_pil.convert("RGB"), imgsz=224)
    raw_class_name = results[0].names[results[0].probs.top1]
    
    mapping = {
        "Stage_1_InkedBoard": "Stage 1: Inked Board",
        "Stage_2_AcidEtch": "Stage 2: Acid Batch (Etched)",
        "Stage_3_GreenCoating": "Stage 3: Green Coating",
        "Stage_4_WeldingTop": "Stage 4: Component Welding (Top View)",
        "Stage_4_WeldingSide": "Stage 4: Component Welding (Side View)"
    }
    return mapping.get(raw_class_name, "Stage 1: Inked Board")