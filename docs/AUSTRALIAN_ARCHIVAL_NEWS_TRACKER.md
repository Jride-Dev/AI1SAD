# Australian Archival News Tracker

This planning page defines a future archival evidence lane for Australian newspaper and public-record research. It supports the planned AI1SAD Shark-Human Incident Registry by tracking source metadata, citations, uncertainty, duplicate publication paths, and review state before any incident-registry promotion.

This is planning documentation only. Phase 26C has not started.

Target full working-version launch remains September 7, 2026.

## Scope

The archival news tracker will capture source metadata before full text. AI1SAD will treat archival articles and public-record references as source evidence, not final truth.

The tracker must not:

- scrape Trove or other archive pages
- use the Trove API before terms, quotas, and rights rules are reviewed
- bulk-download article bodies
- reproduce copyrighted article text in public outputs
- create warnings, alerts, replay facts, scoring changes, or public feed entries
- assign confirmed shark intent

## Source Targets

Initial source targets include:

- Trove / National Library of Australia
- State Library of Queensland
- State Library of New South Wales
- State Library Victoria
- State Library of Western Australia
- State Library of South Australia
- National Archives of Australia
- Australian local newspapers and regional archives
- surf lifesaving club histories
- coroner/inquest references where legally accessible
- government fisheries / shark control reports
- historical court/inquest reporting
- maritime accident archives

## Planned Metadata Fields

The first implementation should capture metadata and review state:

- `archival_source_id`
- `source_platform`
- `archive_collection`
- `newspaper_title`
- `publication_date`
- `article_title`
- `article_url`
- `trove_article_id`
- `page_url`
- `page_number`
- `jurisdiction`
- `location_mentioned`
- `shark_attack_case_candidate`
- `people_mentioned`
- `species_mentioned_raw`
- `incident_date_raw`
- `incident_date_normalized`
- `source_text_excerpt_allowed`
- `copyright_status`
- `rights_note`
- `access_note`
- `citation`
- `extraction_status`
- `review_status`
- `linked_ai1sad_case_id`
- `source_confidence`
- `notes_private`

## Capture Rules

- Store metadata and citations first.
- Do not bulk-download full article bodies unless rights and API terms are confirmed.
- Do not reproduce copyrighted articles in public outputs.
- Preserve OCR uncertainty and include an explicit review status for OCR-derived claims.
- Preserve old terminology as raw text, but normalize carefully in separate reviewed fields.
- Treat archival articles as source evidence, not final truth.
- Link multiple articles to the same incident when possible.
- Detect reprints, syndication, duplicates, later retellings, and retrospective anniversary pieces.
- Track conflicting claims instead of flattening them into a single narrative.

## Confidence And Review

Archival articles can be valuable, but they vary widely in reliability. A future tracker should score source confidence separately from incident confidence and behavioral hypothesis confidence.

Suggested review states:

- `unreviewed`
- `metadata_captured`
- `ocr_needs_review`
- `citation_verified`
- `case_link_candidate`
- `case_link_confirmed`
- `duplicate_or_reprint`
- `rights_review_required`
- `rejected`

Suggested source confidence values:

- `unreviewed`
- `weak`
- `plausible`
- `corroborated`
- `conflicting`
- `contradicted`

## Behavioral Hypothesis Link

Archival news sources may inform future AI1SAD behavioral hypotheses:

- `attempted_predation_event`
- `predatory_probe`
- `territorial_displacement`
- `competitive_food_response`
- `scavenging_context`
- `accidental_contact`
- `mistaken_identity_candidate`
- `unknown_insufficient_evidence`

They must not automatically assign shark intent. AI1SAD does not default to mistaken identity. It treats mistaken identity as one possible hypothesis among competing behavioral explanations.

## Rights And Public Output

Public AI1SAD outputs should use citations, safe metadata, and short rights-reviewed excerpts only where allowed. Full article text, OCR dumps, private notes, and unreviewed claims should remain local/private until terms and rights are confirmed.

## Phase 26B And 26C Handoff

Phase 26B should define the incident registry schema that these archival sources can link to. Phase 26C can then implement the Australian Archival Newspaper Source Tracker as a local/manual metadata capture workflow.
