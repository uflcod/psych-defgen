import json
import re
from pathlib import Path
from psych_defgen.apa_dictionary import get_apa_dictionary_entry
from psych_defgen.chunk_text import chunk_article
from psych_defgen.extract_definition_candidates import extract_definition_candidates
from psych_defgen.get_pmc_articles import get_pmc_ids
from psych_defgen.models import Article
from psych_defgen.parse_fulltext import get_full_text_from_pmcid
from psych_defgen.pubmed_search import search_pubmed, fetch_pubmed_authors
from psych_defgen.rag_retrieval import retrieve_relevant_texts
from psych_defgen.retrieve_abstracts import fetch_pubmed_abstracts
from psych_defgen.select_definition_sentence import select_best_definition_sentence
from psych_defgen.llm_definition_generator import generate_definition_with_llm


def create_pmc_evidence_record(text, title, pmid, pmcid):
    """
    Create a PMC full-text evidence record with article metadata and source URLs.
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
            if pmid else None
        ),
        "url": (
            f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
            if pmcid else None
        ),
    }


def create_abstract_evidence_record(record):
    """
    Convert a PubMed abstract record into the standard evidence format used for retrieval.
    """
    return {
        "text": record.get("abstract", ""),
        "title": record.get("title"),
        "authors": record.get("authors", []),
        "journal": record.get("journal"),
        "year": record.get("year"),
        "pmid": record.get("pmid"),
        "pmcid": None,
        "source": record.get("source", "PubMed abstract"),
        "pubmed_url": record.get("pubmed_url"),
        "url": None,
    }

def save_pipeline_result(result):
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    term = result["term"]
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "_", term.strip().lower())
    filepath = output_dir / f"{filename}.json"

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    print(f"Results saved to: {filepath.resolve()}")

def run_pipeline(
    term,
    max_results=100,
    top_k=10,
    email=None,
    api_key=None,
    llm_provider="ollama",
    llm_model="qwen2.5:7b",
    llm_api_key=None,
    llm_base_url=None,
):
    """
    Retrieve evidence-based definitions of psychological
    constructs from PubMed and PMC literature.

    Search PubMed, retrieve available PMC full text,
    use PubMed abstracts as fallback, extract definition
    candidates, rank evidence using semantic similarity,
    and select the best available definition sentence.

    Return the definition, retrieved evidence, APA
    Dictionary reference, and article identifiers.
    """

    print(f"Creating APA Dictionary reference for: {term}")
    apa_entry = get_apa_dictionary_entry(term)

    print(f"Searching PubMed for: {term}")
    pmids = search_pubmed(
        term,
        max_results=max_results,
        email=email,
        api_key=api_key,
    )

    print(f"PubMed articles found: {len(pmids)}")

    pmid_to_pmcid = get_pmc_ids(
        pmids,
        email=email,
        api_key=api_key,
    )

    print(f"PMC full-text articles found: {len(pmid_to_pmcid)}")

    definition_candidates = []
    full_text_chunks = []
    processed_pmc_pmids = set()

    for pmid, pmcid in pmid_to_pmcid.items():
        print(f"Using full text: PMID {pmid}, {pmcid}")

        try:
            title, text = get_full_text_from_pmcid(
                pmcid,
                email=email,
                api_key=api_key,
            )
        except Exception as error:
            print(
                f"Could not retrieve full text for "
                f"PMID {pmid}, {pmcid}: {error}"
            )
            continue

        if not text or term.lower() not in text.lower():
            continue

        processed_pmc_pmids.add(str(pmid))

        for candidate in extract_definition_candidates(text, term):
            definition_candidates.append(
                create_pmc_evidence_record(
                    candidate, title, pmid, pmcid
                )
            )

        article = Article(
            pmid=pmid,
            pmcid=pmcid,
            title=title,
            source="PMC full text",
            text=text,
        )

        for chunk in chunk_article(article):
            full_text_chunks.append(
                create_pmc_evidence_record(
                    chunk.text,
                    chunk.title,
                    chunk.pmid,
                    chunk.pmcid,
                )
            )

    fallback_pmids = [
        pmid for pmid in pmids
        if str(pmid) not in processed_pmc_pmids
    ]

    print(
        "PMC articles successfully processed: "
        f"{len(processed_pmc_pmids)}"
    )
    print(
        "PubMed abstracts required as fallback: "
        f"{len(fallback_pmids)}"
    )

    abstract_passages = []
    abstract_definition_candidates = []

    if fallback_pmids:
        abstract_records = fetch_pubmed_abstracts(
            fallback_pmids,
            email=email,
            api_key=api_key,
        )

        for record in abstract_records:
            abstract_text = record.get("abstract", "").strip()

            if not abstract_text or term.lower() not in abstract_text.lower():
                continue

            abstract_passages.append(
                create_abstract_evidence_record(record)
            )

            for candidate in extract_definition_candidates(
                abstract_text, term
            ):
                candidate_record = create_abstract_evidence_record(record)
                candidate_record["text"] = candidate
                abstract_definition_candidates.append(candidate_record)

    all_definition_candidates = (
        definition_candidates + abstract_definition_candidates
    )

    retrieval_items = (
        all_definition_candidates
        + full_text_chunks
        + abstract_passages
    )

    print(f"Definition candidates: {len(all_definition_candidates)}")
    print(f"PMC full-text chunks: {len(full_text_chunks)}")
    print(f"PubMed abstract passages: {len(abstract_passages)}")
    print(f"Total retrieval items: {len(retrieval_items)}")

    retrieved = (
        retrieve_relevant_texts(term, retrieval_items, top_k=top_k)
        if retrieval_items else []
    )

    print(f"Evidence passages retrieved: {len(retrieved)}")

    # Retrieve authors only for the final selected evidence.
    selected_pmids = list({
        str(item["pmid"])
        for item in retrieved
        if item.get("pmid")
    })

    authors_by_pmid = {}

    if selected_pmids:
        try:
            authors_by_pmid = fetch_pubmed_authors(
                selected_pmids,
                email=email,
                api_key=api_key,
            )
        except Exception as error:
            print(f"Could not retrieve article authors: {error}")

    for item in retrieved:
        pmid = str(item.get("pmid") or "")
        item["authors"] = (
            authors_by_pmid.get(pmid)
            or item.get("authors")
            or []
        )


    best_definition_sentence, definition_method, selection_usage = select_best_definition_sentence(
        term,
        all_definition_candidates + retrieved,
        provider=llm_provider,
        model=llm_model,
        api_key=llm_api_key,
        base_url=llm_base_url,
    )

    generated_definition = None
    synthesis_usage = None

    if retrieved:
        generation_result = generate_definition_with_llm(
            term=term,
            evidence=retrieved,
            top_k=top_k,
            provider=llm_provider,
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
        )

        generated_definition = generation_result["text"]
        synthesis_usage = generation_result["usage"]

        if generated_definition == "Insufficient evidence to generate a definition.":
            generated_definition = None

    def sum_tokens(field):
        values = [
            usage.get(field)
            for usage in (selection_usage, synthesis_usage)
            if usage is not None
        ]

        if not values:
            return 0

        if any(value is None for value in values):
            return None

        return sum(values)


    llm_usage = {
        "provider": llm_provider,
        "model": llm_model,
        "input_tokens": sum_tokens("input_tokens"),
        "output_tokens": sum_tokens("output_tokens"),
        "total_tokens": sum_tokens("total_tokens"),
        "selection": selection_usage,
        "synthesis": synthesis_usage,
    }

    definition_from_literature = (
        best_definition_sentence.strip()
        if best_definition_sentence
        else "No explicit definition matching the selection criteria was identified in the retrieved literature."
    )

    result = {
        "term": term,
        "apa_entry": apa_entry,
        "definition": definition_from_literature,
        "definition_method": definition_method,
        "generated_definition": generated_definition,
        "llm_usage": llm_usage,
        "evidence": retrieved,
        "pmids": pmids,
        "pmid_to_pmcid": pmid_to_pmcid,
    }

    save_pipeline_result(result)

    return result

  