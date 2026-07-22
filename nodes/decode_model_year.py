from gen.messages_pb2 import VinInput, ModelYearResult
from gen.axiom_context import AxiomContext

from nodes._common import normalize_vin, build_vin, decode_model_year as _decode_model_year, NormalizationError


def decode_model_year(ax: AxiomContext, input: VinInput) -> ModelYearResult:
    """Decode the VIN position-10 model-year code and disambiguate it using
    the NHTSA/SAE position-7 rule (49 CFR 565.16, note to Table VII): a
    numeric position-7 character means the position-10 code refers to the
    1980-2009 cycle, an alphabetic one means 2010-2039. Both the raw
    candidate set (every year the 30-year-cycle code alone is consistent
    with) and the disambiguated single most-likely year are returned.
    """
    try:
        normalized = normalize_vin(input.vin)
        vin_obj = build_vin(normalized)
    except NormalizationError as exc:
        return ModelYearResult(error=exc.code)

    year_code, candidates, most_likely, pos7, error = _decode_model_year(vin_obj)

    return ModelYearResult(
        year_code=year_code,
        candidate_years=candidates,
        most_likely_year=most_likely,
        position_7_character=pos7,
        error=error,
    )
