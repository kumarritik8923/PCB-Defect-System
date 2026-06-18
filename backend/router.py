# backend/router.py

# Import our new inference function
from .inference import run_stage1_inference

def mock_predict_stage(image, manual_selection):
    print(f"[BACKEND] Receiving image for routing. Manual override: {manual_selection}")
    
    response = {
        "status": "success",
        "routed_to": None,
        "message": "",
        "processed_image": None # New key to hold the final image
    }

    if manual_selection == "Stage 1: Bare Board":
        print("[BACKEND] Routing to Stage 1 Pipeline (640x640)")
        
        # Execute real ML inference
        inference_result = run_stage1_inference(image)
        
        if inference_result["status"] == "success":
            response["routed_to"] = "Stage 1"
            response["message"] = inference_result["message"]
            response["processed_image"] = inference_result["processed_image"]
        else:
            response["status"] = "error"
            response["message"] = inference_result["message"]

    # ... [Keep your other elif blocks for Stage 2, 3, 4 exactly as they were in Phase 2] ...
    elif manual_selection == "Stage 2: Solder Paste (SAHI)":
        response["routed_to"] = "Stage 2"
        response["message"] = "Simulated output for solder paste defects using SAHI."

    elif manual_selection == "Stage 3: Component Placement":
        response["routed_to"] = "Stage 3"
        response["message"] = "Simulated output for placement defects."
        
    elif manual_selection == "Stage 4: Final Assembly (Top View)":
        response["routed_to"] = "Stage 4 (Top)"
        response["message"] = "Simulated output for top-view assembly defects."

    elif manual_selection == "Stage 4: Final Assembly (Side View)":
        response["routed_to"] = "Stage 4 (Side)"
        response["message"] = "Simulated output for side-view assembly defects."

    else:
        response["status"] = "error"
        response["message"] = "Failed to route image."

    return response