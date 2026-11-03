from Bio import Entrez

from .entrez_config import configure_entrez


def search_pubmed(term, max_results=100, email=None, api_key=None):
    """
    Search PubMed for articles containing the psychological construct
    in their title or abstract, sorted by relevance.

    Return PubMed IDs up to the specified maximum number of results.
    """
    configure_entrez(email=email, api_key=api_key)

    query = f'"{term}"[Title/Abstract]'

    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=max_results,
        sort="relevance",
    )

    try:
        record = Entrez.read(handle)
    finally:
        handle.close()

    return record["IdList"]

def fetch_pubmed_authors(pmids, email=None, api_key=None):
    """
    Retrieve authors for selected PubMed articles.
    Returns a dictionary mapping PMID to author names.
    """
    if not pmids:
        return {}

    configure_entrez(email=email, api_key=api_key)

    handle = Entrez.efetch(
        db="pubmed",
        id=",".join(map(str, pmids)),
        retmode="xml",
    )

    try:
        records = Entrez.read(handle)
    finally:
        handle.close()

    authors_by_pmid = {}

    for article in records.get("PubmedArticle", []):
        citation = article["MedlineCitation"]
        pmid = str(citation["PMID"])

        authors = []

        for author in citation["Article"].get("AuthorList", []):
            collective_name = author.get("CollectiveName")

            if collective_name:
                authors.append(str(collective_name))
                continue

            first_name = author.get("ForeName", "")
            last_name = author.get("LastName", "")

            full_name = f"{first_name} {last_name}".strip()

            if full_name:
                authors.append(full_name)

        authors_by_pmid[pmid] = authors

    return authors_by_pmid