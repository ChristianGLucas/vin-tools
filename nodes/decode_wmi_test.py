from gen.messages_pb2 import VinInput
from nodes.decode_wmi import decode_wmi
from nodes._test_helpers import FakeAxiomContext


def test_porsche_wmi_documented_public_fact():
    # WP0 = Porsche, Germany, Europe — an undisputed, widely-documented WMI
    # fact (independent of vininfo's own reference data; used as the actual
    # example VIN in Wikipedia's VIN article).
    ax = FakeAxiomContext()
    result = decode_wmi(ax, VinInput(vin="WP0ZZZ99ZTS392124"))
    assert result.wmi == "WP0"
    assert "Porsche" in result.manufacturer
    assert result.country == "Germany"
    assert result.region == "Europe"
    assert result.manufacturer_known is True
    assert result.error == ""


def test_nissan_wmi_documented_public_fact():
    # 1N4 = Nissan, USA-built, North America — likewise a well-documented,
    # independently verifiable WMI assignment.
    ax = FakeAxiomContext()
    result = decode_wmi(ax, VinInput(vin="1N4AL11D75C109151"))
    assert result.wmi == "1N4"
    assert "Nissan" in result.manufacturer
    assert result.country == "United States"
    assert result.region == "North America"
    assert result.manufacturer_known is True


def test_unknown_wmi_reports_not_known_rather_than_a_guess():
    # "ZZ9" is not a real assigned WMI. The node must say so explicitly
    # rather than surfacing vininfo's internal "UnsupportedBrand" fallback
    # class name as if it were a real manufacturer.
    ax = FakeAxiomContext()
    result = decode_wmi(ax, VinInput(vin="ZZ9AA000000000001"))
    assert result.manufacturer_known is False
    assert result.manufacturer == ""
    assert "UnsupportedBrand" not in result.manufacturer


def test_small_volume_manufacturer_flag_is_structural():
    # ISO 3780: a "9" as the WMI's 3rd character marks a low-volume
    # manufacturer (<1000 vehicles/year) — this is derived purely from the
    # VIN's own characters, independent of whether the specific WMI is in
    # the reference database.
    ax = FakeAxiomContext()
    result = decode_wmi(ax, VinInput(vin="ZZ9AA000000000001"))
    assert result.is_small_volume_manufacturer is True

    ax2 = FakeAxiomContext()
    result2 = decode_wmi(ax2, VinInput(vin="1N4AL11D75C109151"))
    assert result2.is_small_volume_manufacturer is False


def test_malformed_input_returns_structured_error_not_crash():
    ax = FakeAxiomContext()
    result = decode_wmi(ax, VinInput(vin="not a vin"))
    assert result.error != ""
    assert result.manufacturer == ""
