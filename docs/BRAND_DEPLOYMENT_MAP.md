# AI1SAD Brand Deployment Map

## Canonical Source Artwork

The canonical source artwork is stored in `images/branding/`.

| Asset | Source path | Role |
| --- | --- | --- |
| Primary emblem | `images/branding/avatar-primary.png` | Main AI1SAD emblem and favicon source |
| Primary avatar | `images/branding/reddit-avatar-under-500kb.jpg` | Compact avatar for dashboard chrome |
| GitHub/social banner | `images/branding/banner-github.png` | Homepage hero, dashboard banner, and social preview |
| Reddit banner | `images/branding/banner-reddit.jpg` | Narrow banner and demo banner texture |
| Concept board | `images/branding/branding_asset_collection.png` | Visual direction reference for radar, sonar, heatmap, and dashboard motifs |

## MkDocs Deployment Copies

| Deployment path | Used by |
| --- | --- |
| `docs/assets/brand/ai1sad-emblem.png` | MkDocs theme logo and homepage emblem |
| `docs/assets/brand/favicon.png` | MkDocs browser favicon |
| `docs/assets/brand/ai1sad-social-banner.png` | MkDocs homepage hero and configured social preview reference |
| `docs/assets/brand/ai1sad-reddit-banner.jpg` | Docs-accessible Reddit banner deployment copy |
| `docs/assets/brand/ai1sad-avatar.jpg` | Docs-accessible avatar deployment copy |

## Frontend Deployment Copies

| Deployment path | Used by |
| --- | --- |
| `frontend/public/brand/ai1sad-emblem.png` | Sidebar brand mark and demo banner mark |
| `frontend/public/brand/ai1sad-avatar.jpg` | Topbar avatar and replay card thumbnail texture |
| `frontend/public/brand/favicon.png` | Browser tab favicon |
| `frontend/public/brand/ai1sad-social-banner.png` | Dashboard banner, replay detail visual, and share preview metadata |
| `frontend/public/brand/ai1sad-reddit-banner.jpg` | Demo banner background |

## Visual Direction Applied

- Radar rings and sonar sweep language appear in the sidebar, MkDocs background, score cards, and map chrome.
- Ocean intelligence banners appear on the MkDocs homepage and dashboard header area.
- Heatmap colors are limited to calm operational cyan, amber, teal, and surveillance purple.
- Replay cards use branded thumbnail treatments without adding frontend scoring logic.

## Maintenance Rule

Update source artwork in `images/branding/` first, then refresh only the deployment copies that are actively referenced by MkDocs or the frontend.
