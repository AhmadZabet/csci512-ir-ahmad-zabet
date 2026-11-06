"""Porter stemming: conditions and Step 1.

This is the first part of our original Porter implementation.
Inputs are lowercase words from the normalization pipeline.
"""


def consonants(word: str) -> list[bool]:
    """Classify characters: True for consonant, False for vowel.

    Initial y is a consonant.
    Otherwise, y takes the opposite classification of the previous letter.
    """

    flags = []

    for letter in word:
        if letter in "aeiou":
            flags.append(False)

        elif letter == "y":
            flags.append(True if not flags else not flags[-1])

        else:
            flags.append(True)

    return flags


def measure(word: str) -> int:
    """Return m: the number of vowel-to-consonant transitions."""

    flags = consonants(word)

    # Pair neighboring classifications and count V -> C transitions.
    return sum(
        not left and right
        for left, right in zip(flags, flags[1:])
    )


def contains_vowel(word: str) -> bool:
    """Implement *v*: check whether the candidate stem contains a vowel."""

    return any(
        not flag
        for flag in consonants(word)
    )


def ends_double_consonant(word: str) -> bool:
    """Implement *d*: check for a repeated final consonant."""

    return (
        len(word) >= 2
        and word[-1] == word[-2]
        and consonants(word)[-1]
    )


def ends_cvc(word: str) -> bool:
    """Implement *o*: final CVC, excluding final w, x, and y."""

    return (
        len(word) >= 3
        and consonants(word)[-3:] == [True, False, True]
        and word[-1] not in "wxy"
    )


def step1a(word: str) -> str:
    """Handle plural endings, considering the longest suffix first."""

    rules = (
        ("sses", "ss"),
        ("ies", "i"),
        ("ss", "ss"),
        ("s", ""),
    )

    for suffix, replacement in rules:
        if word.endswith(suffix):
            # Return immediately after the first matching rule.
            return word[:-len(suffix)] + replacement

    return word


def step1b(word: str) -> str:
    """Handle EED, ED, and ING, including cleanup after ED/ING removal."""

    # Check EED before ED because it is the longer matching suffix.
    if word.endswith("eed"):
        stem = word[:-3]

        if measure(stem) > 0:
            return stem + "ee"

        # A failed EED condition must not fall through to the ED rule.
        return word

    for suffix in ("ed", "ing"):
        if word.endswith(suffix):
            stem = word[:-len(suffix)]

            # ED/ING removal requires a vowel in the candidate stem.
            if not contains_vowel(stem):
                return word

            # Cleanup applies only after ED or ING has been removed.

            # Restore E after AT, BL, or IZ.
            if stem.endswith(("at", "bl", "iz")):
                return stem + "e"

            # Remove one repeated consonant, except L, S, or Z.
            if ends_double_consonant(stem):
                if stem[-1] not in "lsz":
                    return stem[:-1]
                return stem

            # Restore E on a short CVC stem, such as fil -> file.
            if measure(stem) == 1 and ends_cvc(stem):
                return stem + "e"

            return stem

    return word


def step1c(word: str) -> str:
    """Replace final Y with I when the preceding stem contains a vowel."""

    if word.endswith("y"):
        stem = word[:-1]

        if contains_vowel(stem):
            return stem + "i"

    return word


def step1(word: str) -> str:
    """Apply Steps 1a, 1b, and 1c in order.

    This returns the intermediate Step 1 result, not the final Porter stem.
    """

    word = step1a(word)
    word = step1b(word)
    word = step1c(word)

    return word