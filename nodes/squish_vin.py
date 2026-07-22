from gen.messages_pb2 import VinInput, SquishVinResult
from gen.axiom_context import AxiomContext

from nodes._common import normalize_vin, build_vin, NormalizationError


def squish_vin(ax: AxiomContext, input: VinInput) -> SquishVinResult:
    """Produce the Squish (Pattern) VIN: positions 1-8 plus 10-11, omitting
    the position-9 check digit and the position-12-17 sequential serial.
    Groups vehicles of the same make/model/year/plant while dropping the
    individually-identifying tail — useful for anonymized aggregation.
    """
    try:
        normalized = normalize_vin(input.vin)
        vin_obj = build_vin(normalized)
    except NormalizationError as exc:
        return SquishVinResult(error=exc.code)

    return SquishVinResult(squish_vin=vin_obj.squish_vin, error="")
