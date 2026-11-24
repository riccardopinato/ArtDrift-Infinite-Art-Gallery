#!/usr/bin/env python3
"""Fail-closed source-index and private QA photo-attribution contract.

No real-photo downloads, public image clearance, or Wikimedia licensing inferred.
"""
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "research/doppelgangers/candidates_index_v2_20261124.json"
QA = ROOT / "assets/daily_doppelgangers.json"
EXPECTED_PILOT = {
    "paul-mounet-keanu-reeves", "carl-feilberg-john-krasinski",
    "sir-david-wilkie-rupert-grint", "strobel-johann-vogt-robert-de-niro",
    "paul-revere-jack-black",
}

def fail(msg):
    raise ValueError(msg)

def commons_file_name(file_url):
    uri = urlsplit(file_url)
    if uri.scheme != "https" or uri.netloc != "commons.wikimedia.org" or (
        not uri.path.startswith("/wiki/File:")) or uri.query or uri.fragment:
        fail("Unsafe/or noncanonical Commons media page")
    return unquote(uri.path.partition("File:")[2]).replace("_", " ")

def verify():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    qa = json.loads(QA.read_text(encoding="utf-8"))
    pairs = index["pairs"]
    if index.get("schemaVersion") != 2 or index.get("status") != "RESEARCH_ONLY_NOT_RUNTIME":
        fail("Research asset must not be imported as public content")
    if len(pairs) != 37 or len(set(p["id"] for p in pairs)) != 37:
        fail("Lost, duplicate or reassigned research candidate")
    priority = [p for p in pairs if p["reviewV2"]["researchPriority"] == "P1_REVIEW"]
    deferred = [p for p in pairs if p["reviewV2"]["researchPriority"] == "P2_DEFER"]
    if len(priority) != 30 or len(deferred) != 7:
        fail("30 + 7 source-review partition must be disjoint")
    for p in pairs:
        state = p["reviewV2"]
        if not all(state.get(flag) is False for flag in (
            "independentSideBySideVisualCertified", "photoPublicityRightsCleared",
            "commercialReleaseCleared")):
            fail("No visual or legal certification may be asserted for the research index")
        if state["sourceStatus"] == "BOTH_SOURCE_IMAGE_FILE_PAGES_DOCUMENTED":
            if not state["artworkOriginalFilePage"] or not state["celebrityPhotoOriginalFilePage"]:
                fail("Both source file links missing")
        if p["id"] == "AD-DG-027" and state["workMedium"] != "DRAWING_CONFIRMED_EXCLUDE_FROM_PAINTING_ONLY":
            fail("Schiele drawing must not enter painting-only catalog")
    if qa.get("publicationStatus") != "INTERNAL_QA_ONLY":
        fail("Not public-release eligible")
    entries = qa.get("pairs")
    if len(entries) != 5 or {p["id"] for p in entries} != EXPECTED_PILOT:
        fail("Private QA requires exactly source-checked five pairs")
    for p in entries:
        if p["status"] != "INTERNAL_QA_REVIEWED" or p["rightsReviewedForInternalPreview"] is not True:
            fail("Unreviewed QA pairing admitted")
        if p["commercialPublicityCleared"] is not False:
            fail("No commercial release / endorsement has been approved")
        for role in ("portrait", "celebrity"):
            item = p[role]
            if commons_file_name(item["filePage"]) != item["fileName"]:
                fail("Wrong photo attributed to source page")
            if not item.get("license") or not item.get("licenseUrl") or not item.get("credit"):
                fail("Attribution missing")
        if not p["celebrity"]["license"].startswith("CC BY "):
            fail("Photo license outside current Flutter validator")
    print("DOPPLEGANGER_RESEARCH_V2_PASS 37 SOURCED 30 PRIORITY 7 HOLD 5 PRIVATE_QA 0 PUBLIC")
    return True

if __name__ == "__main__":
    verify()
