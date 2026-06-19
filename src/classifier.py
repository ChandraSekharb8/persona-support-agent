import json
import re
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GENERATION_MODEL


def _fallback_persona_detection(user_message: str) -> dict:
    """
    Simple rule-based fallback if Gemini API fails.
    """
    text = user_message.lower()

    technical_keywords = [
        "api", "token", "logs", "configuration", "endpoint",
        "database", "webhook", "401", "403", "429", "json",
        "server", "integration", "headers", "callback"
    ]

    frustrated_keywords = [
        "not working", "nothing works", "angry", "frustrated",
        "immediately", "urgent", "terrible", "bad", "stuck",
        "i tried everything", "refund", "demand"
    ]

    executive_keywords = [
        "business impact", "operations", "timeline", "sla",
        "uptime", "resolution time", "impact", "revenue",
        "executive", "priority"
    ]

    if any(word in text for word in technical_keywords):
        return {
            "persona": "Technical Expert",
            "confidence": 0.75,
            "reasoning": "Detected technical terms such as API, logs, endpoint, configuration, or error codes."
        }

    if any(word in text for word in executive_keywords):
        return {
            "persona": "Business Executive",
            "confidence": 0.75,
            "reasoning": "Detected business-focused language related to impact, timeline, SLA, or operations."
        }

    if any(word in text for word in frustrated_keywords) or "!" in user_message:
        return {
            "persona": "Frustrated User",
            "confidence": 0.75,
            "reasoning": "Detected emotional or urgent language."
        }

    return {
        "persona": "Frustrated User",
        "confidence": 0.55,
        "reasoning": "Defaulted to user-friendly support style because no strong technical or executive signal was found."
    }


def classify_customer_persona(user_message: str) -> dict:
    """
    Classifies customer message into:
    Technical Expert, Frustrated User, or Business Executive.
    """

    if not GEMINI_API_KEY:
        return _fallback_persona_detection(user_message)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        system_instruction = """
You are a customer support persona classification engine.

Classify the user message into exactly one persona:

1. Technical Expert
- Uses technical terminology
- Talks about APIs, logs, configuration, database, tokens, endpoints
- Wants detailed/root-cause explanation

2. Frustrated User
- Uses emotional language
- Complains that something is not working
- Shows urgency, anger, confusion, or repeated attempts

3. Business Executive
- Focuses on business impact
- Wants concise answer
- Asks about timeline, SLA, uptime, operations, revenue, or priority

Return only valid JSON with:
persona, confidence, reasoning
"""

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "persona": {
                    "type": "STRING",
                    "enum": [
                        "Technical Expert",
                        "Frustrated User",
                        "Business Executive"
                    ]
                },
                "confidence": {"type": "NUMBER"},
                "reasoning": {"type": "STRING"}
            },
            "required": ["persona", "confidence", "reasoning"]
        }

        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )

        return json.loads(response.text)

    except Exception:
        return _fallback_persona_detection(user_message)


if __name__ == "__main__":
    test_message = "Our API token is returning 401 unauthorized. Can you check the header configuration?"
    result = classify_customer_persona(test_message)
    print(json.dumps(result, indent=2))