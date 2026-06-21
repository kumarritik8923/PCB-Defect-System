import sqlite3
from google import genai 

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
    # --- STEP 1: SIMPLIFIED PROMPT FOR SMALL MODELS ---
    sql_prompt = f"""
    You are an AI Factory Data Analyst for a PCB Defect Detection System.
    Database Schema: {DATABASE_SCHEMA}
    User Input: "{user_question}"
    
    INSTRUCTIONS:
    If the user asks about the factory database, return ONLY a valid SQLite query starting with "SQL:"
    Example: SQL: SELECT COUNT(*) FROM inference_logs
    
    If the user greets you, talks about other topics, or asks out-of-domain questions, politely reply starting with "CHAT:"
    Example: CHAT: I am a PCB Data Analyst. I don't know about Doraemon, but I can check our factory logs!
    """
    
    raw_response = ""
    client = None
    
    if engine == "Cloud Engine (Gemini)":
        if not api_key: return "Error: Provide Gemini API Key in secrets."
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model='gemini-2.5-flash', contents=sql_prompt)
            raw_response = response.text.strip()
        except Exception as e:
            return f"Gemini API Error: {e}"
            
    elif engine == "Local Engine (Gemma)":
        try:
            import requests 
            res = requests.post("http://localhost:11434/api/generate", json={
                "model": "gemma:2b", "prompt": sql_prompt, "stream": False
            })
            raw_response = res.json().get("response", "").strip()
        except Exception as e:
            return "⚠️ **Local Engine Offline:** Ensure Ollama is running (`ollama run gemma:2b`)."

    # --- STEP 2: BULLETPROOF PARSING ---
    # Convert response to uppercase just for checking conditions safely
    upper_resp = raw_response.upper()
    
    # CASE A: Database Query (Checks for 'SQL:' or the word 'SELECT')
    if upper_resp.startswith("SQL:") or "SELECT " in upper_resp:
        # Clean the string so SQLite can read it
        sql_query = raw_response.replace("SQL:", "").replace("sql:", "").strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").replace(";", "")
        
        if len(sql_query) < 10:
             return "Error: Generated an invalid SQL query."
             
        print(f"[AI AGENT] Generated SQL: {sql_query}")
        db_results = execute_read_query(sql_query)
        
        # --- STEP 3: DYNAMIC TRANSLATION ---
        translation_prompt = f"""
        User Question: "{user_question}"
        Raw Database Result: {db_results}
        
        Act as a highly intelligent, conversational AI Data Analyst. 
        Answer the user's question directly and naturally based ONLY on the raw data provided.
        Do NOT mention "the database" or "raw data". Just answer like a human expert.
        """
        
        friendly_answer = ""
        
        if engine == "Cloud Engine (Gemini)":
            try:
                response = client.models.generate_content(model='gemini-2.5-flash', contents=translation_prompt)
                friendly_answer = response.text.strip()
            except Exception as e:
                friendly_answer = f"Raw Data: {db_results}" 
                
        elif engine == "Local Engine (Gemma)":
            try:
                res = requests.post("http://localhost:11434/api/generate", json={
                    "model": "gemma:2b", "prompt": translation_prompt, "stream": False
                })
                friendly_answer = res.json().get("response", "").strip()
            except Exception as e:
                friendly_answer = f"⚠️ Local translation offline. Raw Data: `{db_results}`"

        return {
            "sql_query": sql_query,
            "raw_results": db_results,
            "friendly_answer": friendly_answer
        }

    # CASE B: Dynamic Conversation (If it uses the CHAT: prefix)
    elif upper_resp.startswith("CHAT:"):
        clean_msg = raw_response[5:].strip() # Removes the "CHAT:" prefix
        return {"sql_query": None, "raw_results": None, "friendly_answer": clean_msg}
        
    # CASE C: Forgiving Fallback (If the LLM forgot the prefix entirely)
    else:
        # Instead of an error, we just pass its raw conversational text straight to the user!
        return {"sql_query": None, "raw_results": None, "friendly_answer": raw_response.strip()}
    