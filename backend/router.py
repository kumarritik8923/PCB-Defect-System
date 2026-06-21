from .inference import (
    run_stage1_inference, 
    run_stage2_sahi_inference, 
    run_stage3_inference, 
    run_stage4_top_inference, 
    run_stage4_side_inference,
    run_ai_classifier 
)

def mock_predict_stage(image, selection):
    response = {"status": "success", "routed_to": None, "message": "", "processed_image": None, "details_dict": {}}
    
    if selection == "Auto-Detect Stage (AI)":
        active_stage = run_ai_classifier(image)
    else:
        active_stage = selection

    if active_stage == "Stage 1: Inked Board":
        res = run_stage1_inference(image)
    elif active_stage == "Stage 2: Acid Batch (Etched)":
        res = run_stage2_sahi_inference(image)
    elif active_stage == "Stage 3: Green Coating":
        res = run_stage3_inference(image)
    elif active_stage == "Stage 4: Component Welding (Top View)":
        res = run_stage4_top_inference(image)
    elif active_stage == "Stage 4: Component Welding (Side View)":
        res = run_stage4_side_inference(image)
    else:
        return {"status": "error", "message": f"Unknown routing failure: {active_stage}"}

    if res["status"] == "success":
        response["routed_to"] = active_stage.split(':')[0]
        response["message"] = res["message"] 
        response["processed_image"] = res.get("processed_image")
        response["details_dict"] = res.get("details_dict", {}) 
        response["total_defects"] = res.get("total_defects", 0)
    else:
        response["status"] = "error"
        response["message"] = res["message"]

    return response
