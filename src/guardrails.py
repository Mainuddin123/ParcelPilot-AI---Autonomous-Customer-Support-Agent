import re

MAX_QUERY_LENGTH = 2000
MAX_RESPONSE_LENGTH = 12000
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior) instructions",
    r"reveal (your|the) (system|developer) prompt",
    r"show (me )?(your|the) hidden instructions",
    r"bypass (all )?(safety|security) rules",
]


def validate_input(query: str):
    if not isinstance(query, str) or not query.strip():
        return False, "Please enter a non-empty question."
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Please keep your question under {MAX_QUERY_LENGTH} characters."
    normalized = query.lower()
    if any(re.search(pattern, normalized) for pattern in INJECTION_PATTERNS):
        return False, "I can only help with parcel and customer-support requests."
    return True, ""


def validate_output(answer: str):
    if not isinstance(answer, str) or not answer.strip():
        return False, "I could not generate a reliable response. Please try again."
    if len(answer) > MAX_RESPONSE_LENGTH:
        return False, "The response exceeded the allowed length. Please narrow your question."
    sensitive_patterns = [
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"AIza[0-9A-Za-z_\-]{30,}",
        r"(?i)\b(api[_ -]?key|secret[_ -]?key)\s*[:=]\s*\S+",
    ]
    if any(re.search(pattern, answer) for pattern in sensitive_patterns):
        return False, "I cannot provide that response because it failed a security check."
    return True, answer
