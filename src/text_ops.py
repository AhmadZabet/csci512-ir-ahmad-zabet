"""Tokenization policy for the project's English collections."""

import re

_ACRONYM = re.compile(r"\b(?:[a-z]\.)+[a-z]\b\.?")
_THOUSANDS = re.compile(r"\b[0-9]{1,3}(?:,[0-9]{3})+\b")
_TOKEN = re.compile(r"[0-9]+\.[0-9]+|[a-z0-9]+")
_APOSTROPHES = str.maketrans({"\u2019": "'", "\u2018": "'"})


def tokenize(text: str) -> list[str]:
    """Return normalized tokens in their original order, with repeats.

    Policy:
    - Lowercase.
    - Join dotted acronyms: U.S.A. and U.S.A become usa.
    - Keep integers and decimals; remove thousands-group commas.
    - Split hyphens and other punctuation into token boundaries.
    - Remove trailing 's, then delete remaining apostrophes.
    - Keep alphanumeric terms such as b52 and 3d.
    - Match ASCII letters and digits; other characters are separators.

    Does not remove stopwords or stem words.
    """
    text = text.lower().translate(_APOSTROPHES)

    # Handle meaningful punctuation before extracting tokens.
    text = _ACRONYM.sub(
        lambda match: match.group().replace(".", ""),
        text,
    )
    text = _THOUSANDS.sub(
        lambda match: match.group().replace(",", ""),
        text,
    )
    text = re.sub(r"'s\b", "", text)
    text = text.replace("'", "")

    return _TOKEN.findall(text)