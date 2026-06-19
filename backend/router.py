from .inference import (
    run_stage1_inference, 
    run_stage2_sahi_inference, 
    run_stage3_inference, 
    run_stage4_top_inference, 
    run_stage4_side_inference,
    run_ai_classifier 
)

def mock_predict_stage(image, selection):
    
    response = {"status": "success", "routed_to": None, "message": "", "processed_image": None}
    
    # --- HYBRID ROUTING LOGIC ---
    if selection == "Auto-Detect Stage (AI)":
        print("[BACKEND] Auto-Detect selected. Passing to real AI Classifier...")
        active_stage = run_ai_classifier(image)
        print(f"[BACKEND] AI Predicted: {active_stage}")
        # UI FIX: Removed the clunky "AI Auto-Detected: " text injection here!
    else:
        active_stage = selection
        print(f"[BACKEND] Manual Override active: {active_stage}")

    # --- EXECUTE THE ACTIVE STAGE ---
    if active_stage == "Stage 1: Inked Board":
        print("[BACKEND] Executing Stage 1 (640x640)")
        res = run_stage1_inference(image)
        
    elif active_stage == "Stage 2: Acid Batch (Etched)":
        print("[BACKEND] Executing Stage 2 SAHI Pipeline")
        res = run_stage2_sahi_inference(image)
        
    elif active_stage == "Stage 3: Green Coating":
        print("[BACKEND] Executing Stage 3 (600x600)")
        res = run_stage3_inference(image)
        
    elif active_stage == "Stage 4: Component Welding (Top View)":
        print("[BACKEND] Executing Stage 4 Top-View (1024x1024)")
        res = run_stage4_top_inference(image)
        
    elif active_stage == "Stage 4: Component Welding (Side View)":
        print("[BACKEND] Executing Stage 4 Side-View (1024x1024)")
        res = run_stage4_side_inference(image)
        
    else:
        return {"status": "error", "message": f"Unknown stage routing failure: {active_stage}"}

    # Map the clean inference results back to the frontend response
    if res["status"] == "success":
        response["routed_to"] = active_stage.split(':')[0] # Clean up the name (e.g., "Stage 3")
        response["message"] = res["message"] # Kept entirely clean!
        response["processed_image"] = res.get("processed_image")
    else:
        response["status"] = "error"
        response["message"] = res["message"]

    return response