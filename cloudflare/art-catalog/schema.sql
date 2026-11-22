-- CC0 metadata only. MoMA image rights are NOT provided by dataset.
CREATE TABLE IF NOT EXISTS works (
  id INTEGER PRIMARY KEY, title TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '',
  date_display TEXT NOT NULL DEFAULT '', medium TEXT NOT NULL DEFAULT '',
  dimensions TEXT NOT NULL DEFAULT '', classification TEXT NOT NULL DEFAULT '',
  department TEXT NOT NULL DEFAULT '', work_url TEXT NOT NULL,
  image_key TEXT, rights_license TEXT, rights_evidence_url TEXT
);
CREATE INDEX IF NOT EXISTS idx_works_artist ON works(artist);
CREATE INDEX IF NOT EXISTS idx_works_title ON works(title);
CREATE VIRTUAL TABLE IF NOT EXISTS works_fts USING fts5(
  title, artist, medium, classification,
  tokenize = 'unicode61 remove_diacritics 2'
);
