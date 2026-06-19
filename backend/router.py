# backend/router.py

from .inference import (
    run_stage1_inference, 
    run_stage2_sahi_inference, 
    run_stage3_inference, 
    run_stage4_top_inference, 
    run_stage4_side_inference
)

def mock_predict_stage(image, manual_selection):
    print(f"[BACKEND] Routing override: {manual_selection}")
    
    response = {"status": "success", "routed_to": None, "message": "", "processed_image": None}

    if manual_selection == "Stage 1: Bare Board":
        print("[BACKEND] Executing Stage 1 (640x640)")
        res = run_stage1_inference(image)
        
    elif manual_selection == "Stage 2: Solder Paste (SAHI)":
        print("[BACKEND] Executing Stage 2 SAHI Pipeline")
        res = run_stage2_sahi_inference(image)
        
    elif manual_selection == "Stage 3: Component Placement":
        print("[BACKEND] Executing Stage 3 (600x600)")
        res = run_stage3_inference(image)
        
    elif manual_selection == "Stage 4: Final Assembly (Top View)":
        print("[BACKEND] Executing Stage 4 Top-View (1024x1024)")
        res = run_stage4_top_inference(image)
        
    elif manual_selection == "Stage 4: Final Assembly (Side View)":
        print("[BACKEND] Executing Stage 4 Side-View (1024x1024)")
        res = run_stage4_side_inference(image)
        
    else:
        return {"status": "error", "message": "Unknown stage."}

    # Map the inference results back to the frontend response
    if res["status"] == "success":
        response["routed_to"] = manual_selection.split(':')[0]
        response["message"] = res["message"]
        response["processed_image"] = res.get("processed_image")
    else:
        response["status"] = "error"
        response["message"] = res["message"]

    return response