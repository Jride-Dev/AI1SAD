# Schema

The initial schema was generated after inspecting `attacks.csv`, which contains the following source columns:

```text
Case Number, Date, Year, Type, Country, Area, Location, Activity, Name,
Sex , Age, Injury, Fatal (Y/N), Time, Species , Investigator or Source,
pdf, href formula, href, Case Number, Case Number, original order, , 
```

The source file includes duplicate `Case Number` columns and blank trailing columns. The public schema intentionally keeps only fields useful for aggregate analysis and removes direct identifiers and restricted-source fields.

## Table: public_incidents

| Column | Type | Description |
| --- | --- | --- |
| `incident_id` | TEXT primary key | Stable SHA-256-derived public ID. |
| `case_number_public` | TEXT | Cleaned public case number when present. |
| `date_text` | TEXT | Original date text, retained because many historical dates are approximate. |
| `year` | INTEGER | Parsed incident year. |
| `incident_type` | TEXT | Source incident type, such as provoked or unprovoked. |
| `country_normalized` | TEXT | Uppercase country label. |
| `area_normalized` | TEXT | State, province, region, or broad area. |
| `location_public` | TEXT | Generalized location with street addresses redacted. |
| `activity_normalized` | TEXT | Lowercase activity label. |
| `sex` | TEXT | Source sex value where available. |
| `age` | TEXT | Source age text where available. |
| `injury_summary` | TEXT | Truncated injury text with simple name redaction. |
| `fatal` | INTEGER | `1` for fatal, `0` otherwise. |
| `time_text` | TEXT | Source time text where available. |
| `species_normalized` | TEXT | Lowercase shark species or description. |

## Indexes

- `idx_public_incidents_year`
- `idx_public_incidents_country`
- `idx_public_incidents_activity`
- `idx_public_incidents_species`

## Excluded Fields

- `Name`
- `Investigator or Source`
- `pdf`
- `href formula`
- `href`
- Private notes
- Exact street addresses
- Restricted-source content

