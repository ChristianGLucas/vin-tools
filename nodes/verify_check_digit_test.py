from gen.messages_pb2 import VinInput
from nodes.verify_check_digit import verify_check_digit
from nodes._test_helpers import FakeAxiomContext


def _hand_computed_check_digit(vin: str) -> str:
    """Independent, from-scratch re-implementation of the SAE J853 check
    digit algorithm, written directly in this test (not importing the
    node's own table) — the "second independent implementation" oracle.
    Values transcribed straight from Wikipedia's worked example.
    """
    transliteration = {
        "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
        "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
        "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
    }
    weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(
        (transliteration[c] if c in transliteration else int(c)) * w
        for c, w in zip(vin, weights)
    )
    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def test_wikipedia_worked_example_matches_hand_computation():
    # Wikipedia's VIN article works this exact example by hand: the 17
    # transliterated/weighted products sum to 351; 351 mod 11 == 10, so the
    # check digit is "X". This is a real, independent oracle, not a
    # round-trip through the node's own implementation.
    vin = "1M8GDM9AXKP042788"
    assert _hand_computed_check_digit(vin) == "X"

    ax = FakeAxiomContext()
    result = verify_check_digit(ax, VinInput(vin=vin))
    assert result.rule_applies is True
    assert result.actual_check_digit == "X"
    assert result.expected_check_digit == "X"
    assert result.valid is True


def test_documented_invalid_check_digit_porsche_vin():
    # Wikipedia's VIN article explicitly notes this VIN "does not pass the
    # North American check-digit verification" — a documented negative case.
    vin = "WP0ZZZ99ZTS392124"
    ax = FakeAxiomContext()
    result = verify_check_digit(ax, VinInput(vin=vin))
    assert result.rule_applies is True
    assert result.actual_check_digit == "Z"
    assert result.expected_check_digit == _hand_computed_check_digit(vin)
    assert result.expected_check_digit != "Z"
    assert result.valid is False


def test_ford_australia_check_digit_rule_does_not_apply():
    # Ford Australia's VIS position 9 is a model code, not an SAE check
    # digit (vininfo.brands.FordAustralia.uses_sae_checkdigit = False). WMI
    # "6FP" is Ford Australia's own reference-data entry.
    ax = FakeAxiomContext()
    result = verify_check_digit(ax, VinInput(vin="6FPBSER1DBGD01234"))
    assert result.rule_applies is False


def test_malformed_input_returns_structured_error_not_crash():
    ax = FakeAxiomContext()
    result = verify_check_digit(ax, VinInput(vin="too-short"))
    assert result.error == "WRONG_LENGTH"
    assert result.valid is False
    assert result.actual_check_digit == ""
