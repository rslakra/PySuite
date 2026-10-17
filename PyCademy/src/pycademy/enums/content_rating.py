from enum import Enum


class ContentRating(Enum):
    """
    Content is judged only on what was said, not how it was delivered.

    Each member's value is the numeric rating. Its `meaning` and `anchor`
    describe what the rating stands for.
    """

    VERY_DISSATISFIED = (
        1,
        "Very dissatisfied",
        "Fails outright: completely irrelevant, wrong, dismissive, ignores the request or correction, "
        "violates a basic principle, is rude or NSFW, or refuses a reasonable request.",
    )
    SOMEWHAT_DISSATISFIED = (
        2,
        "Somewhat dissatisfied",
        "Largely fails: mostly unhelpful or off-topic, has a material omission or error, "
        "ignores a constraint or correction, contradicts itself, or simply agrees without helping.",
    )
    NEUTRAL = (
        3,
        "Neutral",
        "Partially satisfies the request but has a clear, non-disqualifying gap, such as a missed "
        "component, minor inaccuracy, or clumsy handling of context or correction.",
    )
    SOMEWHAT_SATISFIED = (
        4,
        "Somewhat satisfied",
        "Helpful and on target, with one minor shortcoming such as a small omission or slightly "
        "unsuitable length or level of detail.",
    )
    VERY_SATISFIED = (
        5,
        "Very satisfied",
        "Fully addresses the request accurately and relevantly, at the right depth and tone. "
        "Uses earlier context, honors constraints, stays consistent, applies corrections, "
        "and leaves no meaningful complaint.",
    )

    def __init__(self, rating: int, meaning: str, anchor: str):
        self._rating = rating
        self._meaning = meaning
        self._anchor = anchor

    @property
    def rating(self) -> int:
        """Returns the numeric rating (1-5)."""
        return self._rating

    @property
    def meaning(self) -> str:
        """Returns the short meaning of the rating."""
        return self._meaning

    @property
    def anchor(self) -> str:
        """Returns the description of what content earns this rating."""
        return self._anchor

    @classmethod
    def of(cls, rating: int) -> "ContentRating":
        """Returns the ContentRating for the given numeric rating."""
        for member in cls:
            if member.rating == rating:
                return member
        raise ValueError(f"Invalid content rating: {rating}. Expected a value between 1 and 5.")
