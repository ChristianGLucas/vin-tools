"""Shared VIN normalization/decoding helpers for every node in this package.

Wraps the vininfo library (BSD-3-Clause, github.com/idlesign/vininfo) — it
owns the ISO 3779/3780 reference data (WMI table, country/region tables,
manufacturer-specific detail extractors) and the check-digit/model-year
algorithms. This module adds: up-front structural validation with a bounded,
never-crashing error contract, and the NHTSA/SAE position-7 model-year
disambiguation rule that vininfo itself does not apply.
"""

import re

from vininfo import Vin
from vininfo.common import UnsupportedBrand
from vininfo.exceptions import VininfoException

# A real VIN is always exactly 17 characters. Reject absurd input up front,
# before any regex/library work, rather than trusting the caller.
_MAX_INPUT_LEN = 256

_VALID_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

# Standard ISO 3779 / SAE J853 model-year letters+digits, repeating every 30
# years starting 1980. I, O, Q, U, Z, and 0 are excluded/reserved and never
# appear as a year code.
_YEAR_LETTERS = "ABCDEFGHJKLMNPRSTVWXY123456789"


class NormalizationError(Exception):
    """Raised by normalize_vin() with a machine-readable (code, detail) pair."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def normalize_vin(raw: str) -> str:
    """Trim + upper-case, then structurally validate a candidate VIN.

    Returns the normalized 17-char VIN string on success. Raises
    NormalizationError(code, detail) on any structural problem — callers
    turn this into their message's `error`/`detail` fields, never a crash.
    """
    if raw is None:
        raise NormalizationError("EMPTY", "vin field was not provided")

    if len(raw) > _MAX_INPUT_LEN:
        raise NormalizationError(
            "WRONG_LENGTH",
            f"input is {len(raw)} chars, far beyond any valid VIN (17); rejected before processing",
        )

    normalized = raw.strip().upper()

    if not normalized:
        raise NormalizationError("EMPTY", "vin field was empty (or all whitespace)")

    if len(normalized) != 17:
        raise NormalizationError(
            "WRONG_LENGTH",
            f"VIN must be exactly 17 characters after trimming, got {len(normalized)}",
        )

    if not _VALID_VIN_RE.match(normalized):
        allowed = set("ABCDEFGHJKLMNPRSTUVWXYZ0123456789")
        bad_chars = sorted({c for c in normalized if c not in allowed})
        detail = "VIN must contain only digits and letters, excluding I, O, and Q"
        if bad_chars:
            detail += f" (invalid character(s) found: {', '.join(bad_chars)})"
        raise NormalizationError("INVALID_CHARACTERS", detail)

    return normalized


def build_vin(normalized: str):
    """Construct a vininfo.Vin from an already-normalized 17-char VIN.

    Wraps construction (and the manufacturer-detail-extractor lookup it runs
    internally) in a broad catch: a wrapped library can raise late, on
    lazy/internal validation, outside a narrow try/except — so this widens
    to the library's whole exception surface plus any other unexpected
    failure, converting it to NormalizationError rather than crashing.
    """
    try:
        return Vin(normalized)
    except NormalizationError:
        raise
    except (VininfoException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise NormalizationError("DECODE_FAILED", f"VIN could not be decoded: {exc}") from exc


# SAE J853 / ISO 3779 transliteration table: each VIN character maps to a
# digit value used in the weighted check-digit computation below. This is a
# from-scratch implementation of the public standard (not delegated to the
# wrapped library), so `expected_check_digit` is always available, even for
# a manufacturer that doesn't follow the rule.
_TRANSLITERATION = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}
_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)


def compute_expected_check_digit(normalized_vin: str) -> str:
    """Compute the SAE J853 / ISO 3779 position-9 check digit that a VIN's
    other 16 characters imply, independent of what's actually there."""
    total = 0
    for pos, char in enumerate(normalized_vin):
        value = _TRANSLITERATION.get(char, char)
        total += int(value) * _WEIGHTS[pos]

    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def detail_to_str(wrapper) -> str:
    """Safely render a vininfo DetailWrapper (body/engine/model/plant/
    transmission/serial) to a string.

    vininfo's own DetailWrapper.__str__ does `return self.name or self.code`
    — but some manufacturer tables map one code to a LIST of ambiguous names
    (on genuinely real VINs, e.g. several Nissan body/model codes), and
    Python raises TypeError when __str__ returns a non-string. This is a
    late, input-triggered crash in the wrapped library, not a hypothetical:
    a realistic Nissan VIN reproduces it. Never call str(wrapper) directly —
    always go through this function instead.
    """
    if not wrapper:
        return ""
    name = wrapper.name
    if isinstance(name, list):
        return " / ".join(str(n) for n in name)
    if name:
        return str(name)
    code = wrapper.code
    return str(code) if code else ""


def is_manufacturer_known(vin_obj) -> bool:
    """True when the WMI resolved to a real manufacturer entry.

    vininfo's UnsupportedBrand fallback sets `.manufacturer` to its own class
    name ("UnsupportedBrand") rather than leaving it empty when the WMI
    isn't in the reference database — callers must check this explicitly
    rather than trusting `.manufacturer` truthiness.
    """
    return not isinstance(vin_obj.assembler, UnsupportedBrand)


def position_7_cycle(position_7_char: str):
    """NHTSA/SAE position-7 rule (49 CFR 565.16, note to Table VII).

    Returns "1980-2009" when position 7 is numeric, "2010-2039" when it is
    alphabetic, or None if position 7 is itself not a valid VIN character.
    """
    if not position_7_char:
        return None
    if position_7_char.isdigit():
        return "1980-2009"
    if position_7_char.isalpha():
        return "2010-2039"
    return None


def decode_model_year(vin_obj):
    """Return (year_code, candidate_years, most_likely_year, position_7_char, error).

    candidate_years comes straight from vininfo's own 30-year-cycle expansion
    (ambiguous by construction). most_likely_year applies the position-7 rule
    above to pick the single most probable candidate; -1 if none survive.
    """
    year_code = vin_obj.years_code
    candidate_years = list(vin_obj.years)
    # VIN position 7 is index 6 of the FULL 17-char VIN (vin_obj.num) — NOT
    # index 6 of `vis` (which starts at overall position 10, i.e. that would
    # be overall position 16). Get this wrong and the position-7 rule below
    # silently disambiguates against the wrong character.
    position_7_char = vin_obj.num[6] if len(vin_obj.num) > 6 else ""

    if year_code not in _YEAR_LETTERS:
        return year_code, [], -1, position_7_char, "UNRECOGNIZED_YEAR_CODE"

    cycle = position_7_cycle(position_7_char)
    most_likely = -1
    if cycle == "1980-2009":
        for y in candidate_years:
            if 1980 <= y <= 2009:
                most_likely = y
                break
    elif cycle == "2010-2039":
        for y in candidate_years:
            if 2010 <= y <= 2039:
                most_likely = y
                break

    if most_likely == -1 and candidate_years:
        # Rare case (e.g. a manufacturer with a non-standard position 7):
        # fall back to the most recent candidate rather than reporting none.
        most_likely = candidate_years[0]

    return year_code, candidate_years, most_likely, position_7_char, ""
