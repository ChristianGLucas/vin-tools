from gen.messages_pb2 import VinInput
from nodes.validate_vin_format import validate_vin_format
from nodes._test_helpers import FakeAxiomContext


def test_valid_vin_wikipedia_worked_example():
    # ISO 3779 worked example from Wikipedia's VIN article.
    ax = FakeAxiomContext()
    result = validate_vin_format(ax, VinInput(vin="1M8GDM9AXKP042788"))
    assert result.valid is True
    assert result.normalized_vin == "1M8GDM9AXKP042788"
    assert result.error == ""


def test_trims_and_uppercases():
    ax = FakeAxiomContext()
    result = validate_vin_format(ax, VinInput(vin="  1m8gdm9axkp042788  "))
    assert result.valid is True
    assert result.normalized_vin == "1M8GDM9AXKP042788"


def test_wrong_length_rejected():
    ax = FakeAxiomContext()
    result = validate_vin_format(ax, VinInput(vin="1M8GDM9AXKP04278"))  # 16 chars
    assert result.valid is False
    assert result.error == "WRONG_LENGTH"


def test_empty_input_rejected():
    ax = FakeAxiomContext()
    result = validate_vin_format(ax, VinInput(vin=""))
    assert result.valid is False
    assert result.error == "EMPTY"


def test_excluded_letters_i_o_q_rejected():
    # I, O, Q are never valid VIN characters per ISO 3779 (avoids confusion
    # with 1 and 0). Swap position 1 of a valid VIN with each in turn.
    ax = FakeAxiomContext()
    for bad_letter in ("I", "O", "Q"):
        vin = bad_letter + "M8GDM9AXKP042788"
        result = validate_vin_format(ax, VinInput(vin=vin))
        assert result.valid is False, f"expected {bad_letter!r} to be rejected"
        assert result.error == "INVALID_CHARACTERS"
        assert bad_letter in result.detail


def test_absurdly_long_input_rejected_not_crash():
    # Cost-bound: an oversized payload must be rejected cheaply, never
    # processed as if it might be a VIN, and never crash.
    ax = FakeAxiomContext()
    result = validate_vin_format(ax, VinInput(vin="A" * 5000))
    assert result.valid is False
    assert result.error == "WRONG_LENGTH"
    # The echoed preview must be bounded, not the full 5000-char input.
    assert len(result.normalized_vin) <= 64
