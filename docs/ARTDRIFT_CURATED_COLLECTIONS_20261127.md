# Art Drift — themed collection canvases (2026-11-27)

Source candidate #19 exact SHA 5b18249fa6b951257c8f5531a557c15f85b5cb11. Rebased as an Art-only feature on current main; explicit preservation of current read-only D1 cloud search, historic Art toolbar, source-native artwork identities, and retained rights.

- Themes: landscapes, portraits, gardens/flowers, seas, still lifes, 19th/20th centuries and source museums. Only original title, source-native tags, explicit dates or museum IDs; no invented aesthetic labels, AI recognition or media import.
- Entrance from search sheet only when query is empty, with restrained parchment cards and counts in six languages.
- Collection canvas reuses canonical Drift Core via Art InfiniteGallery, with an independent `artdrift.collection.<id>.camera` key, never rewriting canonical `artdrift.camera`.
- On Android and Web collection works must have real preview assets, not metadata-only blank cards. Full search catalog remains available.
- Source/rights/CC0 approvals remain unchanged; no new images, no cloud writes, login, ads or permissions.
- Exact-head Web/Android CI and physical UX/accessibility signoff before external release.
