import json
from src.config import CONFIDENCE_THRESHOLD, SENSITIVE_KEYWORDS


def contains_sensitive_topic(user_message: str) -> bool:
    """
    Checks whether the user message contains billing/legal/security-sensitive topics.
    """
    text = user_message.lower()
    return any(keyword.lower() in text for keyword in SENSITIVE_KEYWORDS)


def should_escalate(user_message: str, retrieved_chunks: list, conversation_history: list = None) -> tuple:
    """
    Decides whether the conversation should be escalated to a human agent.
    Returns: (True/False, reason)
    """

    if conversation_history is None:
        conversation_history = []

    if not retrieved_chunks:
        return True, "No relevant knowledge base information was found."

    best_score = max(chunk.get("score", 0.0) for chunk in retrieved_chunks)

    if best_score < CONFIDENCE_THRESHOLD:
        return True, f"Retrieval confidence is low. Best score: {best_score:.2f}"

    if contains_sensitive_topic(user_message):
        return True, "Sensitive billing, legal, refund, account, or security topic detected."

    frustration_count = 0
    frustration_words = ["not working", "angry", "frustrated", "again", "still", "nothing works", "urgent"]

    for item in conversation_history:
        message = item.get("user", "").lower()
        if any(word in message for word in frustration_words):
            frustration_count += 1

    if frustration_count >= 2:
        return True, "Repeated user frustration detected across multiple interactions."

    return False, "No escalation required."


def generate_handoff_summary(
    user_message: str,
    persona: str,
    retrieved_chunks: list,
    conversation_history: list,
    escalation_reason: str
) -> str:
    """
    Generates structured JSON handoff summary for a human support agent.
    """

    documents_used = list({
        chunk.get("source", "Unknown source")
        for chunk in retrieved_chunks
    })

    handoff_data = {
        "persona": persona,
        "issue": user_message,
        "conversation_history": conversation_history,
        "retrieved_documents_used": documents_used,
        "actions_already_attempted": [
            "Persona detected",
            "Knowledge base retrieval performed",
            "Escalation rules evaluated"
        ],
        "escalation_reason": escalation_reason,
        "recommended_next_steps": [
            "Review the customer's issue manually",
            "Check account, billing, security, or technical logs if applicable",
            "Respond with a clear resolution or next update timeline"
        ]
    }

    return json.dumps(handoff_data, indent=2)