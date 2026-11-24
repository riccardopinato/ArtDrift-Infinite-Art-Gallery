# Art Drift — full 10/10 G2 source candidate (24 November 2026)

**Scope:** on top of PR #58 source `9c00cd49f84066417be897b07462740bf0a06ff6`. Reconcile remaining G2 slots 1/2/3/7 from PR #40, not entire legacy branch. Baseline Factory `ede07c491e586215598ff68daec43e17d699aa51`. No public release or production signing.

## Interface and event contract
- G2 #1 Quiet Canvas and immersion: opt-in museum chrome, idle fade, tap/pointer restores toolbar. The canvas still runs with the actual original engine, without inventing its own render loop.
- G2 #2 long-press tile factual plaque anchored by real source artwork and actual viewport-local tile rectangle; no paintings substituted or copied. Closes on gesture.
- G2 #3 artwork-only flight transitions from exact tapped tile Rect; fallback to simple fade on reduced motion, no scale of entire page.
- G2 #7 Auto/Pausa + bounded speed popover 25/50/75/100 and settings persistence, retains legacy Gallery controls when `museumControls=false`.
- G2 #4/5/6/8/9/10 from PR #58; together **10/10 SOURCE_CANDIDATE**, not 10/10 VISUAL_APPROVED or PHYSICAL_ACCEPTED.
- G2 ad-aware layout component is geometry/QA-only; **no AdMob SDK and no actual ads**. Default 0px leaves no blank bottom gap.

## Hard constraints and cross-app preservation
- Only shared-core change: `packages/drift_core/lib/src/drift_canvas.dart` with **optional arguments** and default `museumControls=false`. Old GalleryDrift behavior should remain byte-for-byte in current consumer; add paired consumer branch CI before this PR can merge.
- Old `artdrift.camera` remains the exact key for old/new installs, and the 4,500 item order is preserved for saved-camera users. Do **not** restore the old `ARTDRIFT_VISUAL_HOME_DEFAULT` alternate camera/path: it moves previously visited tiles. New Android installs use 2,400 curated actual assets from #57.
- D1 read-only archive from PR #54 preserved, 585 new candidates and 635 HOLD not activated; Cloudflare, Supabase and Gallery media privacy unchanged.
- Image rights 4,042 global WebP pack **not commercial-release cleared**; no launch. Single missing Smithsonian metadata-only exception and NGA duplicate issue still open.

## Gates
1. Flutter core test matrix and Flutter App Android/Web exact-head CI.
2. New independent GalleryDrift consumer pin in an isolated PR, CI and correctness of Gallery photo-library permission, local selection, 48-pan and reset path; main pin unchanged until coordinated adoption.
3. Pixel-level compare with 10 approved designs; actual on-device Android 320/390/820, speed popup, long-press and flight; read GPU frame p50/p95/p99 at 60/120Hz and RAM/thermal, preferences persisted on install upgrade.
4. Rights/credits/jurisdiction signoff and stable Android signing, **required** before publication or final acceptance. Keep PR Draft until gates complete.
