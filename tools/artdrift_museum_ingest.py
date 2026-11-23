#!/usr/bin/env python3
"""Art Drift modern-art discovery -> rights-gated Cloudflare D1 staging SQL.

No third-party museum prose or image bytes are copied. No remote writes here.
Tate contributes metadata only; Wikidata/Commons media require per-file CC0/PDM,
a conservative artist-death gate, AND explicit subsequent publication approval.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlencode, unquote, urlparse
from urllib.request import Request, urlopen

TATE_CSV = "https://raw.githubusercontent.com/tategallery/collection/master/artwork_data.csv"
TATE_GUIDELINES = "https://github.com/tategallery/collection"
MOMA_CSV = "https://media.githubusercontent.com/media/MuseumofModernArt/collection/main/Artworks.csv"
MOMA_REPO = "https://github.com/MuseumofModernArt/collection"
WD_SPARQL = "https://query.wikidata.org/sparql"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
MUSEUMS = {
    "Q201469": "Solomon R. Guggenheim Museum, New York",
    "Q1049033": "Peggy Guggenheim Collection, Venice",
    "Q808462": "Barnes Foundation, Philadelphia",
    "Q303139": "Oesterreichische Galerie Belvedere, Vienna",
    "Q1568434": "Yale University Art Gallery, New Haven",
    "Q754507": "Ateneum, Finnish National Gallery, Helsinki",
    "Q2983474": "Finnish National Gallery, Helsinki",
    "Q857276": "Musee d'Art Moderne de Paris",
    "Q1132918": "Nasjonalmuseet, Oslo",
}
NAMES = (
    "monet", "renoir", "van gogh", "gauguin", "cezanne", "c zanne",
    "matisse", "modigliani", "kandinsky", "schiele", "klimt", "munch",
    "picasso", "mondrian", "delaunay", "dufy", "vlaminck", "soutine",
    "chagall", "paul klee", "franz marc", "francis bacon", "turner",
    "manet", "degas", "toulouse lautrec", "miro", "pollock", "zorn",
    "larsson", "de chirico", "boccioni", "balla", "okeeffe", "o keeffe",
    "schjerfbeck", "gallen kallela", "edelfelt", "hammershoi", "koko schka",
    "kokoschka", "signac", "seurat", "rousseau", "sisley", "pissarro", "kirchner",
)
UA = "ArtDrift-MuseumImporter/1.0 (public art research; GitHub riccardopinato/ArtDrift-Infinite-Art-Gallery)"
MAX_SOURCE_BYTES = 48 * 1024 * 1024
FIELDS = (
    "source_key", "provider", "native_id", "museum", "title", "artist",
    "year_text", "medium", "metadata_url", "image_url", "full_image_url",
    "rights_license", "rights_evidence_url", "rights_status", "fingerprint",
)


def clean(value: object, limit: int = 500) -> str:
    return "".join(c for c in str(value or "").strip() if c >= " " and c != "\x7f")[:limit]


def normalized_name(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c)).replace("-", " ").replace("'", "")


def famous(value: str) -> bool:
    name = normalized_name(value)
    return any(n in name for n in NAMES)


def safe_https(url: str, allowed_hosts: set[str]) -> bool:
    try:
        u = urlparse(url)
        return (u.scheme == "https" and u.hostname in allowed_hosts and
                u.username is None and u.password is None and
                u.port in (None, 443) and bool(u.hostname))
    except ValueError:
        return False


def request_bytes(url: str, *, accept: str, max_bytes: int = MAX_SOURCE_BYTES) -> bytes:
    u = urlparse(url)
    if u.scheme != "https":
        raise ValueError("Only HTTPS sources are allowed")
    req = Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urlopen(req, timeout=40) as response:
        if response.status != 200:
            raise ValueError(f"Source HTTP {response.status}")
        body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise ValueError("Source exceeds configured byte limit")
    return body


def request_json(url: str, *, max_bytes: int = 2_000_000) -> dict:
    data = json.loads(request_bytes(url, accept="application/json", max_bytes=max_bytes))
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    return data


def fingerprint(rec: dict) -> str:
    payload = {k: rec[k] for k in FIELDS if k != "fingerprint"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
        ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def record(*, provider: str, native_id: str, museum: str, title: str,
           artist: str, year: str, medium: str, metadata_url: str,
           image_url: str = "", full_image_url: str = "",
           rights_license: str = "", rights_evidence_url: str = "",
           rights_status: str = "METADATA_ONLY") -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_-]{1,30}", provider):
        raise ValueError("Invalid provider")
    native_id = clean(native_id, 128)
    if not native_id or not clean(title):
        raise ValueError("Missing work identity/title")
    if rights_status not in {"METADATA_ONLY", "IMAGE_REVIEW", "IMAGE_RIGHTS_VERIFIED"}:
        raise ValueError("Invalid rights status")
    if not safe_https(metadata_url, {
        "www.tate.org.uk", "www.wikidata.org", "github.com", "www.moma.org",
        *(host for allowed in OFFICIAL_METADATA_HOSTS.values() for host in allowed),
    }):
        raise ValueError("Unrecognized metadata URL")
    if rights_status == "IMAGE_RIGHTS_VERIFIED":
        if provider == "wikidata":
            image_hosts = {"upload.wikimedia.org"}
            evidence_hosts = {"commons.wikimedia.org"}
            accepted = {"CC0 1.0", "Public Domain Mark 1.0"}
        elif provider in OFFICIAL_IMAGE_HOSTS:
            image_hosts = OFFICIAL_IMAGE_HOSTS[provider]
            evidence_hosts = OFFICIAL_EVIDENCE_HOSTS[provider]
            accepted = {"CC0 1.0"}
        else:
            raise ValueError("No approved image provider policy")
        if not (safe_https(image_url, image_hosts) and
                safe_https(full_image_url, image_hosts) and
                safe_https(rights_evidence_url, evidence_hosts) and
                rights_license in accepted):
            raise ValueError("Missing independently verified file license")
    else:
        # Images in non-verified records are deliberately not stored.
        image_url = full_image_url = ""
        rights_license = rights_evidence_url = ""
    r = {
        "source_key": provider + ":" + native_id, "provider": provider,
        "native_id": native_id, "museum": clean(museum, 200),
        "title": clean(title), "artist": clean(artist, 220),
        "year_text": clean(year, 90), "medium": clean(medium, 250),
        "metadata_url": metadata_url, "image_url": image_url,
        "full_image_url": full_image_url, "rights_license": rights_license,
        "rights_evidence_url": rights_evidence_url, "rights_status": rights_status,
    }
    r["fingerprint"] = fingerprint(r)
    return r


def tate_row(row: dict) -> dict | None:
    artist = clean(row.get("artist"), 220)
    medium = clean(row.get("medium"), 250)
    if not famous(artist):
        return None
    # Medium must indicate an actual painting, not artist prints/sculpture.
    if not re.search(r"oil|acrylic|tempera|watercolour|watercolor|gouache|painting", medium, re.I):
        return None
    native_id = clean(row.get("id"), 128)
    title = clean(row.get("title"))
    if not native_id.isdigit() or not title:
        return None
    year = clean(row.get("year") or row.get("dateText"), 90)
    if year.isdigit() and not (1850 <= int(year) <= 1980):
        return None
    return record(
        provider="tate", native_id=native_id, museum="Tate Collection (UK)",
        title=title, artist=artist, year=year, medium=medium,
        metadata_url=f"https://www.tate.org.uk/art/artworks/{clean(row.get('accession_number'), 60)}"
        if re.fullmatch(r"[A-Za-z0-9]+", clean(row.get("accession_number"), 60))
        else TATE_GUIDELINES,
    )


def collect_tate(max_records: int) -> list[dict]:
    if not safe_https(TATE_CSV, {"raw.githubusercontent.com"}):
        raise ValueError("Tate URL not trusted")
    raw = request_bytes(TATE_CSV, accept="text/csv")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not {"id", "title", "artist", "medium"}.issubset(reader.fieldnames or []):
        raise ValueError("Unexpected Tate CSV schema")
    result = []
    for row in reader:
        r = tate_row(row)
        if r:
            result.append(r)
            if len(result) >= max_records:
                break
    return result



def moma_row(row: dict) -> dict | None:
    """MoMA CC0 factual dataset: NEVER import its copyrighted image links."""
    artist = clean(row.get("Artist"), 220)
    title = clean(row.get("Title"))
    type_ = clean(row.get("Classification"), 100).lower()
    medium = clean(row.get("Medium"), 250)
    ident = clean(row.get("ObjectID"), 128)
    if not (ident.isdigit() and title and famous(artist)):
        return None
    if "paint" not in type_ and not re.search(
            r"\b(oil|acrylic|tempera|gouache|watercolou?r)\b", medium, re.I):
        return None
    if type_ and "paint" not in type_:
        return None
    url = clean(row.get("URL"), 300)
    if not safe_https(url, {"www.moma.org"}):
        url = MOMA_REPO
    return record(
        provider="moma", native_id=ident, museum="Museum of Modern Art, New York",
        title=title, artist=artist, year=clean(row.get("Date"), 90),
        medium=medium, metadata_url=url,
    )


def collect_moma(max_records: int) -> list[dict]:
    """Read primary-source CC0 metadata, not MoMA licensed image thumbnails."""
    raw = request_bytes(MOMA_CSV, accept="text/csv", max_bytes=90 * 1024 * 1024)
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValueError("MoMA Git LFS pointer received instead of CSV bytes")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not {"ObjectID", "Title", "Artist", "Classification", "Medium"}.issubset(reader.fieldnames or []):
        raise ValueError("MoMA CSV schema changed")
    result = []
    for row in reader:
        rec = moma_row(row)
        if rec:
            result.append(rec)
            if len(result) >= max_records:
                break
    return result



# These hosts mirror the Art Drift catalog's pre-existing vetted museum adapters.
# The existing catalog only claims per-object CC0/PD metadata; publication remains HOLD.
OFFICIAL_IMAGE_HOSTS = {
    "cleveland": {"openaccess-cdn.clevelandart.org", "www.clevelandart.org", "clevelandart.org"},
    "met": {"images.metmuseum.org"},
    "smithsonian": {"ids.si.edu", "www.si.edu", "si.edu"},
    "smk": {"iip.smk.dk", "iip-thumb.smk.dk"},
    "nga": {"api.nga.gov", "media.nga.gov"},
    "rijks": {"iiif.micr.io"},
    "getty": {"media.getty.edu"},
}
OFFICIAL_METADATA_HOSTS = {
    "cleveland": {"www.clevelandart.org", "clevelandart.org"},
    "met": {"www.metmuseum.org", "metmuseum.org"},
    "smithsonian": {"www.si.edu", "si.edu", "americanart.si.edu", "npg.si.edu", "asia.si.edu"},
    "smk": {"www.smk.dk", "smk.dk", "open.smk.dk"},
    "nga": {"www.nga.gov", "nga.gov"},
    "rijks": {"www.rijksmuseum.nl", "rijksmuseum.nl", "data.rijksmuseum.nl"},
    "getty": {"www.getty.edu", "getty.edu", "data.getty.edu"},
}
OFFICIAL_EVIDENCE_HOSTS = {
    "cleveland": {"www.clevelandart.org", "clevelandart.org"},
    "met": {"www.metmuseum.org", "metmuseum.org"},
    "smithsonian": {"www.si.edu", "si.edu"},
    "smk": {"www.smk.dk", "smk.dk", "open.smk.dk"},
    "nga": {"www.nga.gov", "nga.gov"},
    "rijks": {"www.rijksmuseum.nl", "rijksmuseum.nl", "data.rijksmuseum.nl"},
    "getty": {"www.getty.edu", "getty.edu"},
}


def confirmed_eu_public_domain_artist(label: str) -> bool:
    """Conservative EU/Italy life+70 gate for the 2026 public art service.

    Explicit birth/death dates must be present in source artist label; a
    museum CC0 media flag alone cannot extinguish the painter's copyright.
    Handles multiple credited authors by requiring *all* to pass.
    """
    spans = re.findall(r"(?<!\d)(1[6789]\d{2}|20\d{2})\s*[-–—]\s*(1[789]\d{2}|20\d{2})(?!\d)", label)
    if not spans:
        return False
    return all(int(birth) <= int(death) <= 1955 for birth, death in spans)


def existing_catalog_row(row: dict) -> dict | None:
    """Admit ONLY pre-imported CC0 modernist paintings with official media hosts.

    Reject all generic public-domain labels unless the explicit CC0 item
    license and original publisher evidence are available. No new HTML scrape.
    """
    if not isinstance(row, dict):
        return None
    source = clean(row.get("museum_source"), 30)
    artist = clean(row.get("artist_title") or row.get("artist_display"), 220)
    if source not in OFFICIAL_IMAGE_HOSTS or not famous(artist):
        return None
    if not confirmed_eu_public_domain_artist(artist):
        return None
    if row.get("is_public_domain") is not True:
        return None
    if clean(row.get("artwork_type_title")).casefold() != "painting":
        return None
    if clean(row.get("rights_license")).casefold() not in ("cc0", "cc0 1.0"):
        return None
    preview = clean(row.get("remote_preview_url"), 1800)
    original = clean(row.get("remote_full_url"), 1800) or preview
    evidence = clean(row.get("rights_evidence_url"), 800)
    detail = clean(row.get("remote_museum_url"), 500)
    if not (safe_https(preview, OFFICIAL_IMAGE_HOSTS[source]) and
            safe_https(original, OFFICIAL_IMAGE_HOSTS[source]) and
            safe_https(evidence, OFFICIAL_EVIDENCE_HOSTS[source]) and
            safe_https(detail, OFFICIAL_METADATA_HOSTS[source])):
        return None
    native = clean(row.get("museum_native_id"), 128)
    if not native or not clean(row.get("title")):
        return None
    return record(
        provider=source, native_id=native, museum=clean(row.get("museum_name"), 200),
        title=clean(row.get("title")), artist=artist,
        year=clean(row.get("date_display"), 90),
        medium=clean(row.get("medium_display"), 250), metadata_url=detail,
        image_url=preview, full_image_url=original,
        rights_license="CC0 1.0", rights_evidence_url=evidence,
        rights_status="IMAGE_RIGHTS_VERIFIED",
    )


def collect_verified_catalog(max_records: int) -> list[dict]:
    """Reuse existing Art Drift rights-checked works, not a second scraper."""
    out = []
    seen = set()
    files = [
        Path("assets/museums/catalog.json"),
        Path("assets/museums/catalog_global.json"),
    ]
    for path in files:
        if not path.is_file():
            continue
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("Unexpected Art Drift catalog format")
        for original in records:
            rec = existing_catalog_row(original)
            if rec and rec["source_key"] not in seen:
                seen.add(rec["source_key"])
                out.append(rec)
                if len(out) >= max_records:
                    return out
    return out


def wd_query(max_records: int, museum_ids: tuple[str, ...] | None = None) -> str:
    # P195 is collection membership (not painting the museum building).
    # Museum IDs are verified Wikidata entities, never user-provided free text.
    choices = museum_ids if museum_ids is not None else tuple(MUSEUMS)
    if not choices or any(q not in MUSEUMS for q in choices):
        raise ValueError("Unknown museum ID")
    ids = " ".join("wd:" + q for q in choices)
    return ("""
SELECT DISTINCT ?work ?workLabel ?museum ?image ?creatorLabel ?death WHERE {
  VALUES ?museum { %s }
  ?work wdt:P195 ?museum; wdt:P18 ?image;
        wdt:P31 wd:Q3305213.
  OPTIONAL { ?work wdt:P170 ?creator.
             OPTIONAL { ?creator wdt:P570 ?death. } }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr,it". }
} LIMIT %d
""" % (ids, min(max_records * 4, 400)))


def commons_image(file_url: str) -> tuple[str, str, str, str] | None:
    u = urlparse(file_url)
    if u.hostname != "commons.wikimedia.org" or not u.path.startswith("/wiki/Special:FilePath/"):
        return None
    filename = unquote(u.path.split("/wiki/Special:FilePath/", 1)[1])
    if not filename or "/" in filename or not re.search(r"\.(jpg|jpeg|png|webp)$", filename, re.I):
        return None
    title = "File:" + filename
    query = urlencode({"action": "query", "format": "json", "prop": "imageinfo",
                       "titles": title, "iiprop": "url|size|extmetadata",
                       "iiurlwidth": "640"})
    data = request_json(COMMONS_API + "?" + query)
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        ii = (page.get("imageinfo") or [{}])[0]
        metadata = ii.get("extmetadata") or {}
        license_url = clean((metadata.get("LicenseUrl") or {}).get("value"), 300)
        copyrighted = clean((metadata.get("Copyrighted") or {}).get("value"), 30).lower()
        if copyrighted not in ("false", "0"):
            return None
        allowed = {
            "https://creativecommons.org/publicdomain/zero/1.0/": "CC0 1.0",
            "https://creativecommons.org/publicdomain/mark/1.0/": "Public Domain Mark 1.0",
        }
        if license_url not in allowed:
            return None
        preview = clean(ii.get("thumburl"), 1800)
        original = clean(ii.get("url"), 1800)
        if not (safe_https(preview, {"upload.wikimedia.org"}) and
                safe_https(original, {"upload.wikimedia.org"})):
            return None
        # Canonical, directly inspectable Commons File page, not a museum claim.
        from urllib.parse import quote
        evidence = "https://commons.wikimedia.org/wiki/" + quote(title.replace(" ", "_"), safe=":_()")
        return preview, original, allowed[license_url], evidence
    return None


def wd_row(row: dict) -> dict | None:
    b = row.get
    work = clean(b("work", {}).get("value"), 150)
    museum = clean(b("museum", {}).get("value"), 150).rsplit("/", 1)[-1]
    qid = work.rsplit("/", 1)[-1]
    artist = clean(b("creatorLabel", {}).get("value"), 220)
    death = clean(b("death", {}).get("value"), 50)
    title = clean(b("workLabel", {}).get("value"))
    if museum not in MUSEUMS or not re.fullmatch(r"Q[1-9][0-9]*", qid) or not title or title == qid:
        return None
    if not famous(artist):
        return None
    base = dict(provider="wikidata", native_id=qid, museum=MUSEUMS[museum],
                title=title, artist=artist, year="", medium="Painting",
                metadata_url=f"https://www.wikidata.org/wiki/{qid}")
    # Public-domain age heuristics are a HOLD gate, not an image license.
    if not re.match(r"^[0-9]{4}-", death) or int(death[:4]) > 1955:
        return record(**base)
    info = commons_image(clean(b("image", {}).get("value"), 1800))
    if not info:
        return record(**base)
    preview, original, license_name, evidence = info
    return record(**base, image_url=preview, full_image_url=original,
                  rights_license=license_name, rights_evidence_url=evidence,
                  rights_status="IMAGE_RIGHTS_VERIFIED")


def collect_wikidata(max_records: int, museum_id: str | None = None) -> list[dict]:
    q = wd_query(max_records, (museum_id,) if museum_id else None)
    url = WD_SPARQL + "?" + urlencode({"query": q, "format": "json"})
    data = request_json(url)
    bindings = data.get("results", {}).get("bindings", [])
    if not isinstance(bindings, list):
        raise ValueError("Unexpected Wikidata shape")
    result, seen = [], set()
    for item in bindings:
        if not isinstance(item, dict):
            continue
        rec = wd_row(item)
        time.sleep(0.2)  # Bounded requests; no parallel Commons scraping.
        if rec and rec["source_key"] not in seen:
            seen.add(rec["source_key"])
            result.append(rec)
            if len(result) >= max_records:
                break
    return result


def sql_literal(value: str) -> str:
    if "\x00" in value:
        raise ValueError("Embedded NUL")
    return "'" + value.replace("'", "''") + "'"


def sql_upsert(rec: dict) -> str:
    if set(rec) != set(FIELDS) or fingerprint(rec) != rec["fingerprint"]:
        raise ValueError("Incomplete or modified record")
    columns = ", ".join(FIELDS)
    values = ", ".join(sql_literal(str(rec[k])) for k in FIELDS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in FIELDS if c != "source_key")
    # Same-content reimport keeps any separately approved publication decision.
    # Changed content always reverts publication approval to HOLD.
    return (
        f"INSERT INTO artdrift_museum_ingest ({columns}) VALUES ({values}) "
        "ON CONFLICT(source_key) DO UPDATE SET "
        "publication_status=CASE WHEN artdrift_museum_ingest.fingerprint=excluded.fingerprint "
        "THEN artdrift_museum_ingest.publication_status ELSE 'HOLD' END, "
        + updates + ";"
    )


def export(records: list[dict], jsonl_path: Path, sql_path: Path) -> dict:
    unique = {r["source_key"]: r for r in records}
    if len(unique) != len(records):
        raise ValueError("Duplicate external source identities")
    ordered = sorted(unique.values(), key=lambda r: r["source_key"])
    for r in ordered:
        if r["rights_status"] == "IMAGE_RIGHTS_VERIFIED":
            # Recheck policy on export; never trust a mutable status string.
            record(provider=r["provider"], native_id=r["native_id"], museum=r["museum"],
                   title=r["title"], artist=r["artist"], year=r["year_text"],
                   medium=r["medium"], metadata_url=r["metadata_url"],
                   image_url=r["image_url"], full_image_url=r["full_image_url"],
                   rights_license=r["rights_license"],
                   rights_evidence_url=r["rights_evidence_url"],
                   rights_status=r["rights_status"])
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    sql_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                                  for r in ordered), encoding="utf-8")
    # Wrangler D1 automatically handles transactions; explicit BEGIN/COMMIT is rejected.
    sql_path.write_text("\n".join(sql_upsert(r) for r in ordered) + "\n", encoding="utf-8")
    return {"total": len(ordered), "metadata_only": sum(r["rights_status"] == "METADATA_ONLY" for r in ordered),
            "image_rights_verified_pending_editorial_approval":
            sum(r["rights_status"] == "IMAGE_RIGHTS_VERIFIED" for r in ordered),
            "published_by_import": 0}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", choices=("tate", "moma", "verified", "bulk", "wikidata", "all"), default="tate")
    p.add_argument("--max-records", type=int, default=200)
    p.add_argument("--museum", choices=sorted(MUSEUMS), default=None,
                   help="Limit Wikidata acquisition to one verified institution")
    p.add_argument("--jsonl", type=Path, default=Path(".artdrift_ingest/modern_art.jsonl"))
    p.add_argument("--sql", type=Path, default=Path(".artdrift_ingest/modern_art.sql"))
    args = p.parse_args()
    if not 1 <= args.max_records <= 5000:
        p.error("--max-records must be 1..5000")
    if args.museum and args.source in ("tate", "moma", "verified", "bulk"):
        p.error("--museum applies only to wikidata source")
    works: list[dict] = []
    if args.source in ("tate", "bulk", "all"):
        works.extend(collect_tate(args.max_records))
    if args.source in ("moma", "bulk", "all"):
        works.extend(collect_moma(args.max_records))
    if args.source in ("verified", "bulk", "all"):
        works.extend(collect_verified_catalog(args.max_records))
    if args.source in ("wikidata", "all"):
        works.extend(collect_wikidata(args.max_records, args.museum))
    if not works:
        raise SystemExit("FAIL CLOSED: provider returned no eligible source records")
    counts = export(works, args.jsonl, args.sql)
    print(json.dumps({"providers": args.source, **counts}, sort_keys=True))


if __name__ == "__main__":
    main()
