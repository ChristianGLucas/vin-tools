# vin-tools

Composable [Axiom](https://axiom.ai) nodes for decoding Vehicle Identification
Numbers (VINs) per **ISO 3779/3780** and **SAE J853**. Built for the Axiom
marketplace under the `christiangeorgelucas` handle.

Wraps [vininfo](https://github.com/idlesign/vininfo) (BSD-3-Clause), which
owns the WMI reference table, country/region tables, and manufacturer-specific
detail extractors. The SAE J853 position-9 check-digit algorithm and the
NHTSA/SAE position-7 model-year disambiguation rule are additionally
implemented from scratch against the public standard, so this package doesn't
depend on vininfo for either.

## Nodes

- **ValidateVinFormat** — structural validation (17 chars, excludes I/O/Q).
- **VerifyCheckDigit** — SAE J853 / ISO 3779 position-9 check digit.
- **DecodeWmi** — World Manufacturer Identifier → manufacturer/region/country.
- **DecodeModelYear** — position-10 model year, disambiguated via the
  NHTSA/SAE position-7 rule (49 CFR 565.16).
- **DecodeManufacturerDetails** — manufacturer-specific body/engine/model/
  plant/transmission/serial (Lada/AvtoVAZ, Nissan, Opel, Renault, Dafra,
  Bajaj, Ford Australia).
- **SquishVin** — Squish (Pattern) VIN for anonymized aggregation.
- **DecodeVin** — the full decode in a single envelope.

Every node is stateless, deterministic, and fully offline. Malformed or
oversized input returns a structured error, never a crash.

## License

MIT © 2026 Christian George Lucas
