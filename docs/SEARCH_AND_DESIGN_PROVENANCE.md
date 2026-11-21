# ArtDrift search provenance and accuracy

- Factory baseline: App-Factory-Core \`9391419c6b7c9c23c2f978262fe8fe6670c68160\`, CURRENT master v27, Golden Index v31.
- Certified ephemeral local search donor: \`reference_engines/lib/src/hybrid_search.dart\` and \`semantic_embeddings.dart\` from same baseline. Vendor blob SHA-1 \`95de49c3e531451b8984461223a6a5fb1d9cc1f1\`, \`de96c2dbf0da2c0c4695308efd5b9bbab25b75f5\`; original files unchanged.
- \`GallerySearch\` is an application adapter. It indexes title, author, origin and supplied museum subject terms. Partial name/title suggestions are local. Bounded lexical ranking uses feature hashing only as deterministic aid; **not an LLM or a visual semantic model**. It filters out weak feature-hash-only coincidences.
- Subject aliases for common terms (e.g. \`parco\` -> park/garden/jardin) are explicitly curated; this is *not* guaranteed recognition of arbitrary scenes. Without subject tags or visual annotations, a visually depicted but undescribed park may not match.
- A future (separately validated) vision/CLIP tagging pipeline should create licensed per-artwork semantic tags with confidence and provenance **off device**; its model need not inflate the APK. It must not silently overwrite museum facts.
- Local title/artist/subject indexes: no search query leaves device. External multi-museum search is explicit; it sends the entered query to the sources as described in the in-app privacy note.
- UI design: user-approved ArtDrift infinite mosaic remains unchanged. New parchment/ivory editorial overlay adapts Design-App \`MOCK-STYLE-003\` (Vintage) and \`UI-UX/EDITORIAL UI\` REFERENCE_ONLY guidance, not unlicensed copying of images or TSX components.
