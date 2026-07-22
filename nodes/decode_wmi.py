from gen.messages_pb2 import VinInput, WmiResult
from gen.axiom_context import AxiomContext

from nodes._common import normalize_vin, build_vin, is_manufacturer_known, NormalizationError


def decode_wmi(ax: AxiomContext, input: VinInput) -> WmiResult:
    """Decode the WMI (World Manufacturer Identifier, VIN positions 1-3) per
    ISO 3780: manufacturer, region, and country of origin, plus whether the
    3rd character marks a low-volume manufacturer (fewer than 1000
    vehicles/year).
    """
    try:
        normalized = normalize_vin(input.vin)
        vin_obj = build_vin(normalized)
    except NormalizationError as exc:
        return WmiResult(error=exc.code)

    known = is_manufacturer_known(vin_obj)
    manufacturer = vin_obj.manufacturer if known else ""

    return WmiResult(
        wmi=vin_obj.wmi,
        manufacturer=manufacturer,
        region=vin_obj.region or "",
        country=vin_obj.country or "",
        is_small_volume_manufacturer=vin_obj.manufacturer_is_small,
        manufacturer_known=known,
        error="",
    )
