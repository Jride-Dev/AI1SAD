# Species Season Profiles

Species season profiles describe region-specific seasonal context for warning and surveillance scoring.

They are not individual animal predictions. They are planning metadata used to explain whether a season, region, and species context should increase attention.

## Collections

- `species_season_profiles`: active and peak months, public regional notes, and risk-context factors.
- `migration_windows`: coarse public migration or movement windows by region and species.
- `prey_presence_zones`: public prey/baitfish/pinniped/forage signals where available.

## Example

```json
{
  "visibility": "public",
  "region": "Florida",
  "species": "bull shark",
  "active_months": [5, 6, 7, 8, 9],
  "peak_months": [8, 9],
  "risk_factors": ["river mouth", "runoff", "low visibility"]
}
```

## Rules

- Do not use one global summer definition.
- Keep seasonal context regional and species-aware.
- Treat migration windows as uncertain unless backed by official or reviewed sources.
- Do not infer intent from species presence.
- Keep restricted ecological or tracking data private unless it is cleared for public use.
