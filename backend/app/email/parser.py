import base64
import html as html_lib
import re


def _decode_part_data(data: str) -> str:
    if not data:
        return ""
    padding = "=" * (-len(data) % 4)
    try:
        raw_bytes = base64.urlsafe_b64decode((data + padding).encode("utf-8"))
    except Exception:
        raw_bytes = base64.urlsafe_b64decode(data)
    return raw_bytes.decode("utf-8", errors="ignore")


def _strip_html_tags(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(r"(?i)</div\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _looks_like_html(value: str) -> bool:
    return bool(value and re.search(r"<[a-z][\s\S]*>", value, flags=re.IGNORECASE))


def _get_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return None


def extract_email_feilds(message):
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    subject = _get_header(headers, "Subject")
    sender = _get_header(headers, "From")
    date = _get_header(headers, "Date")

    plain_chunks: list[str] = []
    html_chunks: list[str] = []

    def _extract_parts(parts):
        for part in parts:
            mime_type = (part.get("mimeType") or "").lower()
            data = part.get("body", {}).get("data")
            nested_parts = part.get("parts") or []

            if nested_parts:
                _extract_parts(nested_parts)

            if not data:
                continue

            decoded = _decode_part_data(data)
            if not decoded:
                continue

            if mime_type.startswith("text/plain"):
                plain_chunks.append(decoded)
            elif mime_type.startswith("text/html"):
                html_chunks.append(decoded)

    if payload.get("parts"):
        _extract_parts(payload["parts"])
    else:
        mime_type = (payload.get("mimeType") or "").lower()
        data = payload.get("body", {}).get("data")
        decoded = _decode_part_data(data) if data else ""
        if decoded:
            if mime_type.startswith("text/html"):
                html_chunks.append(decoded)
            else:
                plain_chunks.append(decoded)

    plain_body = "\n".join(chunk for chunk in plain_chunks if chunk).strip()
    html_body = "\n".join(chunk for chunk in html_chunks if chunk).strip()

    # Some messages contain HTML markup in text/plain bodies.
    if plain_body and not html_body and _looks_like_html(plain_body):
        html_body = plain_body
        plain_body = _strip_html_tags(plain_body)

    if not plain_body and html_body:
        plain_body = _strip_html_tags(html_body)

    return {
        "subject": subject,
        "sender": sender,
        "date": date,
        "body": plain_body,
        "html_body": html_body or None,
    }

