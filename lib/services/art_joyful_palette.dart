import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import '../models/artwork.dart';
import 'art_offline_thumbnail_index.dart';

/// Read-only brightness/chroma scores measured from the 4,499 original WebP
/// thumbnails. Each byte is keyed to the exact sorted canonical catalog IDs.
/// A catalog identity change fails closed, falling back to the previous
/// verified color playlist; this never reuses scores for unrelated paintings.
class ArtJoyfulPalette {
  ArtJoyfulPalette._();
  static const assetPath = 'assets/museums/canvas_joyful_pixel_scores_v2.json';

  static int fingerprint(List<String> keys) {
    var hash = 0x811c9dc5;
    for (final key in keys) {
      for (final byte in utf8.encode('$key\u0000')) {
        hash = ((hash ^ byte) * 0x01000193) & 0xffffffff;
      }
    }
    return hash;
  }

  @visibleForTesting
  static Map<String, int> decode(List<Artwork> catalog, String raw) {
    final parsed = jsonDecode(raw);
    if (parsed is! Map || parsed['schema_version'] != 2 ||
        parsed['catalog_key_count'] != catalog.length ||
        parsed['score_byte_count'] != catalog.length ||
        parsed['commercial_release_cleared'] != false) {
      throw const FormatException('Incorrect joyful image score contract');
    }
    final keys = catalog.map((art) => art.catalogKey).toList()..sort();
    if (keys.length != keys.toSet().length ||
        fingerprint(keys) != parsed['catalog_fingerprint_fnv1a32']) {
      throw const FormatException('Joyful image source-ID mismatch');
    }
    final bytes = base64Decode(parsed['score_bytes_base64'] as String);
    if (bytes.length != keys.length) {
      throw const FormatException('Joyful image score length mismatch');
    }
    return Map.unmodifiable({
      for (var i = 0; i < keys.length; i++) keys[i]: bytes[i],
    });
  }

  static Future<Map<String, int>> load(List<Artwork> catalog) async {
    try {
      return decode(catalog, await rootBundle.loadString(assetPath));
    } catch (error) {
      if (kDebugMode) debugPrint('Joyful source scores unavailable: $error');
      return const {};
    }
  }

  static final _landscape = RegExp(
    r'landscape|paesagg|paysage|landschaft|seascape|marin|sea\b|ocean|'
    r'coast|beach|shore|lake|river|mountain|hill|forest|woodland|'
    r'waterfall|water lilies|waterlilies|garden|giardin|park|'
    r'meadow|field|sunset|sunrise|sky|cielo|cloud|fjord|valley|'
    r'view of|village|harbor|harbour|cityscape',caseSensitive:false);
  static final _flowers = RegExp(
    r'flower|fiori|fleur|blossom|botanical|spring|primavera|summer|estate',
    caseSensitive:false);
  static final _portrait = RegExp(
    r'portrait|ritratto|portr[aä]t|self.portrait|bust of|head of|autoritratto',
    caseSensitive:false);
  static final _modern = RegExp(r'18[8-9]\d|19\d\d|20\d\d');

  /// The "modern" term denotes a period-based heuristic, not a claim of
  /// post-1950 copyright clearance. Only real image-backed works may enter.
  static List<Artwork> select(List<Artwork> catalog,
      Map<String,int> scores) {
    if (scores.length != catalog.length || catalog.length < 2400) {
      return const [];
    }
    final candidates = catalog.where((art) =>
      art.displayable && (art.hasBundledPreview ||
        ArtOfflineThumbnailIndex.instance.has(art))).toList();
    if (candidates.length < 2400) return const [];
    double quality(Artwork art) {
      final text = '${art.title} ${art.subjectTerms.join(' ')}';
      return (scores[art.catalogKey] ?? 0) / 255.0 +
        (_landscape.hasMatch(text) ? .07 : 0) +
        (_flowers.hasMatch(text) ? .07 : 0) +
        (_modern.hasMatch(art.date) ? .085 : 0) -
        (_portrait.hasMatch(art.title) ? .11 : 0);
    }
    candidates.sort((a,b) {
      final diff = quality(b).compareTo(quality(a));
      return diff != 0 ? diff : a.catalogKey.compareTo(b.catalogKey);
    });
    return List.unmodifiable(candidates.take(2400));
  }
}
