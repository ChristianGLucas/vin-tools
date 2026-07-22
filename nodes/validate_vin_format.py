from gen.messages_pb2 import VinInput, FormatValidationResult
from gen.axiom_context import AxiomContext

from nodes._common import normalize_vin, NormalizationError


def validate_vin_format(ax: AxiomContext, input: VinInput) -> FormatValidationResult:
    """Validate a VIN's structural form per ISO 3779: exactly 17 characters,
    drawn only from the alphanumeric set that excludes I, O, and Q. Input is
    whitespace-trimmed and upper-cased before checking. Does NOT check the
    position-9 check digit (see VerifyCheckDigit) — this is form only.
    """
    try:
        normalized = normalize_vin(input.vin)
    except NormalizationError as exc:
        # Echo back a bounded preview only — never the full raw input, which
        # could be far larger than any real VIN (see normalize_vin's own cap).
        preview = (input.vin or "").strip().upper()[:64]
        return FormatValidationResult(
            valid=False,
            normalized_vin=preview,
            error=exc.code,
            detail=exc.detail,
        )

    return FormatValidationResult(valid=True, normalized_vin=normalized, error="", detail="")
