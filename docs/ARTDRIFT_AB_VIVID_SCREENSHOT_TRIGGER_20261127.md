# Art Drift visual A/B — real pixel-ranked canvas

2026-11-27 screenshot comparison candidate PR #113 source `55228ece5465df995d0a2a917bb7dadf4bdb5118`.
Compare real Flutter Web 390×844 and 820×1180 with original image-backed catalog screenshots in internal G2 QA.
New 2,400 artworks are sorted by real WebP chroma/brightness; the original artwork pixels must remain unchanged.
The source-metadata fingerprint determines whether this feature activates; if it fails, revert to original color selection.
Do not declare HUMAN_VISUAL_APPROVAL from nonblank screenshot alone or release any newly licensed image.
