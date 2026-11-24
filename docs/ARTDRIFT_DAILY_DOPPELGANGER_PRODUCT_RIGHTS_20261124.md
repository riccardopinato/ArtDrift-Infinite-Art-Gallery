# ArtDrift: Doppleganger del giorno — editorial pilot 24/11/2026

## Product behavior
- User's exact Italian title **Doppleganger del giorno** (spelled Doppleganger as requested). Six-language interface translations provided.
- A featured card in the existing Search Atrium opens a full-screen page. Left column: genuine painting; right: genuine photograph of celebrity, two equal framed images with BoxFit.contain, no generated/face-swapped imagery and no bottom navigation. Source/credit/license links visible under an expansion tile.
- One deterministic reveal per *device-local calendar day*, persisted as a single SharedPreferences value. The user can reopen that day's same pair. Tomorrow changes pair and never repeats yesterday, even on pool reshuffle. Fail closed on removed current pair and backwards device clock.
- A device-local clock is not tamper-proof, and uninstall/reset or a second device can bypass local limits. Real worldwide gating needs an explicitly authorized backend/server clock; this MVP introduces none.
- No facial recognition or biometric embeddings; public-figure likeness is an editorial, subjective comparison, not identity assertion or endorsement.

## Two source-documented QA pairings
1. Paul Mounet (Louis-Maurice Boutet de Monvel, c. 1875), painting public-domain file at Wikimedia Commons, with Keanu Reeves (photo Anna Hanks, Commons CC BY 2.0). Editorial similarity noted by SpeakART and Google Arts & Culture.
2. Carl Adolf Feilberg (Christen Købke, 1835, Statens Museum for Kunst KMS3157), painting CC0 at Commons, with John Krasinski (photo Prime Video AU & NZ, Commons CC BY 3.0). Editorial similarity noted by DailyArt Magazine.

Each record has ID, exact Commons filename and File source page, original creator, name, year, photo author, license and license URL, plus the third-party editorial comparison source. Image data is hotlinked from Commons FilePath on demand (no third-party photo binaries in APK or repo). Technical fallback on image errors. No made-up numerical resemblance score.

## Delivery and release gates
- Feature is OFF by default via ARTDRIFT_ENABLE_DAILY_DOPPELGANGER compile-time flag, enabled in explicitly private QA builds only. Two entries marked INTERNAL_QA_REVIEWED; publicationStatus=INTERNAL_QA_ONLY; commercialPublicityCleared=false.
- Before **any public release**, recheck licenses on four individual media sources and photographer attribution; verify living-person publicity/name/likeness usage under applicable law, editorial consistency, hosting reliability and any redistribution requirements. 2 pairs alternate A/B daily and are inadequate for long-term retention: target 30+ individually reviewed pairs.
- Android and Web screen visual/device acceptance, image URL reachability, midnight rollover, persistence and offline state to verify. A Commons file license is not a blanket celebrity endorsement or commercial publicity release.
- No changes to Drift Core, GalleryDrift, Cloudflare D1, Supabase Auth, favorite storage, ad placement or painter canvas camera. No new cloud cost, notifications, push or automatic publication.
- Baseline App-Factory-Core ede07c491e586215598ff68daec43e17d699aa51, Master v27, relevant editorial versioning and responsive visual QA Golden draft. Branch PR must stay Draft until all rights/release gates.

## Authoritative source URLs
- https://commons.wikimedia.org/wiki/File:Portrait_de_Paul_Mounet_By_Louis-Maurice_Boutet_de_Montvel.jpg
- https://commons.wikimedia.org/wiki/File:Keanu_Reeves_2014.jpg
- https://commons.wikimedia.org/wiki/File:Christen_K%C3%B8bke_-_Portrait_of_Carl_Adolf_Feilberg_-_KMS3157_-_Statens_Museum_for_Kunst.jpg
- https://commons.wikimedia.org/wiki/File:John_Krasinski_2022.jpg
- https://www.speakart.it/en/five-celebrities-and-their-doppelgangers-in-the-art-world/
- https://www.dailyartmagazine.com/famous-people-and-their-doppelgangers-in-art/
