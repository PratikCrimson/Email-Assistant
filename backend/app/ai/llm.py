import os

from openai import OpenAI

from app.core.logging import trace_event

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")


def _chat(messages: list[dict], *, temperature: float = 0, max_tokens: int | None = None) -> str:
    trace_event(
        "llm.request",
        provider="openai",
        model=MODEL_NAME,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )

    kwargs = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)
    content = (response.choices[0].message.content or "").strip()
    trace_event("llm.response", provider="openai", model=MODEL_NAME, content=content)
    return content


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
- If context includes "Focused email for referential follow-up", treat it as the primary target for phrases like "that mail/message".
- If user asks for full/entire/complete body and focused email body is present, return that body text from context.
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

    return _chat(
        [
            {"role": "system", "content": "You are an email assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )


def rewrite_query_with_context(
    *,
    question: str,
    conversation_summary: str = "",
    recent_messages_text: str = "",
) -> str:
    question = (question or "").strip()
    if not question:
        return ""

    prompt = f"""
You rewrite user questions into a standalone query for email retrieval.
Rules:
- Keep the original intent.
- Resolve pronouns like "that", "those", "latest one" using the provided history.
- Correct obvious spelling/typing mistakes while preserving meaning.
- Keep it concise and specific.
- Output only the rewritten query text (no explanation).
- If the question is already standalone, return it unchanged.

Conversation summary:
{conversation_summary or "(none)"}

Recent messages:
{recent_messages_text or "(none)"}

User question:
{question}
"""
    try:
        rewritten = _chat(
            [
                {
                    "role": "system",
                    "content": "You are a query rewriting assistant for retrieval pipelines.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=180,
        )
        rewritten = (rewritten or "").strip()
        return rewritten or question
    except Exception as e:
        print(f"WARN query rewrite failed, using original question: {e}")
        return question


def summarize_conversation(*, existing_summary: str, transcript: str) -> str:
    if not transcript.strip():
        return existing_summary or ""

    prompt = f"""
Create a compact running summary of this email-assistant conversation.
Focus only on:
- user goals/preferences
- important constraints (dates, senders, categories)
- unresolved questions
- concrete facts already established from emails

Do not invent facts. Keep under 220 words.
Return plain text only.

Existing summary:
{existing_summary or "(none)"}

New transcript segment:
{transcript}
"""
    try:
        return _chat(
            [
                {"role": "system", "content": "You summarize chat context for retrieval systems."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=320,
        )
    except Exception as e:
        print(f"WARN conversation summarization failed: {e}")
        return existing_summary or ""
