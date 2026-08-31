from psych_defgen.select_definition_sentence import (
    select_best_definition_sentence,
)


def test_selects_explicit_definition():
    items = [
        {
            "text": (
                "Loneliness is defined as a distressing "
                "feeling resulting from unmet social needs."
            ),
            "score": 0.9,
        }
    ]

    result = select_best_definition_sentence(
        "loneliness",
        items,
    )

    assert result is not None
    assert result.startswith(
        "Loneliness is defined as"
    )


def test_rejects_non_definition():
    items = [
        {
            "text": (
                "Loneliness was examined as a predictor "
                "of health outcomes."
            ),
            "score": 0.9,
        }
    ]

    result = select_best_definition_sentence(
        "loneliness",
        items,
    )

    assert result is None


def test_selects_definition_with_the_prefix():
    items = [
        {
            "text": (
                "The social environment refers to the relationships, "
                "culture, and society that individuals interact with."
            ),
            "score": 0.9,
        }
    ]

    result = select_best_definition_sentence(
        "social environment",
        items,
    )

    assert result is not None
    assert result.startswith(
        "The social environment refers to"
    )


def test_rejects_noisy_non_definition():
    items = [
        {
            "text": (
                "Social environment support affecting loneliness "
                "in older adults and community involvement."
            ),
            "score": 0.9,
        }
    ]

    result = select_best_definition_sentence(
        "social environment",
        items,
    )

    assert result is None


def test_selects_was_defined_as_definition():
    items = [
        {
            "text": (
                "Living status was defined as either independent "
                "(home) or assisted (nursing home, assisted living "
                "facility, rehabilitation facility)."
            ),
            "score": 0.7053,
        }
    ]

    result = select_best_definition_sentence(
        "living status",
        items,
    )

    assert result is not None
    assert result.startswith(
        "Living status was defined as"
    )


def test_selects_plural_definition_for_singular_term():
    items = [
        {
            "text": (
                "Psychosocial factors have been defined as "
                "characteristics or facets that influence an "
                "individual psychologically and/or socially."
            ),
            "score": 0.8446,
        }
    ]

    result = select_best_definition_sentence(
        "psychosocial factor",
        items,
    )

    assert result is not None
    assert result.startswith(
        "Psychosocial factors have been defined as"
    )