from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GENERATION_MODEL
from src.escalator import should_escalate, generate_handoff_summary


def _get_persona_instruction(persona: str) -> str:
    """
    Returns response style instructions based on detected persona.
    """

    if persona == "Technical Expert":
        return """
You are a Senior Technical Support Engineer.
Respond with:
- Root cause analysis
- Technical explanation
- Step-by-step troubleshooting
- API/configuration details when available
- Clear technical structure
"""

    if persona == "Business Executive":
        return """
You are a Client Relations Director.
Respond with:
- Short professional answer
- Business impact
- Resolution timeline guidance if available
- Minimal technical jargon
- Clear next action
"""

    return """
You are an empathetic Customer Support Specialist.
Respond with:
- Warm validation of the user's problem
- Simple language
- Reassuring tone
- Clear action-oriented steps
- Avoid heavy technical jargon
"""


def _fallback_response(user_query: str, persona: str, retrieved_chunks: list) -> str:
    """
    Source-grounded fallback response if Gemini generation fails.
    This prevents Streamlit from crashing and still gives a useful answer.
    """

    sources = list({chunk.get("source", "Unknown") for chunk in retrieved_chunks})
    top_sources = ", ".join(sources) if sources else "No source found"

    context_preview = "\n".join(
        chunk.get("text", "")[:600] for chunk in retrieved_chunks[:2]
    )

    if persona == "Technical Expert":
        return (
            "Based on the retrieved knowledge base content, this issue can be handled as a technical support case.\n\n"
            "Likely areas to verify:\n"
            "1. Check whether the required configuration or authentication details are correctly provided.\n"
            "2. Validate the request format, token, endpoint, permissions, or integration setup based on the retrieved guide.\n"
            "3. Retry the request after correcting the configuration.\n"
            "4. If the issue continues after these checks, escalate it for deeper log-level investigation.\n\n"
            f"Retrieved sources used: {top_sources}\n\n"
            f"Relevant retrieved context:\n{context_preview}"
        )

    if persona == "Business Executive":
        return (
            "Based on the retrieved knowledge base content, this issue should be handled with priority based on business impact.\n\n"
            "Summary:\n"
            "1. The issue may affect operational continuity or customer productivity.\n"
            "2. The recommended action is to follow the documented troubleshooting or support process first.\n"
            "3. If the issue impacts multiple users, production access, billing, or SLA commitments, it should be escalated to human support.\n"
            "4. The next update should include impact, current status, workaround, and expected resolution direction.\n\n"
            f"Retrieved sources used: {top_sources}\n\n"
            f"Relevant retrieved context:\n{context_preview}"
        )

    return (
        "I understand how inconvenient this issue is. Based on the retrieved support documents, please try the following steps:\n\n"
        "1. Refresh the page and try again.\n"
        "2. Log out and log in again.\n"
        "3. Clear browser cache and cookies.\n"
        "4. Try opening the application in incognito or private mode.\n"
        "5. Disable browser extensions temporarily.\n"
        "6. Try another browser or network.\n"
        "7. If the issue still continues, human support should review it further.\n\n"
        f"Retrieved sources used: {top_sources}\n\n"
        f"Relevant retrieved context:\n{context_preview}"
    )

def generate_adaptive_response(
    user_query: str,
    persona: str,
    retrieved_chunks: list,
    conversation_history: list = None
) -> dict:
    """
    Generates persona-adaptive response using retrieved knowledge base content.
    Also checks whether escalation is required.
    """

    if conversation_history is None:
        conversation_history = []

    escalate, escalation_reason = should_escalate(
        user_message=user_query,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history
    )

    if escalate:
        handoff_summary = generate_handoff_summary(
            user_message=user_query,
            persona=persona,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history,
            escalation_reason=escalation_reason
        )

        return {
            "escalated": True,
            "response": (
                "I understand this needs careful attention. "
                "I’m escalating this conversation to a human support specialist "
                "so they can review the issue safely and provide the right next step."
            ),
            "handoff_summary": handoff_summary,
            "escalation_reason": escalation_reason
        }

    context_text = "\n\n".join([
        f"Source: {chunk['source']} | Score: {chunk['score']:.2f}\n{chunk['text']}"
        for chunk in retrieved_chunks
    ])

    persona_instruction = _get_persona_instruction(persona)

    system_prompt = f"""
{persona_instruction}

Critical rules:
- Use only the retrieved knowledge base context.
- Do not hallucinate or invent facts.
- If the answer is not present in the context, say that the issue needs human review.
- Keep the response aligned with the detected persona.

Retrieved knowledge base context:
{context_text}
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2
            )
        )

        final_response = response.text

    except Exception:
        final_response = _fallback_response(
            user_query=user_query,
            persona=persona,
            retrieved_chunks=retrieved_chunks
        )

    return {
        "escalated": False,
        "response": final_response,
        "handoff_summary": None,
        "escalation_reason": None
    }