import os

import streamlit as st

from psych_defgen.pipeline import run_pipeline


st.set_page_config(
    page_title="Psychological Construct Definition Retrieval",
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

with st.expander("Advanced settings"):

    max_results = st.number_input(
        "Maximum PubMed results",
        min_value=1,
        max_value=500,
        value=100,
        step=1,
    )

    top_k = st.number_input(
        "Number of evidence passages",
        min_value=1,
        max_value=50,
        value=10,
        step=1,
    )

    st.divider()

    st.subheader("LLM Configuration")

    llm_provider = st.selectbox(
        "LLM Provider",
        ["ollama", "openrouter", "custom"],
        index=0,
    )

    if llm_provider == "ollama":
        default_model = "qwen2.5:7b"

    elif llm_provider == "openrouter":
        default_model = "openai/gpt-4.1-mini"

    else:
        default_model = ""

    llm_model = st.text_input(
        "LLM Model",
        value=default_model,
        key=f"model_{llm_provider}",
        placeholder="Enter model identifier",
    )


    llm_api_key = None

    if llm_provider == "openrouter":
        llm_api_key = (
            st.text_input(
                "Your OpenRouter API Key",
                type="password",
            )
            or os.getenv("OPENROUTER_API_KEY")
        )

    elif llm_provider == "custom":
        llm_api_key = (
            st.text_input(
                "API Key (if required by the model server)",
                type="password",
            )
            or None
        )

    llm_base_url = (
        st.text_input(
            "LLM API Endpoint",
            placeholder="e.g., http://localhost:1234/v1",
        )
        or None
    )

if st.button("Retrieve definition", type="primary"):

    if not term.strip():
        st.warning("Please enter a psychological construct.")

    else:
        email = os.getenv("NCBI_EMAIL")
        api_key = os.getenv("NCBI_API_KEY")

        if not email:
            st.error(
                "An NCBI email address is required. "
                "Set the NCBI_EMAIL environment variable."
            )
            st.stop()

        try:
            with st.spinner("Searching PubMed and PMC..."):
    
                result = run_pipeline(
                    term=term.strip(),
                    max_results=int(max_results),
                    top_k=int(top_k),
                    email=email,
                    api_key=api_key,
                    llm_provider=llm_provider,
                    llm_model=llm_model,
                    llm_api_key=llm_api_key,
                    llm_base_url=llm_base_url,
                )

        except Exception as error:
            st.error(f"Retrieval failed: {error}")
            st.stop()


        definition_method = result.get("definition_method")
        definition = result.get("definition")
        generated_definition = result.get("generated_definition")
        evidence = result.get("evidence", [])
        llm_usage = result.get("llm_usage")

        # --------------------------------------------------
        # 1. Definition from Literature
        # --------------------------------------------------

        if definition_method == "pattern":

            st.subheader("1. Definition from Literature")

            st.success(definition)

            st.caption(
                "Original definition identified using "
                "pattern-based extraction from scientific literature."
            )

        elif definition_method in ("ollama_selection", "llm_selection"):

            st.subheader("1. Definition from Literature")

            st.write(definition)

            st.caption(
                "Definition selected from retrieved scientific literature using LLM-assisted selection."
            )
            

        else:

            st.subheader("1. Definition from Literature")

            st.info(
                "No explicit definition matching the selection criteria was identified in the retrieved literature."

            )

        # --------------------------------------------------
        # 2. AI-Synthesized Definition
        # --------------------------------------------------

        st.subheader("2. AI-Synthesized Definition")

        if generated_definition:

            st.write(generated_definition)

            st.caption(
                "Definition synthesized from retrieved scientific literature "
                "using a large language model. Requires expert review."
            )

        else:
            st.info("Insufficient evidence to synthesize a definition.")

        if llm_usage:

            st.markdown("**Total LLM Token Usage**")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Input Tokens", llm_usage.get("input_tokens"))

            with col2:
                st.metric("Output Tokens", llm_usage.get("output_tokens"))

            with col3:
                st.metric("Total Tokens", llm_usage.get("total_tokens"))

            st.caption(
                f"Provider: {llm_usage.get('provider', 'Unknown')} | "
                f"Model: {llm_usage.get('model', 'Unknown')}"
            )

            selection_usage = llm_usage.get("selection")
            synthesis_usage = llm_usage.get("synthesis")

            st.markdown("**Token Usage Breakdown**")

            if selection_usage:
                selection_tokens = selection_usage.get("total_tokens")

                st.write(
                    "**Literature Selection:** "
                    + (
                        f"{selection_tokens:,} tokens"
                        if selection_tokens is not None
                        else "N/A"
                    )
                )
            else:
                st.write("**Literature Selection:** No LLM call")

            if synthesis_usage:
                synthesis_tokens = synthesis_usage.get("total_tokens")

                st.write(
                    "**AI Synthesis:** "
                    + (
                        f"{synthesis_tokens:,} tokens"
                        if synthesis_tokens is not None
                        else "N/A"
                    )
                )
            else:
                st.write("**AI Synthesis:** No LLM call")

        # --------------------------------------------------
        # APA Dictionary
        # --------------------------------------------------

        st.header("APA Dictionary")

        apa_entry = result.get("apa_entry") or {}
        apa_status = apa_entry.get("status")
        apa_url = apa_entry.get("url")


        if apa_status == "found":
            st.success(
                "An entry for this term was found in the APA Dictionary of Psychology."
            )

            if apa_url:
                st.link_button(
                    "View APA Dictionary Entry",
                    apa_url,
                )

        elif apa_status == "not_found":
            st.info(
                "No entry for this term was found in the APA Dictionary of Psychology."
            )

        else:
            st.info(
                "The APA Dictionary entry could not be verified automatically."
            )

            if apa_url:
                st.link_button(
                    "View APA Dictionary",
                    apa_url,
                )

        # --------------------------------------------------
        # Retrieved Evidence
        # --------------------------------------------------

        st.header("Retrieved Evidence")

        if not evidence:
            st.info("No relevant evidence was retrieved.")

        for index, item in enumerate(evidence, start=1):
            title = item.get("title") or "Untitled article"

            with st.expander(f"Evidence {index} — Article: {title}"):

                score = item.get("score")

                if score is not None:
                    st.write(
                        f"**Cosine Similarity Score:** "
                        f"{score:.4f}"
                    )

                authors = item.get("authors")

                if authors:
                    st.write(
                        f"**Authors:** {', '.join(authors)}"
                    )

                journal = item.get("journal")
                year = item.get("year")

                if journal:
                    st.write(
                        f"**Journal:** {journal}"
                        + (f" ({year})" if year else "")
                    )

                source = item.get("source")
                if source:
                    st.write(f"**Source:** {source}")

                pmid = item.get("pmid")
                if pmid:
                    st.write(f"**PMID:** {pmid}")

                pmcid = item.get("pmcid")
                if pmcid:
                    st.write(f"**PMCID:** {pmcid}")

                pubmed_url = item.get("pubmed_url")

                if pubmed_url:
                    st.link_button(
                        "View on PubMed",
                        pubmed_url,
                    )

                full_text_url = item.get("url")

                if full_text_url:
                    st.link_button(
                        "View PMC Full Text",
                        full_text_url,
                    )

                st.write("**Evidence:**")

                st.write(
                    item.get("context_text")
                    or item.get("text")
                    or "No evidence text available."
                )

