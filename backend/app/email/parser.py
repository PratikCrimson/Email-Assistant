import base64
from token import MINEQUAL

def _get_header(headers,name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return None

def extract_email_feilds(message):
    payload = message.get("payload", {})
    headers = payload.get("headers",[])

    subject = _get_header(headers,"Subject")
    sender = _get_header(headers,"From")
    date = _get_header(headers,"Date")

    body =""

    def _extract_parts(parts):
        nonlocal body
        for part in parts:
            mime_type = part.get("mimeType")
            data = part.get("body", {}).get("data")

            if data and mime_type =="text/plain":
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                body += decoded
            elif "parts" in part:
                _extract_parts(part["parts"])
    if "parts" in payload:
        _extract_parts(payload["parts"])
    else:
        data = payload.get("body", {}).get("data")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
              
    return {
        "subject": subject,
        "sender": sender,
        "date" : date,
        "body" : body,
    }


