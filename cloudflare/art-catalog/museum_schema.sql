-- Art Drift unified museum index. DATA ONLY; no favorites, credentials or images.
-- Run manually on a test D1 after reviewing manifest and Cloudflare quotas.
-- MoMA CC0 metadata-only tables in schema.sql remain separate.
CREATE TABLE IF NOT EXISTS museum_works (
  source_key TEXT PRIMARY KEY NOT NULL,
  museum_source TEXT NOT NULL,
  museum_native_id TEXT NOT NULL,
  museum_name TEXT NOT NULL,
  title TEXT NOT NULL,
  artist TEXT NOT NULL DEFAULT '',
  date_display TEXT NOT NULL DEFAULT '',
  medium TEXT NOT NULL DEFAULT '',
  source_url TEXT,
  image_url TEXT,
  rights_license TEXT NOT NULL,
  rights_evidence_url TEXT NOT NULL,
  credit_line TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_museum_works_institution
  ON museum_works (museum_name);
CREATE INDEX IF NOT EXISTS idx_museum_works_source
  ON museum_works (museum_source);
CREATE VIRTUAL TABLE IF NOT EXISTS museum_works_fts USING fts5(
  title, artist, museum_name, medium,
  content='museum_works', content_rowid='rowid',
  tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS museum_works_ai AFTER INSERT ON museum_works BEGIN
  INSERT INTO museum_works_fts(rowid,title,artist,museum_name,medium)
    VALUES(new.rowid,new.title,new.artist,new.museum_name,new.medium);
END;
-- No destructive operations, no remote deployment, no R2 upload.
