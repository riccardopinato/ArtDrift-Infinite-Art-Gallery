# Drift Core — 21 November 2026
Source baseline: Art Drift main d329161c88f26eadf30e3f2ad3452c6e36aac604.
Shared engine lives in packages/drift_core. The existing gallery is a thin Artwork adapter to DriftCanvas<Artwork>; Artwork catalog, search, detail, language, privacy, Pro and image fallback remain app-owned.

Visual parity contract: original world hash/layout, 208px columns, 5px gap, 32 height cycle, 180 tiles cap, zoom 0.55..2.7, 450ms decelerate fling, same insets/branding/hint/recenter and artdrift.camera namespace. The only requested icon change here is tune -> settings gear.

Gallery Drift shall consume this package by pinned Git SHA using git.path=packages/drift_core, retain a distinct gallerydrift.camera namespace, and implement local albums/permissions via an adapter. Neither ads nor visual recognition are activated by this extraction.

Tests/source analyzed only when CI reports green; no physical-screen or Play policy certification implied.
