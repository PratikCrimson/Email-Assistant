import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "models/gemini-2.5-flash"

def call_llm(context: str, question: str) -> str:
    prompt = f"""
You are an email assistant.

Answer the user's question strictly using the context below.
If the answer is not present in the context, say:
"I couldn't find this in your emails."

Context:
{context}

User question:
{question}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text.strip()
