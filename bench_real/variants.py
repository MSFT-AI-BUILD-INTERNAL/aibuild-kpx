"""Variant V0..V5 — same definitions as plan v2 §7."""
from __future__ import annotations

from kpx.compress import compress
from kpx.methods import inject_no_filler


def apply_variant(variant: str, system: str, user: str) -> tuple[str, str]:
    """Return (system_out, user_out) after applying the variant.

    By kpx's design, all transforms operate on the system prompt only;
    the user message is passed through unchanged.
    """
    if variant == "V0":
        return system, user
    if variant == "V1":
        return compress(system, methods=["M03"]), user
    if variant == "V2":
        return compress(system, methods=["M24"]), user
    if variant == "V3":
        return compress(system, methods=["M03", "M24", "M25"]), user
    if variant == "V4":
        return compress(system, methods=["M03", "M04", "M19", "M24", "M25"]), user
    if variant == "V5":
        s = compress(system, methods=["M03", "M04", "M19", "M24", "M25"])
        return inject_no_filler(s), user
    raise ValueError(f"unknown variant: {variant}")


VARIANTS = ["V0", "V1", "V2", "V3", "V4", "V5"]
LITE_VARIANTS = ["V0", "V3", "V4"]
