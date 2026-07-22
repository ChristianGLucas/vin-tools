from gen.messages_pb2 import VinInput, CheckDigitResult
from gen.axiom_context import AxiomContext

from nodes._common import normalize_vin, build_vin, compute_expected_check_digit, NormalizationError


def verify_check_digit(ax: AxiomContext, input: VinInput) -> CheckDigitResult:
    """Verify the SAE J853 / ISO 3779 position-9 check digit: transliterate
    every character to a digit, take a weighted sum, then modulus 11 (a
    remainder of 10 is written as the letter X). Not every manufacturer or
    market follows this convention (notably Ford Australia, and VINs outside
    the North American market generally) — `rule_applies` reports whether
    this VIN's manufacturer is known to.
    """
    try:
        normalized = normalize_vin(input.vin)
        vin_obj = build_vin(normalized)
    except NormalizationError as exc:
        return CheckDigitResult(error=exc.code)

    rule_applies = bool(getattr(vin_obj.assembler, "uses_sae_checkdigit", True))
    actual = vin_obj.vds[5] if len(vin_obj.vds) > 5 else ""
    expected = compute_expected_check_digit(normalized)

    return CheckDigitResult(
        rule_applies=rule_applies,
        actual_check_digit=actual,
        expected_check_digit=expected,
        valid=(actual == expected),
        error="",
    )
