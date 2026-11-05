"""The example corpus the retrieval and scoring listings reuse (Listing 2.2).

On-brand: copy that cleared review. Off-brand: the register the brand avoids,
used as negatives in section 2.4. Small on purpose; Chapter 4 turns this into a
real, queryable corpus.
"""

APPROVED_COPY: list[str] = [
    "The shell is here. A 10K/10K waterproof-breathable rating, taped "
    "seams, and a face fabric that is 63% recycled.",
    "Built for the days the forecast is wrong. The Cascade packs to the "
    "size of a water bottle and weighs under 12 ounces.",
    "Three layers, one job: keep the weather out and let the sweat go. "
    "The rating is 10K/10K, measured, not rounded up.",
    "New colorway, same shell. The Ridgeline fleece now comes in slate. "
    "A merino blend, flatlock seams, no tag itch.",
]

OFF_BRAND_COPY: list[str] = [
    "Conquer any storm in the revolutionary all-new Cascade jacket!",
    "The ultimate waterproof shell for your next adventure. Buy yours today!",
    "This game-changing jacket will supercharge your next expedition.",
    "The most incredible, must-have outerwear of the season is finally here.",
]


if __name__ == "__main__":
    print(f"{len(APPROVED_COPY)} approved, {len(OFF_BRAND_COPY)} off-brand lines")
