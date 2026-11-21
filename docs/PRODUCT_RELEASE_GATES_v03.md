# ArtDrift v0.3 — Implementation and public-release gates

Status: code implementation; not an approved commercial launch.

## UI decision (2026-11-21)
- Keep the approved infinite dark art canvas, current artwork layout and detail UX intact.
- Top-center brush search pill exactly 1/3 width, vector-painted ivory/gold frame.
- Search sheet uses parchment/aged-ivory gradient with subtle vector decorative frame, original Flutter implementation (no raster assets).
- Top-right settings framed icon. The previous recenter control moves to lower right, above the canvas instruction.
- Design-App checked: Vintage MOCK-STYLE-003 and Editorial UI are REFERENCE_ONLY patterns, no copy-ready artwork or license; adapted independently.
- No navigation bar, no advertising banner yet.

## Search
- Certified App Factory ephemeral hybrid search donor copied unchanged, two source blobs pinned. Adapter supports author/title/subject/all and live local prefix suggestions.
- Topic aliases (parco -> park/garden etc.) search text/tags/metadata. No universal object detection and NO AI claim.
- External museum search is a separate tap (not called per keystroke). The searched words go to museum APIs directly. A returned record is eligible only if its source explicitly says public-domain/CC0, its object type is a painting and image host is museum-allowlisted.
- Met source uses CURRENT /public/collection/v1.1/search paginated API (old /v1/search retired October 2026), with maximum 24 object checks, only 8 resulting paintings.
- Cleveland: GET /api/artworks/?q=&cc0=1&has_image=1&limit=30, bound to 10 paintings. Both providers fail independently and do not update canvas/notes/favorites silently.
- Rijksmuseum official API uses Linked Art identifiers, image IIIF manifests and item rights: **integration pending source-specific adapter and evidence**. Do not claim it implemented.
- Long-term stable catalog architecture: introduce persistent source ID / versioned catalog and deterministic positional mapping before making remote paintings part of the infinite mosaic. Appending directly to the v0.2 modulo-index layout would shuffle previously seen works, violating user expectation.
- Visual subject recognition, full 10k corpus, image description embeddings and editorial tags are separate data-quality work, not present in this build.

## Locales
- Interface labels and privacy/purchase status available in it, en, fr, es, de, pt.
- Artwork source titles, dates, authors and descriptions stay in their ORIGINAL museum language. No claim of six-language editorial translation until full catalog translations are QAed, sourced and versioned.

## Pro/Billing
- Golden: GOLDEN_ENTITLEMENT_CONTRACT_FLUTTER_v1 (copy-ready provider-agnostic).
- This build does NOT expose fake purchases or Pro grants. Default plan Free, verification required, no billing plugin yet.
- Later: configure exact Play Console product, stable app signing identity, tested billing adapter and backend/store verification or scoped low-value verification contract, restore/revoke, purchase states and internal test track. Obtain the Play catalog localized price instead of hardcoding it.
- Pro could suppress ads and unlock premium curated collections, offline full-resolution packs or visual-semantic search; these capabilities are proposals, not current features or promised purchases.
- For publisher: define entity/contact/support and public privacy-policy URL before release.

## Privacy and AdMob
- Local: favorites, language, canvas coordinate, and bundled 72 low-res paintings.
- Network: remote IIIF images requested on view/zoom; explicit museum-search query is sent to museum API endpoints. Existing AIC catalog refresh requires a user action.
- No login, no ads SDK, no payments SDK, no user analytics in this version.
- **Play Store Data Safety** is not certified until complete SDK/API/permissions audit and public policy, including server/request logs at the provider boundary.
- Before AdMob: UMP European consent, vendor disclosures and consent choices / withdrawal, non-personalized fallback where applicable; app-ads.txt, correct app IDs, testing ad units, placement/policy validation, Pro -> zero ad requests, no ad during keyboard/sheet/detail and reserve safe bottom area only once ads actually load.
- Never create an empty banner gap in the current immersive canvas.
- Privacy note in Settings is in-app technical summary, not a substitute for a hosted legal policy.
- No hidden WebView browser-based advertising/cross-app tracking.

## QA
- Focused tests: prefix, filters, scoped subject, no image hallucination; Met/Cleveland rights filter and allowlist; six locales; Pro fail-closed; toolbar 1/3 width, search and settings widgets.
- GitHub CI: Flutter analyze, tests, ARM64 internal-test APK, exact-head branch/PR and post-merge checks.
- Still pending: actual phone visual parity, 360px and tablets/landscape screenshots, safe-area/keyboard, remote API live QA, network failures and slow-image behavior, Pro Play sandbox and AdMob.
