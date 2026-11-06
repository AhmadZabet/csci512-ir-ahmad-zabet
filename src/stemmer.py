"""Porter's original stemming algorithm: conditions and Steps 1–3.

Inputs are lowercase words from the normalization pipeline.
Steps 4 and 5 will be added next.
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
            return word[:-len(suffix)] + replacement

    return word


def step1b(word: str) -> str:
    """Handle EED, ED, and ING, including cleanup after ED/ING removal."""

    # EED must be checked before the shorter ED suffix.
    if word.endswith("eed"):
        stem = word[:-3]

        if measure(stem) > 0:
            return stem + "ee"

        # Do not try ED after a failed EED condition.
        return word

    for suffix in ("ed", "ing"):
        if word.endswith(suffix):
            stem = word[:-len(suffix)]

            # Removing ED or ING requires a vowel in the candidate stem.
            if not contains_vowel(stem):
                return word

            # Cleanup runs only after ED or ING was removed.

            # conflat -> conflate; troubl -> trouble; siz -> size.
            if stem.endswith(("at", "bl", "iz")):
                return stem + "e"

            # hopp -> hop, but preserve final LL, SS, and ZZ.
            if ends_double_consonant(stem):
                if stem[-1] not in "lsz":
                    return stem[:-1]
                return stem

            # fil -> file.
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
    """Apply Steps 1a, 1b, and 1c in order."""

    word = step1a(word)
    word = step1b(word)
    word = step1c(word)

    return word


# Original Porter 1980 Step 2 rules.
# The original rule is ABLI -> ABLE.
STEP2_RULES = (
    ("ational", "ate"),
    ("tional", "tion"),
    ("enci", "ence"),
    ("anci", "ance"),
    ("izer", "ize"),
    ("abli", "able"),
    ("alli", "al"),
    ("entli", "ent"),
    ("eli", "e"),
    ("ousli", "ous"),
    ("ization", "ize"),
    ("ation", "ate"),
    ("ator", "ate"),
    ("alism", "al"),
    ("iveness", "ive"),
    ("fulness", "ful"),
    ("ousness", "ous"),
    ("aliti", "al"),
    ("iviti", "ive"),
    ("biliti", "ble"),
)

# Original Porter 1980 Step 3 rules.
STEP3_RULES = (
    ("icate", "ic"),
    ("ative", ""),
    ("alize", "al"),
    ("iciti", "ic"),
    ("ical", "ic"),
    ("ful", ""),
    ("ness", ""),
)


def apply_measured_rules(word, rules, minimum_measure=0):
    """Apply the longest matching suffix if its stem has sufficient m.

    The condition is m > minimum_measure.
    If the longest match fails its condition, return the word unchanged.
    """

    ordered_rules = sorted(
        rules,
        key=lambda rule: len(rule[0]),
        reverse=True,
    )

    for suffix, replacement in ordered_rules:
        if word.endswith(suffix):
            stem = word[:-len(suffix)]

            # Test m on the candidate stem, excluding the suffix.
            if measure(stem) > minimum_measure:
                return stem + replacement

            # Never fall through to a shorter matching suffix.
            return word

    return word


def step2(word: str) -> str:
    """Simplify a Step 2 suffix when the candidate stem has m > 0."""

    return apply_measured_rules(
        word,
        STEP2_RULES,
        minimum_measure=0,
    )


def step3(word: str) -> str:
    """Simplify a Step 3 suffix when the candidate stem has m > 0."""

    return apply_measured_rules(
        word,
        STEP3_RULES,
        minimum_measure=0,
    )