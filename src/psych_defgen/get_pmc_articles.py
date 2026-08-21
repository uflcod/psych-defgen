import time
from http.client import IncompleteRead

from Bio import Entrez

from .entrez_config import configure_entrez


def get_pmc_ids(
    pmids,
    email=None,
    api_key=None,
):
    """
    Convert PubMed IDs to PMC IDs when full text is available.
    """

    configure_entrez(
        email=email,
        api_key=api_key,
    )

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

                records = Entrez.read(
                    handle
                )

                handle.close()

                break

            except IncompleteRead as error:

                print(
                    f"Incomplete NCBI response for "
                    f"PMID {pmid}: {error}"
                )

                if attempt < 2:
                    time.sleep(1)
                else:
                    print(
                        f"Skipping PMC lookup for "
                        f"PMID {pmid}."
                    )

            except Exception as error:

                print(
                    f"Could not retrieve PMC ID for "
                    f"PMID {pmid}: {error}"
                )

                break

        if not records:
            continue

        record = records[0]

        link_sets = record.get(
            "LinkSetDb",
            [],
        )

        if not link_sets:
            continue

        links = link_sets[0].get(
            "Link",
            [],
        )

        if not links:
            continue

        pmc_id_number = links[0]["Id"]

        pmcid = f"PMC{pmc_id_number}"

        pmid_to_pmcid[
            str(pmid)
        ] = pmcid

    return pmid_to_pmcid