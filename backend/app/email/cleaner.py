import re
from html import unescape
from bs4 import BeautifulSoup

REPLY_SEPARATORS = [
    r"\nOn .* wrote:",
    r"\nFrom: .*",
    r"\nSent: .*",
    r"\nTo: .*",
    r"\nSubject: .*",
    r"-----Original Message-----",
]

SIGNATURE_PATTERNS = [
    r"\nThanks[,!\n].*",
    r"\nBest regards[,!\n].*",
    r"\nRegards[,!\n].*",
    r"\nSent from my .*",
]

def strip_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return unescape(soup.get_text(" "))


def remove_quoted_replies(text: str) -> str:
    for pattern in REPLY_SEPARATORS:
        text = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)[0]
    return text


def remove_signature(text: str) -> str:
    for pattern in SIGNATURE_PATTERNS:
        text = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)[0]
    return text

def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def clean_email_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    text = strip_html(raw_text)
    text = remove_quoted_replies(text)
    text = remove_signature(text)
    text = normalize_whitespace(text)

    return text

