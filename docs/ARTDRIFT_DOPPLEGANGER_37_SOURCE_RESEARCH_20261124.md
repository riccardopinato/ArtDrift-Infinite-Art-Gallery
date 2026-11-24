# ArtDrift — Doppleganger del giorno, web and visual research, 2026-11-24

## Scope / factual method

Source-only **37 candidate pairings** described by DailyArt Magazine, SpeakART, Artnet News, Dazed, Reddit r/ArtHistory and Bored Panda. The source index is for editorial backlog and is NOT loaded by Flutter or by any public app, and does not modify the existing two-pair feature QA in PR #62.

This explicitly distinguishes:
- a publisher's *suggested resemblance* (subjective editorial opinion);
- confirmed painting / artist / sitter / museum object from authoritative museum inventory;
- actual independently inspected two source media files and current photographic licenses;
- portrait-identity rights and rights for advertising, marketing and commercial app distribution.

Those are **separate review gates**. 37 suggested ≠ 37 independently validated image pairs ≠ 37 eligible for release.

## Quantified evidence, 2026-11-24

| Dimension | Count | Meaning |
|---|---:|---|
| Suggested pairings | 37 | Direct links to publishers, duplicates by actor remain distinct works |
| Named famous people | 35 | Keanu Reeves appears for three different painted works |
| Alleged original paintings | 29 | Based on publisher descriptions, object technique is not independently verified for every one |
| Artwork type/source uncertain | 8 | Need exact object, artist and technique before app eligibility |
| Editorial comparison images visually examined | 9 | Comparison montage/images; NOT independently authenticated high-resolution media pairs |
| Painting-only image visually examined | 1 | The matching celebrity reference image was not independently examined |
| Object-specific museum pages identified | 5 | Others still magazine citation, generic museum or user post |
| Both original image source/photo credits individually recorded | 2 | Inherited ArtDrift PR #62 private-QA examples, not commercial publicity authorization |
| Commercial/public ready | **0** | No release/AdMob/Play or new public media activation |

The detailed SQLite/JSON/CSV research export has individual year, museum, critical issues and side-by-side visual evidence category. The repo JSON is a **lightweight, validated candidate index**, intentionally separate from `assets/daily_doppelgangers.json`.

## Precise art-history/source discrepancies

1. **Sky TG24**, 23 July 2020: photo composites inserting celebrity heads through Photoshop. They are not original historical paintings and were **excluded** as evidence for this feature.
2. Rijksmuseum **Abraham van Strij, Seated Woman with Copper Kettle** is a drawing/watercolor, so the Dazed Chloë Sevigny candidate is excluded from the painting-only feature.
3. NGA **Winslow Homer, Under a Palm Tree** is a watercolor, so the Dazed Uma Thurman pairing is excluded from painting-only scope.
4. NGA `1942.9.96`, **Portrait of a Young Man, c.1505** is currently attributed to **Venetian 16th Century**, though DailyArt labels it Jacopo de' Barbari; record the museum's current attribution rather than treat an older attribution as canonical.
5. **Velázquez El bufón el Primo / Sebastián de Morra** historical sitter identity is disputed in scholarship: don't hardcode a definitive sitter without the current Prado object.
6. Zygmunt Waliszewski **Self-Portrait in a Red Turban** original Commons source labels **1929**, but another biography uses 1935: verify the exact object/variant before certifying the date.
7. SMK old `collection.smk.dk` redirects. Current source is **https://open.smk.dk/artwork/image/KMS3157** for Købke's **Portrait of Carl Adolf Feilberg**.
8. Keep one celebrity paired with multiple different paintings (e.g. Keanu Reeves or different celebrity matches to Franz Liszt) as **distinct candidate pairs**, not duplicate artwork records.

## Proposed editorial flow

- Keep product-facing 2 internal QA candidate pairs in PR #62 unchanged; feature remains feature-flag OFF in public builds.
- Verify 37 original painting images individually against museums and 37 celebrity photographs against original licensing/credit pages; record actual visual subject reference, object ID, image URL/file SHA, date, photograph source/credit, creator and commercial publicity/licensing review.
- For painting-only use, reject non-painting cases; future broader art archive may review them separately.
- Assign editorial quality labels (high/moderate/weak) with verbal reasons rather than fabricated numerical “face resemblance confidence”.
- On release only after item-level photo rights, editorial accuracy, content quality and physical visual checks, and with at least 30 diverse candidates to avoid alternating the same two examples. An offline date based on SharedPreferences does not enforce cross-device locking and does not avoid forward clock manipulation.

No new social scraping at runtime, no face-recognition biometric processing, no copyrighted magazine image download to the app and no Google Art Selfie private API reuse. User data and GalleryDrift remain untouched.

Factory baseline: App-Factory-Core `ede07c491e586215598ff68daec43e17d699aa51`. Golden versioned editorial catalog / media store / duplicate gate. PR should be **Draft** and its source CI PASS must not be mistaken for human rights review.
