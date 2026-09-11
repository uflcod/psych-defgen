from psych_defgen.apa_dictionary import (
    get_apa_dictionary_entry,
)
from psych_defgen.chunk_text import chunk_article
from psych_defgen.extract_definition_candidates import (
    extract_definition_candidates,
)
from psych_defgen.get_pmc_articles import get_pmc_ids
from psych_defgen.models import Article
from psych_defgen.parse_fulltext import (
    get_full_text_from_pmcid,
)
from psych_defgen.pubmed_search import search_pubmed
from psych_defgen.rag_retrieval import (
    retrieve_relevant_texts,
)
from psych_defgen.retrieve_abstracts import (
    fetch_pubmed_abstracts,
)
from psych_defgen.select_definition_sentence import (
    select_best_definition_sentence,
)


def create_pmc_evidence_record(
    text,
    title,
    pmid,
    pmcid,
):
    """
    Create a PMC evidence record.
    """
    return {
        "text": text,
        "title": title,
        "authors": [],
        "journal": None,
        "year": None,
        "pmid": pmid,
        "pmcid": pmcid,
        "source": "PMC full text",
        "pubmed_url": (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            if pmid
            else None
        ),
        "url": (
            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
            if pmcid
            else None
        ),
    }


def create_abstract_evidence_record(record):
    """
    Convert a PubMed abstract record into the
    evidence format used by retrieval.
    """
    return {
        "text": record.get("abstract", ""),
        "title": record.get("title"),
        "authors": record.get("authors", []),
        "journal": record.get("journal"),
        "year": record.get("year"),
        "pmid": record.get("pmid"),
        "pmcid": None,
        "source": record.get(
            "source",
            "PubMed abstract",
        ),
        "pubmed_url": record.get("pubmed_url"),
        "url": None,
    }


def run_pipeline(
    term,
    max_results=100,
    top_k=10,
    email=None,
    api_key=None,
):
    """
    Run the psych-defgen retrieval and
    definition-selection workflow.
    """

    # -------------------------------------------------
    # APA Dictionary
    # -------------------------------------------------

    print(
        f"Creating APA Dictionary reference for: {term}"
    )

    apa_entry = get_apa_dictionary_entry(term)

    # -------------------------------------------------
    # PubMed search
    # -------------------------------------------------

    print(
        f"Searching PubMed for: {term}"
    )

    pmids = search_pubmed(
        term,
        max_results=max_results,
        email=email,
        api_key=api_key,
    )

    print(
        f"PubMed articles found: {len(pmids)}"
    )

    # -------------------------------------------------
    # PMC mapping
    # -------------------------------------------------

    pmid_to_pmcid = get_pmc_ids(
        pmids,
        email=email,
        api_key=api_key,
    )

    print(
        "PMC full-text articles found: "
        f"{len(pmid_to_pmcid)}"
    )

    definition_candidates = []
    full_text_chunks = []

    # -------------------------------------------------
    # PMC full text
    # -------------------------------------------------

    for pmid, pmcid in pmid_to_pmcid.items():

        print(
            f"Using full text: PMID {pmid}, {pmcid}"
        )

        try:
            title, text = get_full_text_from_pmcid(
                pmcid,
                email=email,
                api_key=api_key,
            )

        except Exception as error:
            print(
                "Could not retrieve full text for "
                f"PMID {pmid}, {pmcid}: {error}"
            )
            continue

        if not text:
            continue

        if term.lower() not in text.lower():
            continue

        candidates = extract_definition_candidates(
            text,
            term,
        )

        for candidate in candidates:
            definition_candidates.append(
                create_pmc_evidence_record(
                    text=candidate,
                    title=title,
                    pmid=pmid,
                    pmcid=pmcid,
                )
            )

        article = Article(
            pmid=pmid,
            pmcid=pmcid,
            title=title,
            source="PMC full text",
            text=text,
        )

        chunks = chunk_article(article)

        for chunk in chunks:
            full_text_chunks.append(
                create_pmc_evidence_record(
                    text=chunk.text,
                    title=chunk.title,
                    pmid=chunk.pmid,
                    pmcid=chunk.pmcid,
                )
            )

    # -------------------------------------------------
    # PubMed abstracts
    # -------------------------------------------------

    print(
        "Fetching PubMed abstracts."
    )

    abstract_records = fetch_pubmed_abstracts(
        pmids,
        email=email,
        api_key=api_key,
    )

    abstract_chunks = []
    abstract_definition_candidates = []

    for record in abstract_records:

        abstract_text = record.get(
            "abstract",
            "",
        ).strip()

        if not abstract_text:
            continue

        if term.lower() not in abstract_text.lower():
            continue

        abstract_record = (
            create_abstract_evidence_record(record)
        )

        abstract_chunks.append(
            abstract_record
        )

        candidates = extract_definition_candidates(
            abstract_text,
            term,
        )

        for candidate in candidates:

            candidate_record = (
                create_abstract_evidence_record(
                    record
                )
            )

            candidate_record["text"] = candidate

            abstract_definition_candidates.append(
                candidate_record
            )

    # -------------------------------------------------
    # Combine definition candidates
    # -------------------------------------------------

    all_definition_candidates = (
        definition_candidates
        + abstract_definition_candidates
    )

    # -------------------------------------------------
    # Retrieval pool
    # -------------------------------------------------

    retrieval_items = (
        all_definition_candidates
        + full_text_chunks
        + abstract_chunks
    )

    # -------------------------------------------------
    # Semantic retrieval
    # -------------------------------------------------

    retrieved = []

    if retrieval_items:
        retrieved = retrieve_relevant_texts(
            term,
            retrieval_items,
            top_k=top_k,
        )

    # -------------------------------------------------
    # Explicit definition selection
    # -------------------------------------------------

    candidate_sources = (
        all_definition_candidates
        + retrieved
    )

    best_definition_sentence = (
        select_best_definition_sentence(
            term,
            candidate_sources,
        )
    )

    if best_definition_sentence:
        definition_from_literature = (
            best_definition_sentence.strip()
        )

    else:
        definition_from_literature = (
            "No explicit definition was found "
            "in the retrieved literature."
        )

    # -------------------------------------------------
    # Return results
    # -------------------------------------------------

    return {
        "term": term,
        "apa_entry": apa_entry,
        "definition": definition_from_literature,
        "evidence": retrieved,
        "pmids": pmids,
        "pmid_to_pmcid": pmid_to_pmcid,
    }
