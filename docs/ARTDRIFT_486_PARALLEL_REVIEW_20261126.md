# Art Drift — 486 independently reviewed image candidates (November 26, 2026)

This is a research-only parallel evidence pipeline, **not an import or a publication**.

## Input and identity
- Exactly 486 candidates from the seven user-selected painters.
- Immutable source: PR #84 at commit b82a4574db3d504141b6d2e95e403aa743c771e3.
- Do not use the 4,042 WebP pack as an additive source; those assets map to existing catalog works.
- No edits to Flutter, source catalogs, image assets, shared Drift Core, Cloudflare D1 or GalleryDrift.

## Parallelization
- Deterministic SHA-256 identity partition into 18 workers; every candidate processed exactly once.
- GitHub Actions max-parallel=6: limits remote load/rate limiting and avoids 486 PR branches.
- Each worker emits per-image technical evidence and a visual contact sheet.
- Aggregate checks identity uniqueness and completeness (486/486) and exports an inspection CSV.
- HTTP 403/429, unsupported images or unavailable sources remain an explicit technical HOLD; the pipeline never inserts fabricated replacements.

## Important rights and curation boundary
- Commons metadata contains license claims such as public domain, CC0, CC-BY or CC-BY-SA; the claim alone is not a full legal clearance.
- Artists' authorship, photo/image rights, underlying-work protection, jurisdiction, exact version, attribution requirements and provider policy remain per-object review.
- Brightness and color metrics are technical signals, not proof of artistic quality.
- Pixel quality PASS does not convert an image into a publishable asset.
- Every output deliberately preserves commercial_approval=false and runtime_visible=false.

## Review and eventual integration sequence
1. Inspect result CSV, preview contact sheets, source metadata, artist attribution and duplicate groups.
2. Resolve individual identity and rights evidence and mark unsupported/restricted files as rejected.
3. Reconcile against current main artwork IDs and semantic duplicates before proposing a new versioned catalog addition.
4. Only after legal/visual gates, create a separately reviewed runtime-import PR with actual images and license/credit requirements, CI, user visual acceptance and physical Android test.
5. No public deploy, Store release or automatic merges from this research workflow.
