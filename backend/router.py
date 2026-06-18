# backend/router.py

def mock_predict_stage(image, manual_selection):
    """
    A temporary mock function to simulate the 5-class Router CNN.
    In Phase 5, this will be replaced with actual YOLO inference.
    """
    print(f"[BACKEND] Receiving image for routing. Manual override: {manual_selection}")
    
    # Initialize a default response dictionary
    response = {
        "status": "success",
        "routed_to": None,
        "message": ""
    }

    # The Routing Logic Pipeline
    if manual_selection == "Stage 1: Bare Board":
        print("[BACKEND] Routing to Stage 1 Pipeline (640x640)")
        response["routed_to"] = "Stage 1"
        response["message"] = "Simulated output for bare board defects (shorts, mousebites)."

    elif manual_selection == "Stage 2: Solder Paste (SAHI)":
        print("[BACKEND] Routing to Stage 2 Pipeline (SAHI Slicing)")
        response["routed_to"] = "Stage 2"
        response["message"] = "Simulated output for solder paste defects using SAHI."

    elif manual_selection == "Stage 3: Component Placement":
        print("[BACKEND] Routing to Stage 3 Pipeline (600x600)")
        response["routed_to"] = "Stage 3"
        response["message"] = "Simulated output for placement defects."

    elif manual_selection == "Stage 4: Final Assembly (Top View)":
        print("[BACKEND] Routing to Stage 4 Top-View Pipeline (1024x1024)")
        response["routed_to"] = "Stage 4 (Top)"
        response["message"] = "Simulated output for top-view assembly defects."

    elif manual_selection == "Stage 4: Final Assembly (Side View)":
        print("[BACKEND] Routing to Stage 4 Side-View Pipeline (1024x1024)")
        response["routed_to"] = "Stage 4 (Side)"
        response["message"] = "Simulated output for side-view assembly defects."

    else:
        print("[BACKEND] ERROR: Unknown stage selected.")
        response["status"] = "error"
        response["message"] = "Failed to route image."

    return response