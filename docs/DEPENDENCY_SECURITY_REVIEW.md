# Dependency Security Review

Latest review date: 2026-06-21

## 2026-06-21 Vite Windows Dev Server Alerts

Scope: two open GitHub Dependabot alerts reported against `frontend/package-lock.json` for the direct `vite` dependency.

| Alert | Package | Severity | GHSA | CVE | Old Version | New Version | Dependency Path | Runtime Exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dependabot #5 | `vite` | high | `GHSA-fx2h-pf6j-xcff` | `CVE-2026-53571` | `7.3.3` | `7.3.5` | `frontend/package-lock.json` -> `vite` | Vite development server on Windows; production build output is not the affected server |
| Dependabot #6 | `vite` / advisory path includes `launch-editor` | medium | `GHSA-v6wh-96g9-6wx3` | `CVE-2026-53632` | `7.3.3` | `7.3.5` | `frontend/package-lock.json` -> `vite` | Vite development server/editor-open middleware on Windows; `launch-editor` is not installed as a separate dependency after the patch |

Patch applied:

```text
cd frontend
npm install vite@7.3.5 --save-dev
```

No `npm audit fix --force` command was used. No React, Vitest, application code, replay output, or scoring logic was changed.

Reason for targeted update:

- `vite 7.3.5` is the first patched Vite 7.x version for both reported advisories.
- The high alert covers Windows alternate path handling in the dev server file-deny checks, which can expose denied files such as local environment files when a Vite dev server is reachable.
- The medium alert covers Windows UNC path handling through editor-open behavior, which can trigger NTLM authentication to an attacker-controlled SMB target if a malicious request reaches the local dev server.
- Updating Vite within the same minor line keeps the change narrow and avoids unrelated major dependency churn.

Post-patch resolution:

```text
vite 7.3.5
launch-editor: not present in npm dependency tree
```

Post-patch audit:

```text
npm audit --audit-level=high
0 high or critical vulnerabilities; command exited 0
1 low @babel/core advisory remains outside this Vite-alert scope
```

Validation run for this patch:

- Frontend dependency tree: `npm ls vite` resolved all Vite entries to `7.3.5`
- `npm ls launch-editor`: empty tree; no separate `launch-editor` override required
- Frontend tests: `5` test files passed, `30` tests passed
- Frontend build: passed with Vite `7.3.5`
- Frontend audit high: passed with `0` high or critical vulnerabilities; one low `@babel/core` advisory remains unrelated to the two Vite alerts
- Backend tests:
  - `python -m pytest -q` with system Python 3.14 failed during collection because `pymongo` was not installed in that interpreter
  - `F:\Python310\python.exe -m pytest -q` ran the suite and reported `282 passed, 1 failed, 3 warnings`
  - Failing test: `tests/test_biological_events_provider.py::test_lovers_point_carcass_warning_is_bounded`
  - The backend failure appears unrelated to the frontend Vite dependency patch and was not changed because doing so would expand this maintenance task into provider/replay/scoring behavior
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- README local links/images check: `54` checked, passed
- Secret scan on changed files: no credential matches
- Prohibited-language scan on changed files: no matches
- Git whitespace check: passed with CRLF normalization warnings only

Dependabot confirmation:

- Local audit confirms the Vite high/medium advisories are remediated by `vite 7.3.5`.
- GitHub Dependabot API was checked before commit/push and still reported alerts #5 and #6 open on the remote default branch, as expected because the local patch had not been pushed.
- Recheck Dependabot after the patch is committed and pushed.

Remaining known security item:

- `npm audit --audit-level=low` reports one low `@babel/core` advisory. It is outside the requested Vite-alert scope and was not patched in this targeted maintenance pass.

## 2026-06-15 Esbuild Alerts

Scope: two open GitHub Dependabot alerts reported on the default branch after the Coogee replay commit.

| Alert | Package | Severity | Vulnerable Version | Patched Version | Dependency Path | Scope | Relationship | Runtime Exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dependabot #4 / `GHSA-gv7w-rqvm-qjhr` | `esbuild` | high | `0.27.7` | `0.28.1` | `frontend/package-lock.json` -> `vite` -> `esbuild` | npm runtime scope in manifest metadata | transitive | Build/dev-server tooling; not shipped in the built React bundle |
| Dependabot #3 / `GHSA-g7r4-m6w7-qqqr` | `esbuild` | low | `0.27.7` | `0.28.1` | `frontend/package-lock.json` -> `vite` -> `esbuild` | npm runtime scope in manifest metadata | transitive | Vite development server on Windows; not shipped in the built React bundle |

Patch applied:

```text
frontend/package.json overrides.esbuild = ^0.28.1
npm install
```

Reason for targeted override:

- The patched `esbuild` version is `0.28.1`.
- The current Vite 7.x line still declares `esbuild ^0.27.0`.
- `npm audit fix --force` would move Vite to 8.x, a breaking major upgrade.
- The override updates only the vulnerable transitive `esbuild` package and its platform packages while keeping Vite at `7.3.3` and Vitest at `4.1.8`.

Post-patch resolution:

```text
vite 7.3.3
esbuild 0.28.1
vitest 4.1.8
```

Post-patch audit:

```text
npm audit --audit-level=low
found 0 vulnerabilities
```

Validation run for this patch:

- Frontend tests: `3 passed`, `8 tests passed`
- Frontend build: passed with Vite `7.3.3`
- Frontend audit: `npm audit --audit-level=high` reported `0 vulnerabilities`
- Backend tests: `255 passed, 3 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- Secret scan: no credential values; documentation phrases and `js-tokens` package names only
- Prohibited-language scan: guardrail-only matches in `PROJECT_STATUS.md`

Recommendation: safe patch now. Monitor the Vite 7.x line for a native `esbuild >=0.28.1` dependency range, then remove the override during a normal dependency-maintenance pass.

## 2026-06-03 Vitest Alerts

Scope: two open GitHub Dependabot critical alerts reported after the latest push. The first review documented the issue without changing dependencies. The follow-up patch applied a targeted Vitest-only upgrade.

## Executive Summary

Both open critical Dependabot alerts point to the same vulnerable package and advisory:

- Package: `vitest`
- Advisory: `GHSA-5xrq-8626-4rwp` / `CVE-2026-47429`
- Severity: critical
- Affected range: `<4.1.0`
- Patched range: `>=4.1.0`
- Pre-upgrade project version: `vitest@3.2.4`
- Target and installed patched version: `vitest@4.1.8`

Dependabot shows two alerts because it tracks the same direct dependency in both `frontend/package.json` and `frontend/package-lock.json`.

## Affected Package And Dependency Paths

| Alert | Manifest | Package | Ecosystem | Scope | Relationship | Current | Vulnerable Range | First Patched |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dependabot #2 | `frontend/package.json` | `vitest` | npm | development | direct | `^3.2.4` before patch; `^4.1.8` after patch | `<4.1.0` | `4.1.0` |
| Dependabot #1 | `frontend/package-lock.json` | `vitest` | npm | development | direct | `3.2.4` before patch; `4.1.8` after patch | `<4.1.0` | `4.1.0` |

Local dependency path:

```text
frontend root project
└── vitest@4.1.8 (devDependency)
```

## Impact Classification

| Area | Affected? | Notes |
| --- | --- | --- |
| Frontend | Yes, dev/test tooling only | `frontend/package.json` uses `vitest` for `npm run test`. |
| Backend | No | Python backend dependencies are not involved in this advisory. |
| MkDocs | No | MkDocs Python documentation stack is not involved. |
| Dev-only tooling | Yes | The vulnerable dependency is a direct frontend `devDependency`. |
| Runtime production code | No known direct impact | The React/Vite production bundle does not include Vitest test tooling. Production exposure would require shipping or running Vitest UI/API/browser-mode tooling in an exposed environment. |

## Advisory Summary

The advisory describes arbitrary file read and possible file write/execution paths when the Vitest UI/API server or Browser Mode is listening, especially on Windows or when exposed beyond localhost. The current project test script is:

```text
npm run test -> vitest run
```

No project script currently starts Vitest UI, Browser Mode, or a network-exposed Vitest API server. That lowers practical production exposure, but the package remains a critical dev-tooling issue because contributors run on Windows and the advisory's affected conditions include Windows UI/browser-mode usage.

## Patched Versions

Patched versions exist.

- First patched version: `vitest@4.1.0`
- Latest checked patched version: `vitest@4.1.8`

`npm audit` reports:

```text
vitest <4.1.0
fix available: vitest@4.1.8
semver-major: true
```

## Breaking-Change Assessment

Upgrading from `vitest@3.2.4` to `vitest@4.1.x` is a major-version upgrade.

Observed package metadata:

| Version | Node engine | Vite peer range |
| --- | --- | --- |
| `vitest@3.2.4` | `^18.0.0 || ^20.0.0 || >=22.0.0` | `^5.0.0 || ^6.0.0 || ^7.0.0-0` |
| `vitest@4.1.0` | `^20.0.0 || ^22.0.0 || >=24.0.0` | `^6.0.0 || ^7.0.0 || ^8.0.0-0` |
| `vitest@4.1.8` | `^20.0.0 || ^22.0.0 || >=24.0.0` | `^6.0.0 || ^7.0.0 || ^8.0.0` |

Current local environment checked during review:

```text
node v24.16.0
npm 11.13.0
```

Current frontend Vite dependency is compatible with Vitest 4's peer range:

```text
vite ^7.1.12
```

The likely breaking-change risk is moderate:

- Node 18 would no longer be supported for frontend tests after upgrading.
- Vitest 4 may contain API, snapshot, mock, coverage, or reporter changes.
- Current test usage appears simple (`describe`, `it`, `expect`, `vi`, `beforeEach`, `afterEach`), so migration risk is probably manageable.
- No `@vitest/ui`, Browser Mode, jsdom, happy-dom, or custom Vitest config was found in the project scan.

## Patch Applied

Targeted command used from `frontend/`:

```text
npm install --save-dev vitest@^4.1.8
```

No `npm audit fix --force` command was used. The intended dependency files changed:

- `frontend/package.json`
- `frontend/package-lock.json`

The lockfile changed within Vitest's own dependency graph as part of the 4.x major upgrade. No runtime application code changed.

Post-upgrade package resolution:

```text
ai1sad-dashboard@0.1.0 F:\shark-attack-api\frontend
`-- vitest@4.1.8
```

Post-upgrade audit:

```text
npm audit --audit-level=high
found 0 vulnerabilities
```

Validation after the targeted upgrade:

- Frontend tests: `3 passed`, `8 tests passed`
- Frontend build: passed
- Backend tests: `197 passed, 2 warnings`
- MkDocs build: passed with the standard Material for MkDocs advisory banner
- Secret scan: no matches

## Recommendation

Recommended action: safe patch now, with normal validation, not `npm audit fix --force`.

Proposed manual follow-up:

```text
cd frontend
npm install -D vitest@^4.1.8
npm test
npm run build
```

Then run the normal repo validation:

```text
backend tests
mkdocs build
secret scan
prohibited-language scan
```

Rationale:

- The package is direct and dev-only, so the patch scope is isolated to frontend test tooling.
- A patched version exists.
- The project already uses Node 24 locally, which satisfies Vitest 4's engine requirement.
- Vite 7 is within Vitest 4's peer range.
- The current tests use basic Vitest APIs and should be relatively low-risk to validate.

Do not use `npm audit fix --force` as the primary path because it may apply broader lockfile changes than necessary. The applied patch followed the explicit Vitest-only update path.

## Deferral Criteria

Defer only if the active CI or deployment environment is pinned to Node 18 and cannot be moved to Node 20+ immediately. If deferred:

- keep `vitest run` local-only
- do not run Vitest UI or Browser Mode
- do not expose any Vitest API/UI server to the network
- document the Node 20+ migration blocker
- monitor the advisory for any 3.x backport, although none is currently indicated by Dependabot

## Replace Or Monitor

Replacement is not recommended at this time. Vitest is already aligned with the Vite-based frontend stack, and the patched 4.x line addresses the advisory. Monitor upstream only if a Node 18 test environment blocks the upgrade.
