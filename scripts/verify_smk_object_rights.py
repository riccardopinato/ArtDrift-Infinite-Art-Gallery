#!/usr/bin/env python3
"""Object-by-object SMK official API rights recheck (not commercial legal clearance).

No rights inference from general museum policy. An item is approved for an
internal WebP acquisition ONLY if the current SMK object endpoint repeats the
EXACT object number, public-domain boolean, PDM/CC0 rights URI and IIIF image
prefix stored in the catalog. Network errors fail closed.
"""
import argparse
import collections
import concurrent.futures
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

CATALOG = Path("assets/museums/catalog_global.json")
RESULT = Path("docs/generated/SMK_OBJECT_RIGHTS_RECHECK.json")
API = "https://api.smk.dk/api/v1/art/"
PDM = ("https://creativecommons.org/publicdomain/mark/1.0/",
       "https://creativecommons.org/publicdomain/zero/1.0/")
HEADERS = {"User-Agent": "ArtDrift/0.3 rights-provenance-research (public SMK Open API)",
           "Accept": "application/json"}


def candidates(payload):
    if isinstance(payload, list):
        return [v for v in payload if isinstance(v, dict)]
    if not isinstance(payload, dict):
        return []
    for name in ("items", "data", "results", "artworks", "records"):
        v = payload.get(name)
        if isinstance(v, list):
            return [x for x in v if isinstance(x, dict)]
        if isinstance(v, dict):
            return [v]
    return [payload]


def verify(row):
    key = f"smk:{row['id']}"
    number = str(row.get("museum_native_id", "")).strip()
    evidence = str(row.get("rights_evidence_url", "")).strip()
    preview = str(row.get("remote_preview_url", ""))
    fail = {"key": key, "native_id": number, "status": "HOLD",
            "reason": "NO_MATCHING_OFFICIAL_OBJECT"}
    if not number or evidence not in PDM or row.get("is_public_domain") is not True:
        fail["reason"] = "LOCAL_RIGHTS_METADATA_NOT_EXPLICIT_PDM_CC0"
        return fail
    try:
        url = API + "?" + urlencode({"object_number": number, "lang": "en"})
        with requests.get(url, headers=HEADERS, timeout=(5, 12),
                          stream=True, allow_redirects=False) as response:
            if response.status_code != 200:
                fail["reason"] = f"PROVIDER_HTTP_{response.status_code}"
                return fail
            if not response.headers.get("Content-Type", "").lower().startswith("application/json"):
                fail["reason"] = "UNEXPECTED_PROVIDER_CONTENT_TYPE"
                return fail
            raw = response.raw.read(1_500_001, decode_content=True)
            if len(raw) > 1_500_000:
                fail["reason"] = "PROVIDER_RESPONSE_TOO_LARGE"
                return fail
        decoded = json.loads(raw)
        arr = candidates(decoded)
        for obj in arr:
            if str(obj.get("object_number", "")).strip().casefold() != number.casefold():
                continue
            rights = str(obj.get("rights", "")).strip()
            iiif = str(obj.get("image_iiif_id", "")).strip()
            if (obj.get("public_domain") is not True or not obj.get("has_image")
                    or rights not in PDM or rights != evidence
                    or not iiif.startswith("https://iip.smk.dk/iiif/")
                    or not preview.startswith(iiif + "/full/")):
                fail["reason"] = "PROVIDER_METADATA_RIGHTS_OR_IMAGE_MISMATCH"
                return fail
            canonical = json.dumps(
                {"object_number": number, "rights": rights, "iiif": iiif,
                 "public_domain": obj["public_domain"]},
                sort_keys=True).encode()
            return {"key": key, "native_id": number,
                    "status": "OFFICIAL_OBJECT_METADATA_MATCH",
                    "reason": "PDM_CC0_OBJECT_AND_EXACT_IIIF",
                    "verified_image_prefix": iiif,
                    "official_rights": rights,
                    "object_metadata_sha256": hashlib.sha256(canonical).hexdigest(),
                    "provider_endpoint": url,
                    "commercial_release_cleared": False}
        fail["reason"] = ("NO_EXACT_ITEM_IN_RESPONSE;top_keys=" +
                          ",".join(sorted(decoded)[:12]) if isinstance(decoded, dict)
                          else "NO_EXACT_ITEM_IN_RESPONSE")
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        fail["reason"] = "PROVIDER_ERROR_" + type(exc).__name__
    return fail


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--max-items", type=int, default=500)
    p.add_argument("--workers", type=int, default=2)
    args = p.parse_args()
    if not 1 <= args.max_items <= 500 or not 1 <= args.workers <= 3:
        p.error("bounded provider-friendly limits required")
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    all_smk = sorted([v for v in data if v.get("museum_source") == "smk"],
                     key=lambda r: int(r["id"]))
    if len(all_smk) != 500:
        raise SystemExit(f"SMK_CATALOG_DRIFT: expected 500, got {len(all_smk)}")
    selected = all_smk[:args.max_items]
    # Two concurrent official requests at most; a very small pause on each
    # task avoids a burst of many HTTP requests against the public museum API.
    def process(row):
        time.sleep(.12)
        return verify(row)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        checked = list(pool.map(process, selected))
    tallies = collections.Counter(x["reason"] for x in checked)
    statuses = collections.Counter(x["status"] for x in checked)
    output = {
        "schema_version": 1,
        "official_api": API,
        "catalog_smk_total": len(all_smk),
        "objects_checked": len(checked),
        "validated_for_bounded_download": statuses["OFFICIAL_OBJECT_METADATA_MATCH"],
        "not_checked": len(all_smk) - len(checked),
        "statuses": dict(sorted(statuses.items())),
        "reasons": dict(sorted(tallies.items())),
        "commercial_release_cleared": False,
        "verified": checked,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(output, indent=2, ensure_ascii=False,
                                 sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k != "verified"},
                     indent=2))
    if not checked:
        raise SystemExit("NO_SMK_RECORDS")
    return output


if __name__ == "__main__":
    main()
