import re


EXPLICIT_DEFINITION_PATTERNS = [
    "is defined as",
    "was defined as",
    "are defined as",
    "were defined as",
    "has been defined as",
    "have been defined as",
    "can be defined as",
    "refers to",
    "refer to",
    "is a ",
    "is an ",
    "is the ",
    "is characterized by",
    "are characterized by",
    "is conceptualized as",
    "are conceptualized as",
    "is understood as",
    "are understood as",
]


FALLBACK_DEFINITION_PATTERNS = [
    "involves",
    "occurs when",
    "stems from",
    "typically defined by",
    "defined by",
]


BAD_STUDY_PATTERNS = [
    "systematic review",
    "meta-analysis",
    "association between",
    "found that",
    "study investigating",
    "study examined",
    "study investigates",
    "risk of developing",
    "predictor of",
    "tested a",
    "tested as",
]


def split_sentences(text):
    return re.split(
        r"(?<=[.!?])\s+",
        text,
    )


def clean_sentence(sentence):
    sentence = re.sub(
        r"^\d+\s+",
        "",
        sentence,
    )

    sentence = re.sub(
        r"\s+",
        " ",
        sentence,
    )

    return sentence.strip()

def get_term_variants(term):
    """
    Return simple singular/plural variants of the
    requested term for definition matching.
    """

    term_lower = term.lower().strip()

    variants = {
        term_lower,
    }

    if term_lower.endswith("s"):
        variants.add(
            term_lower[:-1]
        )
    else:
        variants.add(
            f"{term_lower}s"
        )

    return variants


def normalize_for_matching(
    sentence,
    term,
):
    """
    Normalize simple extraction artifacts for
    matching.

    Example:

    "ECONOMIC STABILITY Economic stability is..."
    becomes temporarily:

    "Economic stability is..."

    This normalization is used for matching and
    selection only.
    """

    normalized = clean_sentence(
        sentence
    )

    term_lower = term.lower().strip()
    lower = normalized.lower()

    repeated_term = (
        f"{term_lower} {term_lower}"
    )

    if lower.startswith(
        repeated_term
    ):
        normalized = normalized[
            len(term):
        ].strip()

    return normalized


def get_term_start(
    sentence,
    term,
):
    """
    Return the matched beginning of a definition
    sentence.

    Supports forms such as:

    "social environment ..."
    "the social environment ..."
    "a social environment ..."
    """

    lower = sentence.lower().strip()

    term_variants = get_term_variants(
        term
    )

    valid_starts = []

    for variant in term_variants:
        valid_starts.extend(
            [
                variant,
                f"the {variant}",
                f"a {variant}",
            ]
        )

    for start in sorted(
        valid_starts,
        key=len,
        reverse=True,
    ):
        if lower.startswith(start):
            return start

    return None


def is_bad_study_sentence(
    sentence,
):
    """
    Reject sentences that clearly describe
    study design, associations, predictors,
    or review methodology rather than defining
    the requested construct.
    """

    lower = sentence.lower()

    return any(
        pattern in lower
        for pattern in BAD_STUDY_PATTERNS
    )


def is_explicit_definition_sentence(
    sentence,
    term,
):
    """
    Return True when the sentence contains an
    explicit definitional construction.
    """

    sentence = normalize_for_matching(
        sentence,
        term,
    )

    lower = sentence.lower()
    matched_start = get_term_start(
        sentence,
        term,
    )

    if matched_start is None:
        return False

    word_count = len(
        sentence.split()
    )

    if (
        word_count < 6
        or word_count > 60
    ):
        return False

    if is_bad_study_sentence(
        sentence
    ):
        return False

    remainder = lower[
        len(matched_start):
    ].strip()

    return any(
        remainder.startswith(pattern)
        for pattern in EXPLICIT_DEFINITION_PATTERNS
    )


def is_fallback_definition_sentence(
    sentence,
    term,
):
    """
    Return True for weaker conceptual statements
    that may be used only when no explicit
    definition is available.
    """

    sentence = normalize_for_matching(
        sentence,
        term,
    )

    lower = sentence.lower()
    matched_start = get_term_start(
        sentence,
        term,
    )

    if matched_start is None:
        return False

    word_count = len(
        sentence.split()
    )

    if (
        word_count < 6
        or word_count > 60
    ):
        return False

    if is_bad_study_sentence(
        sentence
    ):
        return False

    remainder = lower[
        len(matched_start):
    ].strip()

    return any(
        remainder.startswith(pattern)
        for pattern in FALLBACK_DEFINITION_PATTERNS
    )


def is_definition_sentence(
    sentence,
    term,
):
    """
    Return True when the sentence is either:

    1. an explicit definition, or
    2. a fallback conceptual definition.
    """

    return (
        is_explicit_definition_sentence(
            sentence,
            term,
        )
        or is_fallback_definition_sentence(
            sentence,
            term,
        )
    )


def normalize_term_prefix_for_scoring(
    sentence,
    term,
):
    """
    Normalize optional leading articles only for
    scoring.

    Example:

    "The social environment refers to..."
    becomes internally:

    "social environment refers to..."

    The original output sentence is preserved.
    """

    lower = sentence.lower().strip()
    term_lower = term.lower().strip()

    if lower.startswith(
        f"the {term_lower}"
    ):
        lower = lower[4:].strip()

    elif lower.startswith(
        f"a {term_lower}"
    ):
        lower = lower[2:].strip()

    return lower


def definition_score(
    sentence,
    term,
):
    """
    Score a valid definition sentence.

    Explicit definitions receive higher scores.

    Fallback constructions receive lower scores
    and are considered only when no explicit
    definition exists.
    """

    matching_sentence = normalize_for_matching(
        sentence,
        term,
    )
    
    lower = matching_sentence.lower().strip()

    term_variants = get_term_variants(
        term
    )

    # Remove optional leading articles for scoring.
    for variant in term_variants:
        if lower.startswith(
            f"the {variant}"
        ):
            lower = lower[4:].strip()
            break

        if lower.startswith(
            f"a {variant}"
        ):
            lower = lower[2:].strip()
            break

    strong_patterns = []

    for variant in term_variants:
        strong_patterns.extend(
            [
                f"{variant} is defined as",
                f"{variant} was defined as",
                f"{variant} are defined as",
                f"{variant} were defined as",
                f"{variant} has been defined as",
                f"{variant} have been defined as",
                f"{variant} can be defined as",
                f"{variant} refers to",
                f"{variant} refer to",
            ]
        )

    if any(
        lower.startswith(pattern)
        for pattern in strong_patterns
    ):
        return 100

    conceptual_patterns = []

    for variant in term_variants:
        conceptual_patterns.extend(
            [
                f"{variant} is conceptualized as",
                f"{variant} are conceptualized as",
                f"{variant} is understood as",
                f"{variant} are understood as",
                f"{variant} is characterized by",
                f"{variant} are characterized by",
    
            ]
        )

    if any(
            lower.startswith(pattern)
            for pattern in conceptual_patterns
    ):
        return 80

    noun_definition_patterns = []

    for variant in term_variants:
        noun_definition_patterns.extend(
            [
                f"{variant} is a ",
                f"{variant} is an ",
                f"{variant} is the ",
            ]
        )

    if any(
        lower.startswith(pattern)
        for pattern in noun_definition_patterns
    ):
        return 70


    if is_fallback_definition_sentence(
        matching_sentence,
        term,
    ):

        fallback_patterns = []

        for variant in term_variants:
            fallback_patterns.extend(

                [
                    f"{variant} involves",
                    f"{variant} occurs when",
                    f"{variant} stems from",
                    f"{variant} typically defined by",
                    f"{variant} defined by",
                ]
            )

        if any(
            lower.startswith(pattern)
            for pattern in fallback_patterns
        ):
            return 50

        return 50

    return -1


def select_best_definition_sentence(
    term,
    retrieved_items,
):
    """
    Select the strongest definition sentence.

    Selection hierarchy:

    1. Prefer explicit definitions.
    2. Use fallback conceptual statements only
       when no explicit definition is available.
    3. Use retrieval similarity only as a
       tie-breaker within each category.
    """

    explicit_candidates = []
    fallback_candidates = []

    for item in retrieved_items:

        text = item.get(
            "text",
            "",
        )

        retrieval_score = item.get(
            "score",
            0.0,
        )

        for sentence in split_sentences(
            text
        ):

            original_sentence = clean_sentence(
                sentence
            )

            output_sentence = (
                normalize_for_matching(
                    original_sentence,
                    term,
                )
            )

            score = definition_score(
                output_sentence,
                term,
            )

            if score < 0:
                continue

            candidate = (
                score,
                retrieval_score,
                output_sentence,
            )

            if is_explicit_definition_sentence(
                output_sentence,
                term,
            ):
                explicit_candidates.append(
                    candidate
                )

            elif is_fallback_definition_sentence(
                output_sentence,
                term,
            ):
                fallback_candidates.append(
                    candidate
                )

    if explicit_candidates:
        candidates = explicit_candidates

    elif fallback_candidates:
        candidates = fallback_candidates

    else:
        return None

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    return candidates[0][2]