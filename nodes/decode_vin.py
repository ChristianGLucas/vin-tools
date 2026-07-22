from gen.messages_pb2 import VinInput, VinDecodeResult
from gen.axiom_context import AxiomContext

from nodes._common import (
    normalize_vin,
    build_vin,
    is_manufacturer_known,
    compute_expected_check_digit,
    detail_to_str,
    decode_model_year as _decode_model_year,
    NormalizationError,
)


def decode_vin(ax: AxiomContext, input: VinInput) -> VinDecodeResult:
    """Full decode of one VIN in a single envelope: WMI (manufacturer,
    region, country), the SAE position-9 check digit, the position-10 model
    year (with the position-7 disambiguation rule applied), the Squish
    (Pattern) VIN, and manufacturer-specific body/engine/model/plant/
    transmission/serial when available. Equivalent to calling every other
    node in this package and combining the results.
    """
    try:
        normalized = normalize_vin(input.vin)
        vin_obj = build_vin(normalized)
    except NormalizationError as exc:
        return VinDecodeResult(vin=(input.vin or "").strip().upper()[:64], format_valid=False, error=exc.code, detail=exc.detail)

    known = is_manufacturer_known(vin_obj)
    manufacturer = vin_obj.manufacturer if known else ""

    rule_applies = bool(getattr(vin_obj.assembler, "uses_sae_checkdigit", True))
    actual_check_digit = vin_obj.vds[5] if len(vin_obj.vds) > 5 else ""
    expected_check_digit = compute_expected_check_digit(normalized)

    year_code, candidate_years, most_likely_year, _pos7, year_error = _decode_model_year(vin_obj)

    details = vin_obj.details
    manufacturer_details_supported = bool(details) and any(
        bool(getattr(details, field))
        for field in ("body", "engine", "model", "plant", "transmission", "serial")
    )

    def detail_field(name: str) -> str:
        if not manufacturer_details_supported:
            return ""
        return detail_to_str(getattr(details, name))

    return VinDecodeResult(
        vin=normalized,
        format_valid=True,
        wmi=vin_obj.wmi,
        manufacturer=manufacturer,
        manufacturer_known=known,
        region=vin_obj.region or "",
        country=vin_obj.country or "",
        is_small_volume_manufacturer=vin_obj.manufacturer_is_small,
        vds=vin_obj.vds,
        vis=vin_obj.vis,
        checkdigit_rule_applies=rule_applies,
        checkdigit_valid=(actual_check_digit == expected_check_digit),
        expected_check_digit=expected_check_digit,
        candidate_model_years=candidate_years,
        most_likely_model_year=most_likely_year,
        squish_vin=vin_obj.squish_vin,
        manufacturer_details_supported=manufacturer_details_supported,
        body=detail_field("body"),
        engine=detail_field("engine"),
        model=detail_field("model"),
        plant=detail_field("plant"),
        transmission=detail_field("transmission"),
        serial=detail_field("serial"),
        error="",
        detail=(year_error or ""),
    )
