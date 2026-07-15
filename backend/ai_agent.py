import sqlite3
import os
import json
import time
from google import genai 
import requests

DB_PATH = "pcb_database.db"

# Pinned model — do NOT auto-update per user request.
GEMINI_MODEL = "gemini-3.1-flash-lite"

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
        # Read-only allowlist: only permit a single SELECT statement.
        cleaned = query.strip().rstrip(";").strip()
        if not cleaned.upper().startswith("SELECT"):
            return "Error: Only read-only SELECT queries are allowed."
        if ";" in cleaned:  # block stacked/multiple statements
            return "Error: Multiple statements are not allowed."

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(cleaned)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return f"SQL Execution Error: {e}"

class LLMError(Exception):
    """Raised when the selected engine cannot produce a response."""


def _call_gemini(client, prompt):
    last_err = ""
    for attempt in range(4):
        try:
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            return (response.text or "").strip()
        except Exception as e:
            last_err = str(e)
            if "429" in last_err or "503" in last_err or "exhausted" in last_err.lower():
                wait_time = 5 * (2 ** attempt)
                print(f"[SYSTEM] Rate limit/High demand. Pausing for {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise LLMError(f"Gemini API Error: {last_err}")
    raise LLMError("Gemini Error: Rate limit exhausted after retries. Please wait a minute.")


def _call_llama(prompt):
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 512},
            },
            timeout=90,
        )
        return res.json().get("response", "").strip()
    except Exception:
        raise LLMError("⚠️ **Local Engine Offline:** Ensure Ollama is running (`ollama run llama3:8b`).")


def _generate(engine, prompt, api_key, client):
    """Route a single prompt to the active engine and return raw text."""
    if engine == "Cloud Engine (Gemini)":
        return _call_gemini(client, prompt)
    return _call_llama(prompt)


ROUTER_PROMPT = """You are an autonomous PCB AOI Factory Agent. You have two capabilities:
(A) query the factory inspection database, and (B) answer as a Senior PCB QA Engineer.

Decide which ONE capability answers the user's message, then respond with EXACTLY one line
using one of these prefixes — never both, never neither, never any other text before it:

  SQL: <a single valid read-only SQLite SELECT statement>
  CHAT: <a direct engineering answer>

Use SQL when the user asks about stored inspections, counts, trends, a specific image/board,
"how many defects", "what stage", "what should I do with image N", or any question that needs
factory records. When the user references a specific board/image number N, scope the query by id.

Database schema:
{schema}

Examples:
  User: how many inspections total?           -> SQL: SELECT COUNT(*) FROM inference_logs
  User: how many defects in image 5?          -> SQL: SELECT id, detected_stage, total_defects, granular_details FROM inference_logs WHERE id = 5
  User: tell me about board 12, keep or scrap? -> SQL: SELECT id, detected_stage, total_defects, granular_details FROM inference_logs WHERE id = 12
  User: which stage has the most defects?     -> SQL: SELECT detected_stage, SUM(total_defects) AS total FROM inference_logs GROUP BY detected_stage ORDER BY total DESC
  User: how do I prevent mouse_bite?          -> CHAT: <engineering guidance>
  User: hi                                     -> CHAT: Hello! Ask me about your inspection logs or defect handling.

Rules:
- Output MUST start with "SQL:" or "CHAT:". No markdown, no code fences, no explanation.
- Never write INSERT/UPDATE/DELETE/DROP — only SELECT.

User message: "{question}"
"""


def _extract_action(raw):
    """Return ('SQL'|'CHAT'|None, payload) from a raw model response."""
    text = (raw or "").strip()
    # Strip stray code fences the model may add.
    text = text.replace("```sql", "").replace("```", "").strip()
    upper = text.upper()
    idx_sql = upper.find("SQL:")
    idx_chat = upper.find("CHAT:")
    # Pick whichever prefix appears first.
    candidates = [(i, tag) for i, tag in ((idx_sql, "SQL"), (idx_chat, "CHAT")) if i != -1]
    if candidates:
        start, tag = min(candidates)
        payload = text[start + len(tag) + 1:].strip()
        return tag, payload
    # No explicit prefix but looks like a bare SELECT — treat as SQL.
    if upper.lstrip().startswith("SELECT"):
        return "SQL", text
    return None, text


def ask_database(user_question, engine="Cloud Engine (Gemini)", api_key=""):
    client = None
    if engine == "Cloud Engine (Gemini)":
        if not api_key:
            return "Error: Provide a Gemini API Key in secrets."
        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            return f"Gemini Initialization Error: {e}"

    router_prompt = ROUTER_PROMPT.format(schema=DATABASE_SCHEMA, question=user_question)

    try:
        raw_response = _generate(engine, router_prompt, api_key, client)
        action, payload = _extract_action(raw_response)

        # One corrective retry if the model ignored the protocol.
        if action is None:
            retry_prompt = (
                router_prompt
                + "\n\nYour previous reply did not start with SQL: or CHAT:. "
                "Reply again with EXACTLY one line starting with SQL: or CHAT:."
            )
            raw_response = _generate(engine, retry_prompt, api_key, client)
            action, payload = _extract_action(raw_response)

        # CASE A: Database query
        if action == "SQL":
            db_results = execute_read_query(payload)
            translation_prompt = f"""You are a Senior PCB Manufacturing QA Engineer analyzing factory inspection data.

User question: "{user_question}"
Query results (rows from inference_logs): {db_results}

Note: the 'granular_details' field is a JSON object mapping defect class names to counts
(e.g. {{"mouse_bite": 2, "short": 1}}). Parse it to reason about specific defect types.

{ENGINEERING_CONTEXT}

Answer the user's question directly using ONLY the data above. If they ask whether to keep,
scrap, or rework a board, apply the engineering rules (consider stage AND defect type) and give
a clear recommendation plus prevention/improvement advice. If the data is empty, say no matching
records were found. Do NOT mention "the database", "SQL", or "raw data" — speak naturally."""
            try:
                friendly_answer = _generate(engine, translation_prompt, api_key, client)
            except LLMError:
                friendly_answer = f"Here is what I found: {db_results}"
            return {"sql_query": payload, "raw_results": db_results, "friendly_answer": friendly_answer}

        # CASE B: Direct engineering chat (also covers corrective-retry success)
        clean_msg = payload.strip() if action == "CHAT" else raw_response.strip()
        return {"sql_query": None, "raw_results": None, "friendly_answer": clean_msg}

    except LLMError as e:
        return str(e)