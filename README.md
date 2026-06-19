# Persona-Adaptive Customer Support Agent

## Project Overview

This project is a Persona-Adaptive Customer Support Agent built using Python, Gemini LLM, Retrieval-Augmented Generation, ChromaDB, and Streamlit.

The system accepts a customer support message, detects the customer's communication persona, retrieves relevant information from a local support knowledge base, generates a response in the correct tone, and escalates sensitive or low-confidence cases to a human support representative.

The agent supports three customer personas:

1. Technical Expert
2. Frustrated User
3. Business Executive

## Objective

The objective of this project is to demonstrate a practical LLM-powered support workflow that combines:

* Persona detection
* Retrieval-Augmented Generation
* Adaptive response generation
* Human escalation logic
* Structured handoff summary generation
* Interactive web UI

## Tech Stack

* Python 3.11+
* Google Gemini API
* Gemini Embeddings
* ChromaDB
* LangChain Text Splitters
* Streamlit
* pypdf
* python-dotenv

## Project Structure

```text
persona-support-agent/
│
├── data/
│   ├── account_security.txt
│   ├── api_authentication.md
│   ├── billing_policy.txt
│   ├── dashboard_troubleshooting.md
│   ├── integration_errors.md
│   ├── login_issue_guide.txt
│   ├── password_reset_guide.pdf
│   ├── payment_failure_guide.txt
│   ├── refund_policy.md
│   ├── subscription_cancellation.txt
│   └── uptime_sla_policy.txt
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── classifier.py
│   ├── rag_pipeline.py
│   ├── generator.py
│   └── escalator.py
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Architecture Diagram

```text
User Query
   ↓
Persona Detection
   ↓
Knowledge Base Retrieval
   ↓
Adaptive Response Generation
   ↓
Escalation Check
   ↓
Human Handoff Summary
```

## System Workflow

1. The user enters a customer support query in the Streamlit interface.
2. The query is sent to the persona classifier.
3. The classifier identifies the user as Technical Expert, Frustrated User, or Business Executive.
4. The RAG pipeline retrieves the most relevant knowledge base chunks from ChromaDB.
5. The response generator creates a grounded answer using only retrieved support content.
6. The escalation module checks for low confidence, sensitive topics, or repeated frustration.
7. If escalation is needed, the system generates a structured JSON handoff summary for a human support agent.

## Persona Detection Strategy

The system classifies the user message into one of three personas.

### Technical Expert

Characteristics:

* Uses technical terminology
* Mentions APIs, tokens, logs, databases, endpoints, configurations, or errors
* Wants detailed and structured troubleshooting

Response style:

* Technical
* Detailed
* Root-cause focused
* Step-by-step troubleshooting

### Frustrated User

Characteristics:

* Uses emotional language
* Shows urgency or dissatisfaction
* Says something is not working even after repeated attempts

Response style:

* Empathetic
* Simple
* Reassuring
* Action-oriented

### Business Executive

Characteristics:

* Focuses on business impact
* Asks about timeline, SLA, operations, uptime, or resolution priority
* Prefers concise communication

Response style:

* Short
* Professional
* Impact-focused
* Minimal technical jargon

## RAG Pipeline Design

The Retrieval-Augmented Generation pipeline performs the following steps:

1. Loads support documents from the `data/` directory.
2. Supports `.txt`, `.md`, and `.pdf` files.
3. Extracts text from PDF documents using `pypdf`.
4. Splits documents into chunks using `RecursiveCharacterTextSplitter`.
5. Generates embeddings using Gemini Embeddings.
6. Stores embeddings, text chunks, and metadata in ChromaDB.
7. Retrieves top-k relevant chunks for each user query.
8. Sends retrieved context to the response generator.

## Knowledge Base

The project includes realistic SaaS customer support documents covering:

* API authentication
* Billing policy
* Account security
* Dashboard troubleshooting
* Subscription cancellation
* Payment failures
* Refund policy
* Login issues
* Integration errors
* Uptime and SLA policy
* Password reset guide PDF

## Escalation Logic

The system escalates to a human support agent when:

* No relevant knowledge base content is found
* Retrieval confidence is below the configured threshold
* Billing, refund, legal, account, tax, or security-sensitive topics are detected
* Repeated frustration is detected across conversation history
* The issue cannot be safely resolved using available documents

The escalation threshold and sensitive keywords are configured in `src/config.py`.

## Human Handoff Summary

When escalation occurs, the system generates a structured JSON summary containing:

* Detected persona
* User issue
* Conversation history
* Retrieved documents used
* Actions already attempted
* Escalation reason
* Recommended next steps

Example:

```json
{
  "persona": "Frustrated User",
  "issue": "My billing statement has unexpected duplicate charges. I demand an immediate refund!",
  "conversation_history": [],
  "retrieved_documents_used": [
    "billing_policy.txt",
    "refund_policy.md"
  ],
  "actions_already_attempted": [
    "Persona detected",
    "Knowledge base retrieval performed",
    "Escalation rules evaluated"
  ],
  "escalation_reason": "Sensitive billing, legal, refund, account, or security topic detected.",
  "recommended_next_steps": [
    "Review the customer's issue manually",
    "Check account, billing, security, or technical logs if applicable",
    "Respond with a clear resolution or next update timeline"
  ]
}
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd persona-support-agent
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

For Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory.

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Do not commit `.env` to GitHub.

### 6. Run the Application

```bash
streamlit run app.py
```

The application will open at:

```text
http://localhost:8501
```

## Example Queries

### Technical Expert Query

```text
What are the header parameter requirements for bearer token authentication?
```

Expected behavior:

* Detects Technical Expert persona
* Retrieves API authentication content
* Provides detailed technical response

### Frustrated User Query

```text
I've tried everything and nothing works! My dashboard is still not loading!
```

Expected behavior:

* Detects Frustrated User persona
* Responds with empathy
* Gives simple troubleshooting steps

### Business Executive Query

```text
Our operational uptime is decreasing. What is the business impact and resolution timeline?
```

Expected behavior:

* Detects Business Executive persona
* Gives concise business-focused response
* Mentions impact and resolution guidance

### Technical API Error Query

```text
I am getting 401 unauthorized error while calling your API endpoint.
```

Expected behavior:

* Detects Technical Expert persona
* Retrieves API authentication guide
* Explains possible causes and resolution steps

### Escalation Query

```text
My billing statement has unexpected duplicate charges. I demand an immediate refund!
```

Expected behavior:

* Detects Frustrated User persona
* Detects sensitive billing/refund topic
* Escalates to human support
* Generates handoff JSON summary

## Application Output

The Streamlit UI displays:

* User message
* Detected persona
* Persona confidence
* Persona reasoning
* Retrieved sources
* Generated response
* Escalation status
* Human handoff summary when escalation occurs
* Conversation history

## Known Limitations

* The project uses a local ChromaDB vector database.
* The quality of answers depends on the knowledge base documents.
* The system does not connect to real customer accounts or real billing systems.
* Escalation is simulated through JSON handoff summary.
* Conversation memory is stored only during the active Streamlit session.
* The application requires a valid Gemini API key.

## Future Improvements

* Add persistent conversation storage using SQLite or PostgreSQL.
* Add sentiment analysis for better frustration tracking.
* Add admin dashboard for escalated tickets.
* Add human approval workflow.
* Add LangGraph-based multi-agent workflow.
* Add analytics for persona distribution and escalation frequency.

## Demo Checklist

The demo video should show:

1. Project structure overview
2. Knowledge base documents
3. Vector database retrieval
4. Persona detection examples
5. Responses for all three personas
6. At least five different test queries
7. Escalation scenario
8. Human handoff JSON summary
9. One technical design decision
