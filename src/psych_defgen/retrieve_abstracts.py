import re

from Bio import Entrez

from .entrez_config import configure_entrez


def _extract_authors(author_list):
    """Extract readable author names from PubMed author records."""
    authors = []

    for author in author_list or []:
        collective_name = author.get("CollectiveName")

        if collective_name:
            authors.append(str(collective_name))
            continue

        last_name = author.get("LastName")
        initials = author.get("Initials")
        fore_name = author.get("ForeName")

        if last_name and initials:
            authors.append(f"{last_name} {initials}")
        elif fore_name and last_name:
            authors.append(f"{fore_name} {last_name}")
        elif last_name:
            authors.append(str(last_name))

    return authors


def _extract_abstract_text(abstract_sections):
    """Combine PubMed abstract sections, preserving section labels."""
    sections = []

    for section in abstract_sections or []:
        text = str(section).strip()

        if not text:
            continue

        label = getattr(section, "attributes", {}).get("Label")
        sections.append(f"{label}: {text}" if label else text)

    return "\n".join(sections)


def _extract_publication_year(article_record):
    """Extract the publication year from PubMed journal date metadata."""
    pub_date = (
        article_record.get("MedlineCitation", {})
        .get("Article", {})
        .get("Journal", {})
        .get("JournalIssue", {})
        .get("PubDate", {})
    )

    year = pub_date.get("Year")

    if year:
        return str(year)

    medline_date = pub_date.get("MedlineDate", "")
    match = re.search(r"\b(?:19|20)\d{2}\b", str(medline_date))

    return match.group(0) if match else None


def fetch_pubmed_abstracts(pmids, email=None, api_key=None):
    """
    Retrieve PubMed abstracts and associated article metadata.

    Return records containing article identifiers, title,
    authors, journal, publication year, abstract, and source URL.
    """
    configure_entrez(email=email, api_key=api_key)

    if not pmids:
        return []

    handle = Entrez.efetch(
        db="pubmed",
        id=",".join(str(pmid) for pmid in pmids),
        rettype="medline",
        retmode="xml",
    )

    try:
        records = Entrez.read(handle)
    finally:
        handle.close()

    abstract_records = []

    for pubmed_article in records.get("PubmedArticle", []):
        medline_citation = pubmed_article.get("MedlineCitation", {})
        article = medline_citation.get("Article", {})

        pmid = str(medline_citation.get("PMID", "")).strip()
        title = str(article.get("ArticleTitle", "Title unavailable")).strip()

        abstract_text = _extract_abstract_text(
            article.get("Abstract", {}).get("AbstractText", [])
        )

        if not abstract_text:
            continue

        authors = _extract_authors(article.get("AuthorList", []))
        journal = str(article.get("Journal", {}).get("Title", "")).strip()
        year = _extract_publication_year(pubmed_article)

        abstract_records.append(
            {
                "pmid": pmid or None,
                "title": title,
                "authors": authors,
                "journal": journal or None,
                "year": year,
                "abstract": abstract_text,
                "source": "PubMed abstract",
                "pubmed_url": (
                    f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    if pmid else None
                ),
            }
        )

    return abstract_records