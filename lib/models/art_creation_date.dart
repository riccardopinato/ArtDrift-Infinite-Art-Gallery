/// A deliberately conservative date/media gate for 1950+ Open Access art.
/// The date is the museum's artwork *creation date*, not an acquisition date.
/// Centuries without a four-digit year and ranges crossing 1950 are excluded.
class ArtCreationDate {
  ArtCreationDate._();

  static final RegExp _year = RegExp(
    r'(?<!\d)(?:1[0-9]{3}|20[0-9]{2})(?!\d)',
  );

  static int? explicitYearFrom1950(String date) {
    final years = _year.allMatches(date)
        .map((match) => int.parse(match.group(0)!))
        .toList(growable: false);
    if (years.isEmpty) return null;
    final earliest = years.reduce((a, b) => a < b ? a : b);
    final latest = years.reduce((a, b) => a > b ? a : b);
    if (earliest < 1950 || latest > 2026) return null;
    return earliest;
  }

  /// Artwork types remain precisely described (never mislabeled "painting").
  static bool eligibleModernMedium(String originalType) {
    final kind = originalType.toLowerCase().trim();
    if (kind.isEmpty) return false;
    return const [
      'paint', 'draw', 'print', 'photo', 'sculpt', 'ceramic',
      'textile', 'mixed media', 'poster', 'design', 'graphic',
      'collage', 'assemblage', 'installation',
    ].any(kind.contains);
  }
}
