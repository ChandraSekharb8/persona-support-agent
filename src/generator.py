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

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=user_query,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2
        )
    )

    return {
        "escalated": False,
        "response": response.text,
        "handoff_summary": None,
        "escalation_reason": None
    }