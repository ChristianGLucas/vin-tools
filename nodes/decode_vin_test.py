from gen.messages_pb2 import VinInput
from nodes.decode_vin import decode_vin
from nodes._test_helpers import FakeAxiomContext


def test_full_decode_wikipedia_worked_example():
    # Cross-checks the comprehensive node against the same independently
    # verified facts used across this package's other node tests: the
    # Wikipedia worked check-digit example (351 mod 11 == 10 -> 'X'), the
    # ISO 3780 WMI/region/country tables, and the position-7 model-year
    # disambiguation rule.
    ax = FakeAxiomContext()
    result = decode_vin(ax, VinInput(vin="  1m8gdm9axkp042788  "))

    assert result.format_valid is True
    assert result.vin == "1M8GDM9AXKP042788"
    assert result.wmi == "1M8"
    assert result.region == "North America"
    assert result.country == "United States"
    assert result.vds == "GDM9AX"
    assert result.vis == "KP042788"

    assert result.checkdigit_rule_applies is True
    assert result.expected_check_digit == "X"
    assert result.checkdigit_valid is True

    assert 1989 in result.candidate_model_years
    assert 2019 in result.candidate_model_years
    assert result.most_likely_model_year == 1989

    assert result.squish_vin == "1M8GDM9AKP"
    assert result.error == ""


def test_full_decode_matches_single_purpose_nodes_for_nissan_vin():
    # The combined envelope must agree with the equivalent single-purpose
    # nodes for the same input (internal consistency across the package).
    from nodes.decode_wmi import decode_wmi
    from nodes.verify_check_digit import verify_check_digit
    from nodes.decode_manufacturer_details import decode_manufacturer_details

    vin = "1N4AL11D75C109151"
    ax = FakeAxiomContext()

    combined = decode_vin(ax, VinInput(vin=vin))
    wmi = decode_wmi(ax, VinInput(vin=vin))
    checkdigit = verify_check_digit(ax, VinInput(vin=vin))
    details = decode_manufacturer_details(ax, VinInput(vin=vin))

    assert combined.manufacturer == wmi.manufacturer
    assert combined.country == wmi.country
    assert combined.checkdigit_valid == checkdigit.valid
    assert combined.expected_check_digit == checkdigit.expected_check_digit
    assert combined.plant == details.plant
    assert combined.serial == details.serial
    # Regression: the ambiguous list-valued body detail must not crash the
    # combined node either (see decode_manufacturer_details_test.py).
    assert combined.body == details.body


def test_invalid_vin_returns_structured_error_with_zeroed_fields():
    ax = FakeAxiomContext()
    result = decode_vin(ax, VinInput(vin="not-a-real-vin-at-all"))
    assert result.format_valid is False
    assert result.error != ""
    assert result.manufacturer == ""
    assert result.checkdigit_valid is False
    assert list(result.candidate_model_years) == []
