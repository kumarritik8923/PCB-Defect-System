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
    # --- STEP 1: Text to SQL ---
    sql_prompt = f"""
    You are a SQLite expert. Given this schema: {DATABASE_SCHEMA}
    Write a valid SQLite query to answer: "{user_question}"
    RULES: Return ONLY the raw SQL query. No markdown. No explanations. Only SELECT.
    """
    
    sql_query = ""
    client = None
    
    if engine == "Cloud Engine (Gemini)":
        if not api_key: return "Error: Provide Gemini API Key."
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model='gemini-2.5-flash', contents=sql_prompt)
            sql_query = response.text.strip().replace("```sql", "").replace("```", "").replace(";", "")
        except Exception as e:
            return f"Gemini API Error: {e}"
            
    elif engine == "Local Engine (Gemma)":
        try:
            import requests 
            res = requests.post("http://localhost:11434/api/generate", json={
                "model": "gemma:2b", "prompt": sql_prompt, "stream": False
            })
            sql_query = res.json().get("response", "").strip().replace("```sql", "").replace("```", "").replace(";", "")
        except Exception as e:
            return f"Local Gemma Error: {e}"

    if not sql_query or len(sql_query) < 10:
         return f"Error: The AI was unable to generate a valid SQL query."

    # --- STEP 2: Execute SQL ---
    print(f"[AI AGENT] Generated SQL: {sql_query}")
    db_results = execute_read_query(sql_query)
    
    # --- STEP 3: Translate Raw Data to English ---
    translation_prompt = f"""
    The user asked: "{user_question}"
    The database returned this raw data: {db_results}
    
    Act as a friendly, professional AI assistant. Answer the user's question smoothly in 1 or 2 sentences based strictly on the raw data. 
    DO NOT mention SQL, queries, or tuples. Just give the final answer.
    """
    
    friendly_answer = ""
    
    if engine == "Cloud Engine (Gemini)":
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=translation_prompt)
            friendly_answer = response.text.strip()
        except Exception as e:
            friendly_answer = f"Raw Data: {db_results}" # Fallback if translation fails
            
    elif engine == "Local Engine (Gemma)":
        try:
            res = requests.post("http://localhost:11434/api/generate", json={
                "model": "gemma:2b", "prompt": translation_prompt, "stream": False
            })
            friendly_answer = res.json().get("response", "").strip()
        except:
            friendly_answer = f"Raw Data: {db_results}"

    return {
        "sql_query": sql_query,
        "raw_results": db_results,
        "friendly_answer": friendly_answer
    }