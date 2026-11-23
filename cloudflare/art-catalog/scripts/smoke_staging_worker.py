#!/usr/bin/env python3
"""Read-only smoke test against the owner's deployed Art Drift staging Worker.

No auth tokens, no D1 writes, no image downloading, no production deploy.
All checks go through Workers.dev and prove live binding and FTS search.
"""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ORIGIN = "https://artdrift-catalog-staging.riccardopinato.workers.dev"
EXPECTED = 5084

def fetch(path, expected=200):
    last=None
    for retry in range(6):
        try:
            request=Request(ORIGIN + path,headers={
                "User-Agent":"ArtDrift-Worker-Staging-Smoke/1.0 (GitHub Actions)",
                "Accept":"application/json",
            })
            with urlopen(request,timeout=17) as response:
                if response.status!=expected:
                    raise RuntimeError(f"HTTP {response.status} instead of {expected} for {path}")
                raw=response.read(500_001)
                if len(raw)>500_000:
                    raise RuntimeError("Oversized Worker JSON response")
                data=json.loads(raw)
                if not isinstance(data,dict):
                    raise RuntimeError("Malformed Worker response")
                return data
        except HTTPError as e:
            if e.code==expected:
                return json.loads(e.read(500_001))
            last=RuntimeError(f"HTTP {e.code}: {path}; {e.read(900)!r}")
            if e.code not in (429,503,502,504):
                raise last
        except (URLError,TimeoutError) as e:
            last=e
        if retry<5:
            time.sleep(2+retry*2)
    raise RuntimeError(f"Staging unavailable after six requests: {path}: {last}")

def main():
    health=fetch("/health")
    if health.get("status") not in ("configured","ready"):
        raise RuntimeError("Unexpected Worker health response")
    print("STAGING_HEALTH_PASS",health.get("status"),flush=True)

    listings=fetch("/api/v1/museums")
    if listings.get("source")!="ArtDrift-Museums":
        raise RuntimeError("Incorrect Worker museum source")
    institutions=listings.get("institutions")
    if not isinstance(institutions,list) or not institutions:
        raise RuntimeError("No museum institutions in remote D1")
    if any(type(item.get("works")) is not int or item["works"]<1
           or not item.get("museum_name")
           for item in institutions):
        raise RuntimeError("Malformed museum institution counts")
    total=sum(item["works"] for item in institutions)
    if total!=EXPECTED:
        raise RuntimeError(f"Remote D1 count discrepancy: {total} vs {EXPECTED}")
    print("STAGING_MUSEUMS_PASS",len(institutions),"institutions",total,"works",flush=True)

    query=urlencode({"q":"painting","scope":"all","cursor":"0"})
    page=fetch("/api/v1/museum-search?"+query)
    if page.get("source")!="ArtDrift-Museums":
        raise RuntimeError("Wrong search source")
    rows=page.get("works")
    if not isinstance(rows,list) or not 1<=len(rows)<=24:
        raise RuntimeError("Remote D1 FTS search returned no works or too many")
    if any(not isinstance(row,dict) or not row.get("source_key") or
           not row.get("museum_name") or not row.get("rights_license")
           or not row.get("rights_evidence_url")
           for row in rows):
        raise RuntimeError("Works lack source identity or license evidence")
    if len({r["source_key"] for r in rows})!=len(rows):
        raise RuntimeError("Duplicate works in one search page")
    print("STAGING_SEARCH_PASS",len(rows),"works, cursor",page.get("next_cursor"),flush=True)

    invalid=fetch("/api/v1/museum-search?q=x",expected=400)
    if invalid.get("error")!="bad_query":
        raise RuntimeError("Search validation gate failed")
    print("STAGING_VALIDATION_PASS",flush=True)
    print("ARTDRIFT_STAGING_WORKER_E2E_PASS 5084 indexed museum works; "
          "read-only HTTP and FTS validated",flush=True)

if __name__=="__main__":
    main()
