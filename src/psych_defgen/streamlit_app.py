import streamlit as st

st.set_page_config(
    page_title="Psychological Construct Definition Retrieval",
    page_icon="📚",
    layout="wide",
)

st.title("Psychological Construct Definition Retrieval")

st.write(
    "Retrieve evidence-based definitions of psychological "
    "constructs from PubMed and PubMed Central literature."
)

term = st.text_input(
    "Psychological construct",
    placeholder="e.g., social isolation",
)

if st.button("Retrieve definition", type="primary"):
    if not term.strip():
        st.warning("Please enter a psychological construct.")
    else:
        st.success(f"Ready to retrieve: {term.strip()}")
