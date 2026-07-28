import re


def generate_definition(term, evidence_summary):
    """
    Generate a literature-derived definition.

    This function uses only the evidence summary generated from
    PubMed/PMC articles. It must not use APA Dictionary content
    when generating the definition.
    """

    if not evidence_summary or evidence_summary.startswith("No evidence"):
        return (
            f"{term.capitalize()} is a construct requiring expert review because "
            f"insufficient literature evidence was retrieved to generate a definition."
        )

    definition = re.sub(r"\s+", " ", evidence_summary).strip()

    return definition