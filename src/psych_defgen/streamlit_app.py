import os

import streamlit as st

from psych_defgen.pipeline import run_pipeline


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

if st.button(
    "Retrieve definition",
    type="primary",
):

    if not term.strip():
        st.warning(
            "Please enter a psychological construct."
        )

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
            with st.spinner(
                "Searching PubMed and PMC..."
            ):
                result = run_pipeline(
                    term=term.strip(),
                    max_results=int(max_results),
                    top_k=int(top_k),
                    email=email,
                    api_key=api_key,
                )

        except Exception as error:
            st.error(
                f"Retrieval failed: {error}"
            )
            st.stop()

        st.header(
            "Definition from Literature"
        )

        st.write(
            result["definition"]
        )

        st.header(
            "APA Dictionary"
        )

        apa_entry = result.get(
            "apa_entry",
            {},
        )

        apa_status = apa_entry.get("status")
        apa_url = apa_entry.get("url")

        if apa_status == "found":
            st.success(
                "An entry for this term was found in "
                "the APA Dictionary of Psychology."
            )

            if apa_url:
                st.link_button(
                    "View APA Dictionary Entry",
                    apa_url,
                )

        elif apa_status == "not_found":
            st.info(
                "No entry for this term was found in "
                "the APA Dictionary of Psychology."
            )

        else:
            st.info(
                "The APA Dictionary entry could not "
                "be verified automatically."
            )

            if apa_url:
                st.link_button(
                    "View APA Dictionary",
                    apa_url,
                )

        st.header(
            "Retrieved Evidence"
        )

        evidence = result.get(
            "evidence",
            [],
        )

        if not evidence:
            st.info(
                "No relevant evidence was retrieved."
            )

        for index, item in enumerate(
            evidence,
            start=1,
        ):
            title = (
                item.get("title")
                or "Untitled article"
            )

            with st.expander(
                f"Evidence {index}: {title}"
            ):
                score = item.get("score")

                if score is not None:
                    st.write(
                        "**Semantic similarity score:** "
                        f"{score:.4f}"
                    )

                source = item.get("source")

                if source:
                    st.write(
                        f"**Source:** {source}"
                    )

                pmid = item.get("pmid")

                if pmid:
                    st.write(
                        f"**PMID:** {pmid}"
                    )

                pmcid = item.get("pmcid")

                if pmcid:
                    st.write(
                        f"**PMCID:** {pmcid}"
                    )

                pubmed_url = item.get(
                    "pubmed_url"
                )

                if pubmed_url:
                    st.link_button(
                        "View on PubMed",
                        pubmed_url,
                    )

                full_text_url = item.get(
                    "url"
                )

                if full_text_url:
                    st.link_button(
                        "View PMC Full Text",
                        full_text_url,
                    )

                st.write(
                    "**Evidence:**"
                )

                st.write(
                    item.get(
                        "text",
                        "",
                    )
                )

        st.caption(
            "Semantic similarity scores represent cosine "
            "similarity to the construct-focused definitional "
            "query and should not be interpreted as the "
            "probability that a passage is a definition."
        )

        st.subheader(
            "Curation Status"
        )

        st.write(
            "Needs expert review."
        )
