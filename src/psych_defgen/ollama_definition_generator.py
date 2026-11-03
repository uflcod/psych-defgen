"""Generate evidence-grounded psychological construct definitions using LLMs."""

from psych_defgen.llm_provider import generate_llm_response


def generate_definition_with_llm(
    term: str,
    evidence: list[dict],
    model: str = "qwen2.5:7b",
    top_k: int = 10,
    provider: str = "ollama",
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    
    """
    Generate a definition using only retrieved evidence passages.

    Args:
        term: Psychological construct to define.
        evidence: Ranked evidence records from semantic retrieval.
        model: Model name for the selected LLM provider.
        top_k: Maximum number of evidence passages to use.
        provider: LLM provider, such as Ollama or OpenAI.
        api_key: API key for providers requiring authentication.
        base_url: Optional custom provider endpoint.

    Returns:
        A consolidated evidence-grounded definition.
    """

    passages = []

    for index, item in enumerate(evidence[:top_k], start=1):

        passage = (
            item.get("context_text")
            or item.get("text")
            or ""
        ).strip()

        if passage:
            passages.append(
                f"Evidence {index}:\n{passage}"
            )

    if not passages:
        return "Insufficient evidence to generate a definition."

    evidence_text = "\n\n".join(passages)

    system_prompt = """
You generate evidence-based definitions of psychological constructs.

Use ONLY the provided evidence passages.

Rules:
1. Identify information directly relevant to defining the construct.
2. Combine useful information from the evidence passages.
3. Remove repetition and redundant information.
4. Rephrase or reorganize wording only when necessary.
5. Begin with an appropriate class or category supported by the evidence.
6. Do not add information from external knowledge.
7. Do not invent characteristics, causes, functions, or outcomes.
8. Do not introduce interpretations absent from the evidence.
9. Do not force information from irrelevant passages into the definition.
10. If the evidence is insufficient, return exactly:
    Insufficient evidence to generate a definition.
11. Return only one concise, coherent definition.
"""

    user_prompt = f"""
Psychological construct: {term}

Retrieved evidence passages:

{evidence_text}

Generate a consolidated definition using only the evidence above.
"""

    return generate_llm_response(
        prompt=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
    ).strip()