from gen.messages_pb2 import VinInput
from nodes.squish_vin import squish_vin
from nodes._test_helpers import FakeAxiomContext


def _hand_rolled_squish(vin: str) -> str:
    """Independent, from-scratch computation of the Squish VIN definition
    (positions 1-8 + 10-11), written directly in this test."""
    return vin[:8] + vin[9:11]


def test_squish_vin_matches_hand_rolled_definition():
    vin = "1M8GDM9AXKP042788"
    expected = _hand_rolled_squish(vin)
    assert expected == "1M8GDM9AKP"

    ax = FakeAxiomContext()
    result = squish_vin(ax, VinInput(vin=vin))
    assert result.squish_vin == expected
    assert result.error == ""


def test_squish_vin_omits_check_digit_and_serial():
    vin = "1N4AL11D75C109151"
    ax = FakeAxiomContext()
    result = squish_vin(ax, VinInput(vin=vin))
    assert result.squish_vin == _hand_rolled_squish(vin)
    # Position 9 (the check digit, vin[8] == '7') must not appear at the
    # position-9 slot of the squish VIN, and the 6-digit serial tail
    # (vin[11:] == "109151") must be entirely absent.
    assert result.squish_vin == "1N4AL11D5C"
    assert "109151" not in result.squish_vin


def test_malformed_input_returns_structured_error_not_crash():
    ax = FakeAxiomContext()
    result = squish_vin(ax, VinInput(vin=""))
    assert result.error == "EMPTY"
    assert result.squish_vin == ""
