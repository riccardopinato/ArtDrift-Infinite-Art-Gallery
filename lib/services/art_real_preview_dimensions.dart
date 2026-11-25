import 'dart:convert';

import 'package:flutter/services.dart';

import '../models/artwork.dart';
import 'art_joyful_palette.dart';

/// The exact pixel width/height of the bundled WebP bytes, measured directly
/// from RIFF headers at build time. Museum API metadata is not authoritative
/// for preview dimensions (many museums report a different thumbnail crop).
///
/// Fully offline, platform-neutral, source-ID pinned, no image decoding and
/// no requests to third-party servers. When provenance changes, fail closed.
class ArtRealPreviewDimensions {
  ArtRealPreviewDimensions._();

  static const assetPath =
      'assets/museums/canvas_real_webp_dimensions_v1.json';
  static const expectedCount = 4500;
  static const expectedFingerprint = 2742452096;

  static Future<Map<String, double>> load(List<Artwork> catalog) async {
    if (catalog.length != expectedCount) return const {};
    try {
      final raw = await rootBundle.loadString(assetPath);
      return decode(catalog, raw);
    } catch (_) {
      return const {};
    }
  }

  /// Also used by the asset-integrity regression tests.
  static Map<String, double> decode(
      List<Artwork> catalog, String raw) {
    if (catalog.length != expectedCount) return const {};
    try {
      final data = jsonDecode(raw);
      if (data is! Map ||
          data['schema_version'] != 1 ||
          data['catalog_key_count'] != expectedCount ||
          data['catalog_fingerprint_fnv1a32'] != expectedFingerprint ||
          data['dimensions_base64'] is! String) return const {};
      final sorted = catalog.map((a) => a.catalogKey).toList()..sort();
      if (sorted.toSet().length != expectedCount ||
          ArtJoyfulPalette.fingerprint(sorted) != expectedFingerprint) {
        return const {};
      }
      final bytes = base64Decode(data['dimensions_base64'] as String);
      if (bytes.length != expectedCount * 4) return const {};
      final result = <String, double>{};
      for (var i = 0; i < sorted.length; i++) {
        final p = i * 4;
        final width = (bytes[p] << 8) | bytes[p + 1];
        final height = (bytes[p + 2] << 8) | bytes[p + 3];
        if (width > 0 && height > 0) {
          result[sorted[i]] = width / height;
        }
      }
      if (result.length != data['available_preview_count'] ||
          result.length < 4400) return const {};
      return Map.unmodifiable(result);
    } catch (_) {
      return const {};
    }
  }
}
