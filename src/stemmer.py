"""Building blocks for Porter's original stemming algorithm.

Inputs are lowercase words from our normalization pipeline.
"""


def consonants(word: str) -> list[bool]:
    """Classify each character: True for consonant, False for vowel.

    Porter treats y as:
    - A consonant at the beginning.
    - Otherwise, the opposite of the preceding character.
    """

    flags = []

    for letter in word:
        if letter in "aeiou":
            flags.append(False)

        elif letter == "y":
            # Initial y is a consonant.
            # Other y characters reverse the previous classification.
            flags.append(True if not flags else not flags[-1])

        else:
            flags.append(True)

    return flags


def measure(word: str) -> int:
    """Calculate Porter's m: the number of vowel-to-consonant transitions."""

    flags = consonants(word)

    # zip pairs neighboring classifications.
    # Each False -> True pair is one vowel-to-consonant transition.
    return sum(
        not left and right
        for left, right in zip(flags, flags[1:])
    )


def contains_vowel(word: str) -> bool:
    """Implement *v*: return True if the word contains a Porter vowel."""

    return any(
        not flag
        for flag in consonants(word)
    )


def ends_double_consonant(word: str) -> bool:
    """Implement *d*: a repeated final letter that is a consonant."""

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