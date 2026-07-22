from gen.messages_pb2 import VinInput
from nodes.decode_model_year import decode_model_year
from nodes._test_helpers import FakeAxiomContext


def _hand_rolled_candidate_years(year_code: str, current_year: int = 2026) -> list:
    """Independent, from-scratch re-implementation of the ISO 3779 30-year
    repeating model-year cycle, written directly in this test."""
    letters = "ABCDEFGHJKLMNPRSTVWXY123456789"
    idx = letters.index(year_code)
    years = []
    year = 1980 + idx
    while year <= current_year + 1:
        years.append(year)
        year += 30
    return sorted(years, reverse=True)


def test_wikipedia_example_disambiguated_to_1989():
    # VIN "1M8GDM9AXKP042788": position 10 = 'K', position 7 = '9'
    # (numeric) -> per the NHTSA/SAE position-7 rule (49 CFR 565.16), the
    # 1980-2009 cycle applies, so 'K' must mean 1989, not 2019.
    ax = FakeAxiomContext()
    result = decode_model_year(ax, VinInput(vin="1M8GDM9AXKP042788"))
    assert result.year_code == "K"
    assert result.position_7_character == "9"
    assert list(result.candidate_years) == _hand_rolled_candidate_years("K")
    assert 1989 in result.candidate_years
    assert 2019 in result.candidate_years
    assert result.most_likely_year == 1989


def test_alphabetic_position_7_selects_2010_plus_cycle():
    # Construct a VIN whose position 7 is a LETTER (not a digit): the rule
    # should then select the 2010-2039 candidate over the 1980-2009 one for
    # the same position-10 code 'K'.
    # VIN: 1 M 8 G D M A A X K P 0 4 2 7 8 8  (position7 = 'A', alphabetic)
    ax = FakeAxiomContext()
    result = decode_model_year(ax, VinInput(vin="1M8GDMAAXKP042788"))
    assert result.position_7_character == "A"
    assert result.year_code == "K"
    assert result.most_likely_year == 2019


def test_position_7_is_true_vin_position_not_vis_position():
    # Regression: position 7 must be read from the full 17-char VIN (index
    # 6), never from an offset into the VIS substring (which starts at
    # overall position 10) — an earlier version of this node had that bug.
    ax = FakeAxiomContext()
    result = decode_model_year(ax, VinInput(vin="1N4AL11D75C109151"))
    normalized = "1N4AL11D75C109151"
    assert result.position_7_character == normalized[6]


def test_malformed_input_returns_structured_error_not_crash():
    ax = FakeAxiomContext()
    result = decode_model_year(ax, VinInput(vin="short"))
    assert result.error == "WRONG_LENGTH"
    assert result.most_likely_year == 0
    assert list(result.candidate_years) == []
