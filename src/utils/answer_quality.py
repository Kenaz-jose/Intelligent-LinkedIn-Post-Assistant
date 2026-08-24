"""
Deterministic quality checks on raw interview answers.

Runs before the brief is synthesised, while the answers can still be
improved by asking again. No LLM call - this decides whether asking a
follow-up is worth an LLM call, so it must be cheaper than one.
"""
import string

VAGUE_OPENERS = (
    "i think", "i guess", "i believe", "it depends", "generally",
    "usually", "in general", "these days", "a lot of", "many people",
    "i would say", "probably",
)

FIRST_PERSON = {"i", "we", "my", "our", "me", "us"}


def _effective_words(text: str) -> list[str]:
    """
    Word count after stripping a vague opener.

    "I think AI is changing everything" is six words, but four of them
    carry content. Hedging phrases inflate length without adding
    specifics, so they are removed before measuring.
    """
    lowered = text.strip().lower()

    for opener in VAGUE_OPENERS:
        if lowered.startswith(opener):
            lowered = lowered[len(opener):].lstrip(" ,-")
            break

    return lowered.split()


def answer_is_thin(text: str) -> bool:
    """
    True when an answer has too little to build a post on.

    Deliberately crude, and tuned to fire conservatively. A false
    positive costs one extra question; a false negative costs a generic
    post. Length is the primary signal, with numbers and first-person
    claims acting as rescuers for short but concrete answers.
    """
    words = _effective_words(text)

    if len(words) < 5:
        return True

    has_number = any(c.isdigit() for c in text)
    clean_words = {word.strip(string.punctuation) for word in words}
    has_first_person = bool(FIRST_PERSON & clean_words)


    if len(words) < 10 and not (has_number or has_first_person):
        return True

    return False


def thin_answers(answers: list) -> list:
    """Answers worth probing, thinnest first."""
    thin = [a for a in answers if answer_is_thin(a.answer)]
    return sorted(thin, key=lambda a: len(a.answer.split()))