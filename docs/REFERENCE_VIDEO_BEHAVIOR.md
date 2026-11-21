# UX reference observations — user supplied video, 2026-11-21

Source: `WhatsApp Video 2026-11-21 at 03.46.50.mp4`, 47.5s, 848 × 478, 30fps.
The video is **not** redistributed in the public repository.

1. 0–2s: a painting detail screen on almost-black background, small white Italian text near left, large uncropped painting near the center/right.
2. 3–10s: dense mixed-ratio artwork mosaic as the viewport moves; almost no whitespace, ~thin dark gutters.
3. ~11–13s: selected painting opens into full-frame detail with concise Italian narrative.
4. ~15–20s: move back to mosaic; variable tile sizes, very little UI chrome; returning to the same region reveals the same works.
5. 27–31s: detail of seascape, with small white controls on upper-right.
6. ~38–43s: another detail with left-side caption and action 'Imposta come sfondo'; close returns to mosaic.

ArtDrift target interaction: original implementation of these behavior categories, adapted to handheld portrait. No pixel-exact brand copying.

### QA acceptance

- Pan left/right/up/down changes virtual viewport, no apparent edge.
- Pinch zoom preserves focal-point world coordinate; no sudden jump.
- Artworks remain assigned to the same virtual positions when revisited.
- Only visible/nearby tile widgets are created, with memory cap.
- Tap opens an immersive full-frame detail, not a new Home/list.
- Close returns to the same canvas camera and approximate art arrangement.
- Offline, failed images, image format, gesture conflicts and extremely distant coordinates are handled honestly.
