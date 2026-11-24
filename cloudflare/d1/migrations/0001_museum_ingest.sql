-- Art Drift D1: independent museum staging; never replace the Flutter bundle or user favorites.
-- Apply once to an EXISTING D1 instance using Wrangler. No media bytes are stored.
CREATE TABLE IF NOT EXISTS artdrift_museum_ingest (
  source_key TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  native_id TEXT NOT NULL,
  museum TEXT NOT NULL,
  title TEXT NOT NULL,
  artist TEXT NOT NULL DEFAULT '',
  year_text TEXT NOT NULL DEFAULT '',
  medium TEXT NOT NULL DEFAULT '',
  metadata_url TEXT NOT NULL,
  image_url TEXT NOT NULL DEFAULT '',
  full_image_url TEXT NOT NULL DEFAULT '',
  rights_license TEXT NOT NULL DEFAULT '',
  rights_evidence_url TEXT NOT NULL DEFAULT '',
  rights_status TEXT NOT NULL CHECK(rights_status IN ('METADATA_ONLY','IMAGE_REVIEW','IMAGE_RIGHTS_VERIFIED')),
  fingerprint TEXT NOT NULL,
  publication_status TEXT NOT NULL DEFAULT 'HOLD' CHECK(publication_status IN ('HOLD','APPROVED','REJECTED')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(provider, native_id)
);
CREATE INDEX IF NOT EXISTS artdrift_museum_ingest_artist_idx ON artdrift_museum_ingest(artist);
CREATE INDEX IF NOT EXISTS artdrift_museum_ingest_review_idx ON artdrift_museum_ingest(publication_status, rights_status);
CREATE VIEW IF NOT EXISTS artdrift_publishable_modern_art AS
SELECT source_key, provider, native_id, museum, title, artist, year_text, medium,
       metadata_url, image_url, full_image_url, rights_license, rights_evidence_url, fingerprint
FROM artdrift_museum_ingest
WHERE publication_status = 'APPROVED'
  AND rights_status = 'IMAGE_RIGHTS_VERIFIED'
  AND image_url != '' AND full_image_url != ''
  AND rights_evidence_url != '';
