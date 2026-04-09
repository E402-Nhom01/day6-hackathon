import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT_TEMPLATE = """
You are a booking assistant.

Use the user context to resolve locations.

USER CONTEXT:
{context}

Return ONLY valid JSON.

Schema:
{{
  "pickup_location": "",
  "dropoff_location": "",
  "vehicle_type": "",
  "time": "",
  "notes": ""
}}

User input:
"{text}"
"""

def extract_booking(text: str, context: dict):
    prompt = PROMPT_TEMPLATE.format(
        text=text,
        context=json.dumps(context, ensure_ascii=False)
    )

    res = requests.post(OLLAMA_URL, json={
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    })

    output = res.json()["response"]

    try:
        return json.loads(output)
    except:
        return {"error": "invalid_json", "raw": output}