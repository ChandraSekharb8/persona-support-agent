import streamlit as st

from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response


st.set_page_config(
    page_title="Persona-Adaptive Customer Support Agent",
    page_icon="🤖",
    layout="wide"
)
st.markdown("""
<style>
.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #1f2937;
    margin-bottom: 5px;
}
.subtitle {
    font-size: 17px;
    color: #4b5563;
    margin-bottom: 25px;
}
.info-card {
    background-color: #f8fafc;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    margin-bottom: 15px;
}
.success-card {
    background-color: #ecfdf5;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #10b981;
}
.warning-card {
    background-color: #fff7ed;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #f97316;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_rag_pipeline():
    rag = LocalRAGPipeline()
    rag.build_vector_database(force_rebuild=False)
    return rag


def show_retrieved_sources(retrieved_chunks):
    if not retrieved_chunks:
        st.warning("No retrieved sources found.")
        return

    for index, chunk in enumerate(retrieved_chunks, start=1):
        with st.expander(
            f"Source {index}: {chunk['source']} | Confidence Score: {chunk['score']:.2f}"
        ):
            st.write(chunk["text"])


def main():
    st.markdown(
        "<div class='main-title'>🤖 Persona-Adaptive Customer Support Agent</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>AI-powered support assistant using Persona Detection, RAG, Adaptive Response Generation, and Human Escalation.</div>",
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.header("Project Controls")

        if st.button("Rebuild Knowledge Base Index"):
            with st.spinner("Rebuilding ChromaDB vector index..."):
                rag = LocalRAGPipeline()
                count = rag.build_vector_database(force_rebuild=True)
                st.cache_resource.clear()
                st.success(f"Knowledge base rebuilt successfully. Total chunks: {count}")

        st.markdown("---")
        st.subheader("Supported Personas")
        st.write("1. Technical Expert")
        st.write("2. Frustrated User")
        st.write("3. Business Executive")

        st.markdown("---")
        st.subheader("System Workflow")
        st.write("User Query → Persona Detection → RAG Retrieval → Adaptive Response → Escalation Check")
    try:
        rag = load_rag_pipeline()
    except Exception as error:
        st.error(f"Failed to load RAG pipeline: {error}")
        st.stop()

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    st.subheader("Customer Message")

    example_query = st.selectbox(
        "Try an example query or type your own below:",
        [
            "",
            "What are the header parameter requirements for bearer token authentication?",
            "I've tried everything and nothing works! My dashboard is still not loading!",
            "Our operational uptime is decreasing. What is the business impact and resolution timeline?",
            "My billing statement has unexpected duplicate charges. I demand an immediate refund!",
            "I am getting 401 unauthorized error while calling your API endpoint."
        ]
    )

    user_query = st.text_area(
        "Enter customer message:",
        value=example_query,
        height=120
    )

    if st.button("Generate Support Response"):
        if not user_query.strip():
            st.warning("Please enter a customer message.")
            return

        with st.spinner("Detecting persona, retrieving knowledge base, and generating response..."):
            persona_result = classify_customer_persona(user_query)
            persona = persona_result.get("persona", "Frustrated User")

            retrieved_chunks = rag.retrieve_context(user_query)

            result = generate_adaptive_response(
                user_query=user_query,
                persona=persona,
                retrieved_chunks=retrieved_chunks,
                conversation_history=st.session_state.conversation_history
            )

            st.session_state.conversation_history.append({
                "user": user_query,
                "persona": persona,
                "response": result["response"],
                "escalated": result["escalated"]
            })

            st.session_state.last_result = {
                "user_query": user_query,
                "persona_result": persona_result,
                "retrieved_chunks": retrieved_chunks,
                "result": result
            }

    if st.session_state.last_result:
        data = st.session_state.last_result

        st.markdown("---")
        st.subheader("Application Output")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Detected Persona", data["persona_result"].get("persona", "Unknown"))

        with col2:
            st.metric(
                "Persona Confidence",
                f"{data['persona_result'].get('confidence', 0):.2f}"
            )

        with col3:
            escalation_status = "Escalated" if data["result"]["escalated"] else "Not Escalated"
            st.metric("Escalation Status", escalation_status)

        st.markdown("### User Message")
        st.write(data["user_query"])

        st.markdown("### Persona Detection Reasoning")
        st.info(data["persona_result"].get("reasoning", "No reasoning available."))

        st.markdown("### Retrieved Sources")
        show_retrieved_sources(data["retrieved_chunks"])

        st.markdown("### Generated Response")
        st.success(data["result"]["response"])

        if data["result"]["escalated"]:
            st.markdown("### Escalation Reason")
            st.warning(data["result"]["escalation_reason"])

            st.markdown("### Human Handoff Summary JSON")
            st.code(data["result"]["handoff_summary"], language="json")

    st.markdown("---")

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    with st.expander("📜 View Conversation History", expanded=False):
        if st.session_state.conversation_history:
            for index, item in enumerate(st.session_state.conversation_history, start=1):
                st.markdown(f"### Conversation {index}")
                st.write(f"**User:** {item['user']}")
                st.write(f"**Persona:** {item['persona']}")
                st.write(f"**Escalated:** {item['escalated']}")
                st.write(f"**Response:** {item['response']}")
                st.markdown("---")
        else:
            st.info("No conversation history yet.")
if __name__ == "__main__":
    main()