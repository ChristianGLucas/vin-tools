from gen.messages_pb2 import VinInput, ManufacturerDetailsResult
from gen.axiom_context import AxiomContext

from nodes._common import normalize_vin, build_vin, is_manufacturer_known, detail_to_str, NormalizationError


def decode_manufacturer_details(ax: AxiomContext, input: VinInput) -> ManufacturerDetailsResult:
    """Decode manufacturer-specific body/engine/model/plant/transmission/
    serial from the VDS and VIS. Only a handful of manufacturers have a
    dedicated decoder available (currently: Lada/AvtoVAZ, Nissan, Opel,
    Renault, Dafra, Bajaj, and Ford Australia) — `supported=false` for every
    other VIN is expected, not an error.
    """
    try:
        normalized = normalize_vin(input.vin)
        vin_obj = build_vin(normalized)
    except NormalizationError as exc:
        return ManufacturerDetailsResult(error=exc.code)

    details = vin_obj.details
    supported = bool(details) and any(
        bool(getattr(details, field))
        for field in ("body", "engine", "model", "plant", "transmission", "serial")
    )

    if not supported:
        manufacturer = vin_obj.manufacturer if is_manufacturer_known(vin_obj) else ""
        return ManufacturerDetailsResult(supported=False, manufacturer=manufacturer, error="")

    def field(name: str) -> str:
        return detail_to_str(getattr(details, name))

    return ManufacturerDetailsResult(
        supported=True,
        manufacturer=vin_obj.manufacturer,
        body=field("body"),
        engine=field("engine"),
        model=field("model"),
        plant=field("plant"),
        transmission=field("transmission"),
        serial=field("serial"),
        error="",
    )
