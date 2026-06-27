import sqlite3
import os
import json
import time
from google import genai 
import requests

DB_PATH = "pcb_database.db"

DATABASE_SCHEMA = """
Table: inference_logs
Columns: 
- id (INTEGER): The unique ID of the inspection.
- timestamp (DATETIME): When the inspection happened.
- detected_stage (TEXT): The manufacturing stage (e.g., 'Stage 3').
- total_defects (INTEGER): The sum of all defects found in the image.
- granular_details (TEXT): A JSON dictionary of specific defects (e.g., '{"Mousebite": 2}').
- image_path (TEXT): Where the image is saved.
"""

ENGINEERING_CONTEXT = """
================ PCB AOI ENGINEERING KNOWLEDGE BASE ================

You are a Senior PCB Manufacturing and Quality Assurance Engineer.

Your task:
1. Explain detected defects.
2. Identify probable root causes.
3. Recommend ACCEPT, REWORK + REINSPECT or SCRAP.
4. Consider BOTH manufacturing stage and defect type before deciding.

---------------- FINAL DECISION OPTIONS ----------------

ACCEPT
- Board satisfies quality requirements.

REWORK + REINSPECT
- Defect can be repaired reliably.
- Board must be inspected again after repair.

SCRAP
- Defect cannot be repaired reliably or economically.

Never recommend SCRAP unless defect severity justifies it.

====================================================================
STAGE 1 : INKED BOARD INSPECTION
Purpose:
Verify that manufactured copper artwork matches the design blueprint.

Typical Defects:
mouse_bite, spur, missing_hole, short, open_circuit, spurious_copper

Decision Guidelines:

- spur, spurious_copper:
  Usually removable -> REWORK + REINSPECT

- mouse_bite:
  Minor damage -> REWORK
  Severe conductor loss -> SCRAP

- open_circuit:
  External trace -> REWORK
  Large or critical trace damage -> SCRAP

- short:
  Surface copper bridge -> REWORK

- missing_hole:
  Electrical via missing -> SCRAP

====================================================================
STAGE 2 : POST ETCH INSPECTION
Purpose:
Inspect physical copper traces after etching.

Defects found at this stage are generally more severe because copper has already been permanently processed.

Decision Guidelines:

- spur, spurious_copper:
  Usually repairable -> REWORK

- short:
  Surface bridge -> REWORK
  Internal short -> SCRAP

- open_circuit:
  Accessible trace -> REWORK
  Critical/high-speed trace -> SCRAP

- mouse_bite:
  Minor -> REWORK
  Severe -> SCRAP

- missing_hole:
  Usually SCRAP

====================================================================
STAGE 3 : GREEN SOLDER MASK INSPECTION
Purpose:
Inspect board after protective coating application.

Typical Defects:
mouse_bite, spur, missing_hole, short, open_circuit, spurious_copper

Because solder mask is already applied, repairs become more difficult.

Decision Guidelines:

- spur, spurious_copper:
  REWORK if accessible.

- open_circuit:
  REWORK only if conductor accessible.

- short:
  REWORK if accessible.

- severe conductor damage:
  SCRAP.

- missing electrical hole:
  SCRAP.

====================================================================
STAGE 4 TOP VIEW : COMPONENT PLACEMENT INSPECTION

good_placed:
ACCEPT.

not_good:
Component placement error.

Probable Causes:
- Pick-and-place calibration error.
- Nozzle issue.
- Vision alignment error.

Action:
Usually REWORK + REINSPECT.

====================================================================
STAGE 4 SIDE VIEW : SOLDER JOINT INSPECTION

good:
ACCEPT.

excess_solder:
REWORK + REINSPECT.

poor_solder:
REWORK + REINSPECT.

spike:
REWORK + REINSPECT.

Root Causes:
- Incorrect solder paste volume.
- Improper reflow profile.
- Flux contamination.

====================================================================
RESPONSE FORMAT

### Defect Analysis

### Possible Root Cause

### Recommended Action
(ACCEPT / REWORK + REINSPECT / SCRAP)

### Manufacturing Recommendation

### Severity
(LOW / MEDIUM / HIGH / CRITICAL)

Rules:

1. Always consider manufacturing stage before deciding.
2. If multiple defects exist, prioritize the most severe defect.
3. If any defect is non-repairable, final recommendation should be SCRAP.
4. Never invent measurements or process parameters.
5. If insufficient information exists, state uncertainty clearly.

====================================================================
"""

def execute_read_query(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if "DROP" in query.upper() or "DELETE" in query.upper() or "UPDATE" in query.upper():
            return "Error: Modifying the database is not allowed."
            
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return f"SQL Execution Error: {e}"

def ask_database(user_question, engine="Cloud Engine (Gemini)", api_key=""):
    sql_prompt = f"""
    You are an AI Factory Data Analyst and Senior PCB QA Engineer.
    
    Database Schema: {DATABASE_SCHEMA}
    {ENGINEERING_CONTEXT}
    
    User Input: "{user_question}"
    
    INSTRUCTIONS:
    1. If the user asks to look up factory records, trends, or stats, return ONLY a valid SQLite query starting with "SQL: "
       Example: SQL: SELECT COUNT(*) FROM inference_logs
       
    2. If the user asks a general engineering question (e.g., "what to do if a board is defective?"), a greeting, or anything not requiring database lookup, answer directly starting with "CHAT: "
       Example: CHAT: If a board has a short circuit, standard protocol dictates...
    """
    
    raw_response = ""
    client = None
    
    if engine == "Cloud Engine (Gemini)":
        if not api_key: return "Error: Provide Gemini API Key in secrets."
        try:
            client = genai.Client(api_key=api_key)
            for attempt in range(4):
                try:
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=sql_prompt)
                    raw_response = response.text.strip()
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "503" in error_msg or "exhausted" in error_msg.lower():
                        wait_time = 10 * (2 ** attempt) 
                        print(f"[SYSTEM] Rate limit/High demand. Pausing for {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"Gemini API Error: {error_msg}"
            if not raw_response: return "Gemini Error: Rate limit exhausted after retries. Please wait 1 minute."
        except Exception as e:
            return f"Gemini Initialization Error: {e}"
            
    elif engine == "Local Engine (Llama 3)":
        try:
            res = requests.post("http://localhost:11434/api/generate", json={
                "model": "llama3:8b", "prompt": sql_prompt, "stream": False
            }, timeout=180)
            raw_response = res.json().get("response", "").strip()
        except Exception as e:
            return "⚠️ **Local Engine Offline:** Ensure Ollama is running (`ollama run llama3:8b`)."

    upper_resp = raw_response.upper()
    
    # CASE A: Database Query
    if upper_resp.startswith("SQL:") or "SELECT " in upper_resp:
        sql_query = raw_response.replace("SQL:", "").replace("sql:", "").strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").replace(";", "")
        
        db_results = execute_read_query(sql_query)
        
        translation_prompt = f"""
        User Question: "{user_question}"
        Raw Database Result: {db_results}
        {ENGINEERING_CONTEXT}
        
        Act as a highly intelligent PCB Data Analyst. 
        Answer the user's question directly based ONLY on the raw data provided. Apply engineering context if asked for advice.
        Do NOT mention "the database" or "raw data". Speak naturally.
        """
        
        friendly_answer = ""
        
        if engine == "Cloud Engine (Gemini)":
            try:
                for attempt in range(4):
                    try:
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=translation_prompt)
                        friendly_answer = response.text.strip()
                        break
                    except Exception as e:
                        if "429" in str(e) or "503" in str(e):
                            time.sleep(10 * (2 ** attempt))
                            continue
                        else:
                            friendly_answer = f"Raw Data: {db_results}" 
                            break
                if not friendly_answer: friendly_answer = f"Raw Data: {db_results}"
            except Exception as e:
                friendly_answer = f"Raw Data: {db_results}" 
                
        elif engine == "Local Engine (Llama 3)":
            try:
                res = requests.post("http://localhost:11434/api/generate", json={
                    "model": "llama3:8b", "prompt": translation_prompt, "stream": False
                })
                friendly_answer = res.json().get("response", "").strip()
            except Exception as e:
                friendly_answer = f"⚠️ Local translation offline. Raw Data: `{db_results}`"

        return {
            "sql_query": sql_query,
            "raw_results": db_results,
            "friendly_answer": friendly_answer
        }

    # CASE B: Dynamic Conversation 
    elif upper_resp.startswith("CHAT:"):
        clean_msg = raw_response[5:].strip()
        return {"sql_query": None, "raw_results": None, "friendly_answer": clean_msg}
        
    # CASE C: Forgiving Fallback
    else:
        return {"sql_query": None, "raw_results": None, "friendly_answer": raw_response.strip()}