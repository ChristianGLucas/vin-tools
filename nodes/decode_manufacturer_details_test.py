from gen.messages_pb2 import VinInput
from nodes.decode_manufacturer_details import decode_manufacturer_details
from nodes._test_helpers import FakeAxiomContext


def test_nissan_plant_and_serial_decoded():
    # VIN "1N4AL11D75C109151": WMI 1N4 resolves to Nissan (a manufacturer
    # with a dedicated decoder). vininfo's own NissanDetails table (read
    # directly from source: plant = Detail(('vis', 1), {'C': 'Smyrna', ...})
    # and serial = Detail(('vis', slice(2, None)))) says VIS index 1 ('C')
    # -> plant "Smyrna", and the VIS tail is the serial. These expected
    # values are hand-transcribed from the library's own reference table,
    # not re-derived by calling the code under test.
    ax = FakeAxiomContext()
    result = decode_manufacturer_details(ax, VinInput(vin="1N4AL11D75C109151"))
    assert result.supported is True
    assert result.manufacturer == "Nissan"
    assert result.plant == "Smyrna"
    assert result.serial == "109151"
    assert result.error == ""


def test_ambiguous_multi_candidate_detail_does_not_crash():
    # Regression: some Nissan body/engine codes map to a LIST of candidate
    # names in vininfo's table (e.g. VDS index 3 == '1' -> body is
    # ['Sedan, 4-Door', 'Standard Body Truck']). vininfo's own
    # DetailWrapper.__str__ raises TypeError on this ("__str__ returned
    # non-string (type list)") — a real crash on a realistic VIN. This node
    # must instead join the candidates into one readable string.
    ax = FakeAxiomContext()
    result = decode_manufacturer_details(ax, VinInput(vin="1N4AL11D75C109151"))
    assert "Sedan, 4-Door" in result.body
    assert "/" in result.body  # joined, not a crash and not a single guess


def test_unsupported_manufacturer_reports_false_not_error():
    # Porsche (WP0) has no manufacturer-specific decoder in vininfo —
    # supported=false is the correct, expected result, not an error.
    ax = FakeAxiomContext()
    result = decode_manufacturer_details(ax, VinInput(vin="WP0ZZZ99ZTS392124"))
    assert result.supported is False
    assert result.body == ""
    assert result.error == ""


def test_malformed_input_returns_structured_error_not_crash():
    ax = FakeAxiomContext()
    result = decode_manufacturer_details(ax, VinInput(vin="bad"))
    assert result.error == "WRONG_LENGTH"
    assert result.supported is False
