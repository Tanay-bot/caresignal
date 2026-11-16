"""Frozen fictional notes for the credential-free walkthrough.

These are authored test inputs, not Fruta records or a held-out experiment.
"""

from datetime import date

DEMO_DATE = date(2026, 1, 15)
DEMO_NOTE = (
    "This morning she needed an aide beside her on the way to breakfast. "
    "She ate her breakfast in the dining room."
)
DEMO_REPLACEMENT = (
    "This morning she walked to breakfast with her walker. "
    "The note does not say whether anyone helped during the walk."
)
WALKING_ATTEMPT_NOTE = (
    "She tried walking to the lounge this morning. "
    "An aide held her arm and steadied her while she took several steps. "
    "Later, her roommate walked independently to lunch."
)
WALKING_ATTEMPT_QUOTE = (
    "She tried walking to the lounge this morning. "
    "An aide held her arm and steadied her while she took several steps."
)
FIXTURE_VERSION = "fictional-walkthrough-v1"


# Exact frozen public development example; provenance lives beside the checkout
# in data/fruta_nn_1093.json. These constants keep fixture use wheel-safe.
FRUTA_NOTE = (
    "The resident attempted to walk on her own, but found that she needed support. "
    "We gave her physical support and clarified safety."
)
FRUTA_DATE = date(2024, 3, 7)
FRUTA_RESIDENT_NAME = "Fruta synthetic resident cn_04"
FRUTA_TARGET_CUE = "attempt to walk on her own"
