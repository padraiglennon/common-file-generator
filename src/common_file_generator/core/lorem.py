"""Seeded lorem-ipsum filler text (standard library only).

Used by generate mode to populate slides with placeholder content. All output is
driven by a caller-supplied :class:`random.Random`, so the same seed yields the
same text - generated decks are reproducible.
"""

from __future__ import annotations

import random

_WORDS = [
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipiscing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
    "enim",
    "ad",
    "minim",
    "veniam",
    "quis",
    "nostrud",
    "exercitation",
    "ullamco",
    "laboris",
    "nisi",
    "aliquip",
    "ex",
    "ea",
    "commodo",
    "consequat",
    "duis",
    "aute",
    "irure",
    "in",
    "reprehenderit",
    "voluptate",
    "velit",
    "esse",
    "cillum",
    "fugiat",
    "nulla",
    "pariatur",
    "excepteur",
    "sint",
    "occaecat",
    "cupidatat",
    "non",
    "proident",
    "sunt",
    "culpa",
    "qui",
    "officia",
    "deserunt",
    "mollit",
    "anim",
    "id",
    "est",
    "laborum",
]


class Lorem:
    """Generates lorem-ipsum words, sentences, and titles from a seeded RNG."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def words(self, count: int) -> str:
        return " ".join(self._rng.choice(_WORDS) for _ in range(max(count, 1)))

    def title(self, max_words: int = 5) -> str:
        n = self._rng.randint(2, max(2, max_words))
        return self.words(n).title()

    def sentence(self, min_words: int = 6, max_words: int = 14) -> str:
        n = self._rng.randint(min_words, max(min_words, max_words))
        return self.words(n).capitalize() + "."

    def paragraph(self, min_sentences: int = 2, max_sentences: int = 4) -> str:
        n = self._rng.randint(min_sentences, max(min_sentences, max_sentences))
        return " ".join(self.sentence() for _ in range(n))

    def bullets(self, count: int) -> list[str]:
        return [self.sentence(4, 9) for _ in range(max(count, 1))]
