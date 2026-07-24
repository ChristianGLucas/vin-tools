# vin-tools

Composable [Axiom](https://axiomide.com) nodes for decoding Vehicle Identification
Numbers (VINs) per **ISO 3779/3780** and **SAE J853**. Built for the Axiom
marketplace under the `christiangeorgelucas` handle.

Wraps [vininfo](https://github.com/idlesign/vininfo) (BSD-3-Clause), which
owns the WMI reference table, country/region tables, and manufacturer-specific
detail extractors. The SAE J853 position-9 check-digit algorithm and the
NHTSA/SAE position-7 model-year disambiguation rule are additionally
implemented from scratch against the public standard, so this package doesn't
depend on vininfo for either.

## Use it from your agent or app

Every node in this package is a **live, auto-scaling API endpoint** on the
[Axiom](https://axiomide.com) marketplace — call it from an AI agent or your own
code, with nothing to self-host.

**📦 See it on the marketplace:**
https://dev.axiomide.com/marketplace/christiangeorgelucas/vin-tools@0.1.1

**Hook it up to an AI agent (MCP).** Add Axiom's hosted MCP server to any MCP
client and every node becomes a typed tool your agent can call — search the
catalog, inspect a schema, and invoke it directly.

```bash
# Claude Code
claude mcp add --transport http axiom https://api.axiomide.com/mcp \
  --header "Authorization: Bearer $AXIOM_API_KEY"
```

Claude Desktop, Cursor, or any config-based client:

```json
{
  "mcpServers": {
    "axiom": {
      "type": "http",
      "url": "https://api.axiomide.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_AXIOM_API_KEY" }
    }
  }
}
```

**Call it from the CLI.**

```bash
axiom invoke christiangeorgelucas/vin-tools/ValidateVinFormat --input '{ ... }'
```

**Call it over HTTP.**

```bash
curl -X POST https://api.axiomide.com/invocations/v1/nodes/christiangeorgelucas/vin-tools/0.1.1/ValidateVinFormat \
  -H "Authorization: Bearer $AXIOM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

> Input/output schema for each node is on the marketplace page above, or via
> `axiom inspect node christiangeorgelucas/vin-tools/ValidateVinFormat`.

### Get started free

Install the CLI:

```bash
# macOS / Linux — Homebrew
brew install axiomide/tap/axiom

# macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/AxiomIDE/axiom-releases/main/install.sh | sh
```

**Windows:** download the `windows/amd64` `.zip` from the
[releases page](https://github.com/AxiomIDE/axiom-releases/releases), unzip it,
and put `axiom.exe` on your `PATH`.

Then `axiom version` to verify, `axiom login` (GitHub or Google) to authenticate,
and create an API key under **Console → API Keys**. Docs and sign-up at
**[axiomide.com](https://axiomide.com)**.

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
