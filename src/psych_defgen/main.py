
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
    Save the retrieved definition, APA Dictionary reference,
    supporting evidence, and curation status to a Markdown file.
    """
    if output_path:
        filepath = output_path
    else:
        filename = f"{term.replace(' ', '_')}_definition.md"
        filepath = os.path.join(output_dir, filename)

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(f"# {term}\n\n")
        file.write("## APA Dictionary\n\n")

        apa_status = apa_entry.get("status")
        apa_url = apa_entry.get("url")

        if apa_status == "found":
            file.write(
                "An entry for this term was found in the "
                "APA Dictionary of Psychology.\n\n"
                "The APA Dictionary is provided as an external "
                "reference only and is not used to identify "
                "definitions in the literature.\n\n"
            )
            if apa_url:
                file.write(f"Reference: [APA Dictionary Entry]({apa_url})\n\n")

        elif apa_status == "not_found":
            file.write(
                "No entry for this term was found in the "
                "APA Dictionary of Psychology.\n\n"
                "This does not affect the search for a definition "
                "in the retrieved literature.\n\n"
            )

        elif apa_status == "unavailable":
            file.write(
                "The presence of an APA Dictionary entry "
                "could not be verified automatically.\n\n"
            )
            if apa_url:
                file.write(f"Reference: [Search the APA Dictionary]({apa_url})\n\n")

        else:
            file.write(
                "The APA Dictionary of Psychology could "
                "not be accessed automatically.\n\n"
            )
            if apa_url:
                file.write(f"Reference: [APA Dictionary]({apa_url})\n\n")

        file.write("## Definition from Literature\n\n")
        file.write(definition_from_literature.strip() + "\n\n")

        file.write("## Retrieved Evidence\n\n")

        if not evidence:
            file.write("No relevant evidence was retrieved.\n\n")

        for index, item in enumerate(evidence, start=1):
            file.write(f"### Evidence {index}\n\n")

            score = item.get("score")
            if score is not None:
                file.write(f"**Passage similarity score:** {score:.4f}\n\n")

            sentence_score = item.get("sentence_score")
            if sentence_score is not None:
                file.write(
                    f"**Sentence similarity score:** "
                    f"{sentence_score:.4f}\n\n"
                )

            evidence_type = item.get("evidence_type")
            if evidence_type:
                file.write(f"**Evidence type:** {evidence_type}\n\n")

            for key, label in [
                ("title", "Article"),
                ("journal", "Journal"),
                ("year", "Year"),
                ("source", "Source"),
                ("pmid", "PMID"),
                ("pmcid", "PMCID"),
            ]:
                value = item.get(key)
                if value:
                    file.write(f"**{label}:** {value}\n\n")

            authors = item.get("authors")
            if authors:
                if isinstance(authors, list):
                    authors = ", ".join(authors)
                file.write(f"**Authors:** {authors}\n\n")

            pubmed_url = item.get("pubmed_url")
            if pubmed_url:
                file.write(f"**PubMed:** [View article]({pubmed_url})\n\n")

            article_url = item.get("url")
            if article_url:
                file.write(f"**Full text:** [View article]({article_url})\n\n")

            evidence_sentence = item.get("evidence_sentence")

            if evidence_sentence:
                file.write("**Relevant evidence sentence:**\n\n")
                file.write(evidence_sentence.strip() + "\n\n")
            else:
                file.write("**Evidence:**\n\n")
                file.write(item.get("text", "").strip() + "\n\n")

            original_passage = item.get("context_text")

            if original_passage and evidence_sentence:
                file.write("<details>\n")
                file.write("<summary>Original passage</summary>\n\n")
                file.write(original_passage.strip() + "\n\n")
                file.write("</details>\n\n")

        file.write("## Curation Status\n\n")
        file.write("Needs expert review.\n")

    return filepath


@click.command()
@click.option("--max-results", default=100, show_default=True, type=int)
@click.option("--top-k", default=10, show_default=True, type=int)
@click.option(
    "--email",
    default=None,
    help="NCBI email address. Overrides NCBI_EMAIL.",
)
@click.option(
    "--api-key",
    default=None,
    help="NCBI API key. Overrides NCBI_API_KEY.",
)
@click.option(
    "--output",
    default=None,
    help="Output Markdown file. Defaults to the outputs directory.",
)
@click.argument("term", nargs=-1, required=True)
def main(max_results, top_k, email, api_key, output, term):
    """
    Retrieve a psychological construct definition from PubMed
    and PMC literature and save the results as Markdown.

    The APA Dictionary is used only as an external reference,
    not as evidence for definition selection.
    """
    term = " ".join(term)

    email = email or os.getenv("NCBI_EMAIL")

    if not email:
        raise click.ClickException(
            "An NCBI email address is required. "
            "Provide --email or set NCBI_EMAIL."
        )

    result = run_pipeline(
        term=term,
        max_results=max_results,
        top_k=top_k,
        email=email,
        api_key=api_key,
    )

    output_path = save_output(
        term=term,
        apa_entry=result["apa_entry"],
        definition_from_literature=result["definition"],
        evidence=result["evidence"],
        output_path=output,
    )

    click.echo(f"Saved output to: {output_path}")


if __name__ == "__main__":
    main()
