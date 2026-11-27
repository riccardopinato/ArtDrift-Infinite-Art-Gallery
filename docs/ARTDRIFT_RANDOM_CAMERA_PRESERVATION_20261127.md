# Drift Core — Random-start camera preservation fix (2026-11-27)

Source: Art Drift PR #110 merged `45984f1ee15c7c8d80d7c4a65c18f67bf3674407`; this hotfix preserves the pre-existing explicit user camera preference keys when random-region mode is ON.

Bug: `initialWorldCenter` skipped restoring saved camera but old pan/fling events still called `_saveCamera()`, overwriting those keys. Fix: while `initialWorldCenter != null`, camera saves are intentionally ephemeral; when the mode is turned OFF, original saved x/y/zoom are restored unmodified. Recenter uses that session's random starting region, not global zero. No impact on GalleryDrift, which passes null by default, or Art installations with random-region mode disabled. Same source-ID/viewport, no catalog, right, account, asset changes.

Must run exact-head Art Web/Android + Gallery pinned consumer CI before merge. Physical gesture/device QA remains separate.
