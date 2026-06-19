# backend/router.py

from .inference import (
    run_stage1_inference, 
    run_stage2_sahi_inference, 
    run_stage3_inference, 
    run_stage4_top_inference, 
    run_stage4_side_inference,
    run_ai_classifier # Import the new classifier function
)

def mock_predict_stage(image, selection):
    
    response = {"status": "success", "routed_to": None, "message": "", "processed_image": None}
    
    # --- HYBRID ROUTING LOGIC ---
    if selection == "Auto-Detect Stage (AI)":
        print("[BACKEND] Auto-Detect selected. Passing to AI Classifier...")
        active_stage = run_ai_classifier(image)
        print(f"[BACKEND] AI Predicted: {active_stage}")
        response["message"] += f"**AI Auto-Detected:** {active_stage}. "
    else:
        active_stage = selection
        print(f"[BACKEND] Manual Override active: {active_stage}")
        response["message"] += f"**Manual Override:** {active_stage}. "

    # --- EXECUTE THE ACTIVE STAGE ---
    if active_stage == "Stage 1: Bare Board":
        res = run_stage1_inference(image)
        
    elif active_stage == "Stage 2: Solder Paste (SAHI)":
        res = run_stage2_sahi_inference(image)
        
    elif active_stage == "Stage 3: Component Placement":
        res = run_stage3_inference(image)
        
    elif active_stage == "Stage 4: Final Assembly (Top View)":
        res = run_stage4_top_inference(image)
        
    elif active_stage == "Stage 4: Final Assembly (Side View)":
        res = run_stage4_side_inference(image)
        
    else:
        return {"status": "error", "message": "Unknown stage routing failure."}

    # Map results
    if res["status"] == "success":
        response["routed_to"] = active_stage.split(':')[0] # Clean up the name for UI
        response["message"] += res["message"]
        response["processed_image"] = res.get("processed_image")
    else:
        response["status"] = "error"
        response["message"] = res["message"]

    return response