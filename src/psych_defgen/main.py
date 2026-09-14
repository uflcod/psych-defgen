import os

import click

from psych_defgen.pipeline import run_pipeline

def save_output(
    term,
    apa_entry,
    definition_from_literature,
    evidence,
    output_path=None,
    output_dir="outputs",
):
    """
    Save the definition found in the literature and the retrieved
    evidence as a Markdown file.
    """

    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    if output_path:
        filepath = output_path

        os.makedirs(
            os.path.dirname(filepath) or ".",
            exist_ok=True,
        )

    else:
        filename = (
            f"{term.replace(' ', '_')}_definition.md"
        )

        filepath = os.path.join(
            output_dir,
            filename,
        )

    with open(
        filepath,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            f"# {term}\n\n"
        )

        # -------------------------------------------------
        # APA Dictionary
        # -------------------------------------------------

        file.write(
            "## APA Dictionary\n\n"
        )

        apa_status = apa_entry.get("status")
        apa_url = apa_entry.get("url")

        if apa_status == "found":

            file.write(
                "An entry for this term was found in "
                "the APA Dictionary of Psychology.\n\n"
            )

            file.write(
                "The APA Dictionary is provided as an "
                "external reference only and is not used "
                "to identify definitions in the literature. \n\n"
            )

            file.write(
                f"Reference: "
                f"[APA Dictionary Entry]({apa_url})\n\n"
            )

        elif apa_status == "not_found":

            file.write(
                "No entry for this term was found in "
                "the APA Dictionary of Psychology.\n\n"
            )

            file.write(
                "This does not affect the search for "
                "a definition in the retrieved literature.\n\n"
            )

        elif apa_status == "unavailable":

            file.write(
                "The presence of an APA Dictionary entry "
                "could not be verified automatically.\n\n"
            )

            file.write(
                f"Reference: "
                f"[Search the APA Dictionary]({apa_url})"
                "\n\n"
            )

        else:

            file.write(
                "The APA Dictionary of Psychology could "
                "not be accessed automatically.\n\n"
            )

            file.write(
                f"Reference: "
                f"[APA Dictionary]({apa_url})\n\n"
            )

        # -------------------------------------------------
        # Definition found in literature
        # -------------------------------------------------

        file.write(
            "## Definition from Literature\n\n"
        )

        file.write(
            definition_from_literature.strip()
            + "\n\n"
        )

        # -------------------------------------------------
        # Retrieved Evidence
        # -------------------------------------------------

        file.write(
            "## Retrieved Evidence\n\n"
        )

        if not evidence:
            file.write(
                "No relevant evidence was retrieved.\n\n"
            )

        for index, item in enumerate(
            evidence,
            start=1,
        ):
            file.write(
                f"### Evidence {index}\n\n"
            )

            score = item.get("score")

            if score is not None:
                file.write(
                    f"**Score:** {score:.4f}\n\n"
                )

            title = item.get("title")

            if title:
                file.write(
                    f"**Article:** {title}\n\n"
                )

            authors = item.get("authors")

            if authors:

                if isinstance(
                    authors,
                    list,
                ):
                    authors = ", ".join(authors)

                file.write(
                    f"**Authors:** {authors}\n\n"
                )

            journal = item.get("journal")
            year = item.get("year")

            if journal and year:

                file.write(
                    f"**Journal:** "
                    f"{journal} ({year})\n\n"
                )

            elif journal:

                file.write(
                    f"**Journal:** {journal}\n\n"
                )

            elif year:

                file.write(
                    f"**Year:** {year}\n\n"
                )

            source = item.get("source")

            if source:
                file.write(
                    f"**Source:** {source}\n\n"
                )

            pmid = item.get("pmid")

            if pmid:
                file.write(
                    f"**PMID:** {pmid}\n\n"
                )

            pmcid = item.get("pmcid")

            if pmcid:
                file.write(
                    f"**PMCID:** {pmcid}\n\n"
                )

            pubmed_url = item.get(
                "pubmed_url"
            )

            if pubmed_url:
                file.write(
                    "**PubMed:** "
                    f"[View article]"
                    f"({pubmed_url})\n\n"
                )

            article_url = item.get("url")

            if article_url:
                file.write(
                    "**Full text:** "
                    f"[View article]"
                    f"({article_url})\n\n"
                )

            file.write(
                "**Evidence:**\n\n"
            )

            file.write(
                item["text"].strip()
                + "\n\n"
            )

        # -------------------------------------------------
        # Curation status
        # -------------------------------------------------

        file.write(
            "## Curation Status\n\n"
        )

        file.write(
            "Needs expert review.\n"
        )

    return filepath


@click.command()
@click.option(
    "--max-results",
    default=100,
    show_default=True,
    type=int,
)
@click.option(
    "--top-k",
    default=10,
    show_default=True,
    type=int,
)
@click.option(
    "--email",
    default=None,
    help=(
        "NCBI email address. Overrides the "
        "NCBI_EMAIL environment variable."
    ),
)
@click.option(
    "--api-key",
    default=None,
    help=(
        "NCBI API key. Overrides the "
        "NCBI_API_KEY environment variable."
    ),
)
@click.option(
    "--output",
    default=None,
    help=(
        "Output Markdown file. "
        "If omitted, a file is created in the "
        "outputs directory."
    ),
)
@click.argument(
    "term",
    nargs=-1,
    required=True,
)
def main(
    max_results,
    top_k,
    email,
    api_key,
    output,
    term,
):
    """
    Find an explicit definition of a psychological
    construct in retrieved PubMed abstracts and PMC
    full-text literature.

    The APA Dictionary is used only to verify and
    reference official entries and is not used as
    evidence when identifying definitions from the
    literature.
    """

    term = " ".join(term)

    email = (
        email
        or os.getenv("NCBI_EMAIL")
    )

    api_key = (
        api_key
        or os.getenv("NCBI_API_KEY")
    )

    if not email:
        raise click.ClickException(
            "An NCBI email address is required. "
            "Provide it using --email or set the "
            "NCBI_EMAIL environment variable."
        )


    # -------------------------------------------------
    # Run shared retrieval pipeline
    # -------------------------------------------------

    result = run_pipeline(
        term=term,
        max_results=max_results,
        top_k=top_k,
        email=email,
        api_key=api_key,
    )


    print(
        "DEBUG APA:",
        type(result["apa_entry"]),
        result["apa_entry"],
    )

    # =====================================================
    # Save output
    # =====================================================

    output_path = save_output(
        term=term,
        apa_entry=result["apa_entry"],
        definition_from_literature=result["definition"],
        evidence=result["evidence"],
        output_path=output,
    )

    print(
        f"Saved output to: {output_path}"
    )


if __name__ == "__main__":
    main()
