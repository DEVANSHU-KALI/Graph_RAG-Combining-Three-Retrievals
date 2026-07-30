This file explains: `entity_extractor.py` and `graph_builder.py` scripts.

## entity_extractor.py
This script uses `llama` from `groq` llm provider to extract entities from the query, which is then used to search the graph database for relevant information.
We wrap the model with openai wrapper and use that, and let the llm respond in json format for better extraction.

### code breakdown
```python
import json
from openai import OpenAI
from backend.core.config import GROQ_API_KEY
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
```
- to get response in json format, we import json.
- we take the groq api key from the config file and initialize the client.

```python
def extract_entities(query: str) -> list[str]:
    prompt = f"""
    Extract only the important entities from the user query.
    Return ONLY valid JSON.
    ...
    {{
        "entities": [
            "FastAPI",
            "Qdrant",
            "Sarcoplasmic Reticulum"
        ]
    }}
    Query:{query}
    """
```
- the function takes query and returns list of strings as mentioned.
- the prompt is given in such way that, it make the llm to response in that specific format mentioned.
```python
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    return result.get("entities", [])
```
- Here one thing to notice is `client.chat.completions.create`, this is the **chat endpoint** of **openai wrapper**, so we pass our information to that llm in this way.
- We also mentioned to generate response as json object.
- Another thing to notice here is the thing which `result` variable holding,
that is how we are going to extract the response from that llm.
- finally we return the entities if they are available.

---

## graph_builder.py
