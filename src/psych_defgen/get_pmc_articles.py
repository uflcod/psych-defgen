import time
from http.client import IncompleteRead

from Bio import Entrez

from .entrez_config import configure_entrez


def get_pmc_ids(pmids, email=None, api_key=None):
    """
    Retrieve PMC IDs corresponding to PubMed IDs.

    Retry incomplete NCBI responses up to three times
    and return a mapping of PubMed IDs to PMC IDs.
    """
    configure_entrez(email=email, api_key=api_key)

    if not pmids:
        return {}

    pmid_to_pmcid = {}

    for pmid in pmids:
        records = None

        for attempt in range(3):
            try:
                handle = Entrez.elink(
                    dbfrom="pubmed",
                    db="pmc",
                    id=str(pmid),
                    linkname="pubmed_pmc",
                )

                try:
                    records = Entrez.read(handle)
                finally:
                    handle.close()

                break

            except IncompleteRead as error:
                print(f"Incomplete NCBI response for PMID {pmid}: {error}")

                if attempt < 2:
                    time.sleep(1)
                else:
                    print(f"Skipping PMC lookup for PMID {pmid}.")

            except Exception as error:
                print(f"Could not retrieve PMC ID for PMID {pmid}: {error}")
                break

        if not records:
            continue

        link_sets = records[0].get("LinkSetDb", [])

        if not link_sets:
            continue

        links = link_sets[0].get("Link", [])

        if not links:
            continue

        pmid_to_pmcid[str(pmid)] = f"PMC{links[0]['Id']}"

    return pmid_to_pmcid