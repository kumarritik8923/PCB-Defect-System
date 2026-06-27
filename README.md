# Multi-Stage Automated PCB Defect Detection System with Intelligent Routing and AI Diagnostic Agent

## Overview

This project presents an end-to-end computer vision and conversational AI pipeline for automated defect detection across multiple stages of the Printed Circuit Board (PCB) manufacturing process.

The system automatically identifies the manufacturing stage of an input PCB image and routes it to a specialized defect detection model. In addition, an AI-powered assistant provides contextual explanations, root-cause analysis, and diagnostic support.

---

## Features

- Automatic PCB manufacturing stage classification using **YOLOv11-cls**
- Stage-specific defect detection using **YOLOv8/YOLOv11**
- High-resolution inference using **SAHI slicing**
- Interactive web interface built with **Streamlit**
- SQLite-based inspection history management
- AI-powered diagnostic assistant using **Gemini API**
- Manual detector override option
- Visualization of detected defects with confidence scores

---

## System Architecture

```text
                      [ Raw PCB Image Input ]
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │  Streamlit Input Buffer   │
                        └───────────────────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
     ┌───────────────────┐                         ┌───────────────────┐
     │ Automatic Routing │                         │ Manual Selection  │
     └───────────────────┘                         └───────────────────┘
               │                                             │
               ▼                                             │
   ┌───────────────────────┐                                 │
   │ YOLOv11-cls Router    │                                 │
   │ (Stage Classification)│                                 │
   └───────────────────────┘                                 │
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      │
                                      ▼
            ┌─────────────────────────┼─────────────────────────┐─┼─────────────────────────┐
            ▼                         ▼                         ▼                           ▼
  ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐       ┌───────────────────┐
  │ Stage 1 Detector  │     │ Stage 2 Detector  │     │ Stage 3 Detector  │       │ Stage 4 Detector  │
  │                   │     │  SAHI + YOLO      │     │                   │       │                   │
  └───────────────────┘     └───────────────────┘     └───────────────────┘       └───────────────────┘
            │                         │                         │                         │
            └─────────────────────────┼─────────────────────────┘─────────────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │      Result Logging       │
                        └───────────────────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
  ┌─────────────────────────┐                   ┌─────────────────────────┐
  │ SQLite Inspection Logs  │                   │ Gemini AI Assistant     │
  └─────────────────────────┘                   └─────────────────────────┘
```

---

## Project Structure

```text
Project_Name/
│
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml
│
├── app.py
│
├── assets/
│   ├── detected.jpg
│   └── original.jpg
│
├── backend/
│   ├── __init__.py
│   ├── ai_agent.py
│   ├── database.py
│   ├── inference.py
│   └── router.py
│
├── models/
│   └── router_classifier_best.pt
│   ├── stage1_best.pt
│   ├── stage2_sahi_best.pt
│   ├── stage3_best.pt
│   ├── stage4_side_best.pt
│   ├── stage4_top_best.pt
│
├── .gitignore
├── frontend_utils.py
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kumarritik8923/PCB-Defect-System/.git

cd your-repository-name
```

---

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

#### Activate Environment

**Linux/macOS**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

---

### 3. Install Dependencies

Upgrade pip:

```bash
pip install --upgrade pip
```

Install required packages:

```bash
pip install -r requirements.txt
```

---

## AI Diagnostic Assistant Setup

### Option 1: Gemini API (Recommended)

This project uses the Gemini API for conversational diagnostics.

### Steps

1. Visit: https://aistudio.google.com/
2. Sign in with your Google account.
3. Click **Get API Key**.
4. Generate a new API key.
5. Create a file:

```text
.streamlit/secrets.toml
```

6. Add your API key:

```toml
GEMINI_API_KEY = "YOUR_API_KEY"
```

---

### Option 2: Local LLM using Ollama

If your system has sufficient GPU memory (≥12GB VRAM):

Install Ollama from:

https://ollama.com/

Pull the Llama 3 model:

```bash
ollama pull llama3:8b
```

Enable local mode inside:

```python
# backend/ai_agent.py

USE_LOCAL_LLM = True
```

---

## Running the Application

Start the Streamlit server:

```bash
streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## How to Use

### Step 1: Upload PCB Image

Upload a PCB image (`.jpg`, `.jpeg`, `.png`) using the dashboard.

---

### Step 2: Automatic Stage Identification

The system automatically:

- Classifies the manufacturing stage.
- Routes the image to the appropriate defect detector.

---

### Step 3: Manual Override (Optional)

Users can manually select a detector from the sidebar if needed.

---

### Step 4: Inspect Results

The system displays:

- Defect bounding boxes
- Defect labels
- Confidence scores

---

### Step 5: View Inspection History

All inspections are stored in an SQLite database and can be viewed through the dashboard.

---

### Step 6: Interact with the AI Assistant

Ask questions such as:

- Why did this defect occur?
- What are the possible root causes?
- How can this defect be prevented?

The assistant provides contextual industrial recommendations.

---

## Technologies Used

- Python
- Streamlit
- YOLOv8
- YOLOv11
- SAHI
- SQLite
- Google Gemini API
- OpenCV
- Ultralytics

---

## Future Improvements

- Multi-user authentication
- Cloud deployment support
- Real-time production line monitoring
- Defect severity analysis
- Report generation in PDF format

---


---
