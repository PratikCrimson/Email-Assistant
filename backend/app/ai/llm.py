import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-4o-mini"

def call_llm(context: str, question: str) -> str:
    prompt = f"""
You are an AI email assistant.

You MUST answer strictly using only the provided context.
Do NOT use outside knowledge.
Do NOT make assumptions.
If the answer is not explicitly present in the context, say:
"I couldn't find this in your emails."

Rules:
- For time-based queries (latest, recent, newest, last), use the Date field and select the newest matching email.
- If multiple emails match, list them in descending date order.
- Keep responses concise and readable.
- When listing emails, use bullet points with:
  - Subject
  - Sender
  - Date
- Do NOT include tracking links, internal IDs, raw HTML, or long body dumps unless explicitly requested.

Context:
{context}

User question:
{question}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an email assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()