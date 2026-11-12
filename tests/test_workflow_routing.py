
import pytest

from src.workflow import detect_workflow


@pytest.mark.parametrize("query", [
    "Cancel ORD-1001",
    "Please cancel ORD-1001",
    "Cancel my order ORD-1001",
    "Can I cancel my order?",
    "I want to cancel my shipment",
    "Stop my parcel",
    "Request cancellation for my shipment",
])
def test_cancellation_routing(query):
    assert detect_workflow(query) == "cancellation"


@pytest.mark.parametrize("query", [
    "What is the cancellation policy?",
    "Explain cancellation rules",
    "What are the refund rules?",
])
def test_policy_questions_use_rag(query):
    assert detect_workflow(query) == "general"


@pytest.mark.parametrize("query", [
    "Check order ORD-1001",
    "Track my shipment",
    "Where is my parcel?",
])
def test_order_routing(query):
    assert detect_workflow(query) == "order"


@pytest.mark.parametrize("query", [
    "Request service credit",
    "Am I eligible for compensation?",
])
def test_service_credit_routing(query):
    assert detect_workflow(query) == "service_credit"


@pytest.mark.parametrize("query", [
    "Escalate my ticket",
    "Please escalate this issue",
])
def test_escalation_routing(query):
    assert detect_workflow(query) == "escalation"
