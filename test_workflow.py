
from src.workflow import detect_workflow

test_cases = [
    ("What is the escalation SLA?", "general"),
    ("Explain escalation policy", "general"),
    ("What is the escalation process?", "general"),
    ("Escalate ticket TKT-1001", "escalation"),
    ("I want to escalate my issue", "escalation"),
    ("Check ticket status", "ticket"),
    ("What is the cancellation policy?", "general"),
    ("Can I cancel ORD-1001?", "cancellation"),
    ("Am I eligible for service credit?", "service_credit"),
    ("What is the status of my order?", "order"),
]

passed = 0

for query, expected in test_cases:
    actual = detect_workflow(query)

    if actual == expected:
        print(f"PASS: {query}")
        passed += 1
    else:
        print(f"FAIL: {query}")
        print(f"Expected: {expected}, Got: {actual}")

print(f"\nResults: {passed}/{len(test_cases)} passed")
