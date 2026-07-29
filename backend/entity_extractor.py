import json

from openai import OpenAI

from backend.core.config import GROQ_API_KEY

client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)


# -----------------------------
# Extract Entities
# -----------------------------
def extract_entities(query: str) -> list[str]:

    prompt = f"""
    Extract only the important entities from the user query.
    Return ONLY valid JSON.
    Guidelines:
    1. Normalize the extracted entities to Title Case (e.g., convert "sarcoplasmic reticulum" to "Sarcoplasmic Reticulum").
    2. Do not split proper nouns (e.g., return "Maillard Reaction" as one entity, not "Maillard" and "Reaction" separately).
    Example:
    {{
        "entities": [
            "FastAPI",
            "Qdrant",
            "Sarcoplasmic Reticulum"
        ]
    }}

Query:
{query}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    return result.get("entities", [])
