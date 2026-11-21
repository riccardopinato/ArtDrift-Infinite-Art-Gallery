import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/artwork.dart';

/// Source-specific Open Access painting bundle. Does not own or alter
/// Drift Core canvas/camera/search/billing; data is handed to existing UI.
/// Only a small set of WebP previews ships with the Android application.
class MuseumCatalog {
  const MuseumCatalog();

  Future<List<Artwork>> bundled({AssetBundle? bundle}) async {
    try {
      final text = await (bundle ?? rootBundle)
          .loadString('assets/museums/catalog.json');
      final source = jsonDecode(text);
      if (source is! List) return const [];
      final unique = <String, Artwork>{};
      for (final item in source) {
        if (item is! Map<String, dynamic>) continue;
        final artwork = Artwork.fromJson(item);
        // Never fall back to unlicensed records, arbitrary image URLs,
        // broken paths, or non-paintings.
        if (!artwork.displayable || !artwork.hasBundledPreview ||
            artwork.museumName.trim().isEmpty ||
            artwork.museumNativeId.trim().isEmpty ||
            artwork.rightsEvidenceUrl.trim().isEmpty) continue;
        final license = artwork.rightsLicense.toLowerCase();
        if (!license.contains('cc0') && !license.contains('public domain')) {
          continue;
        }
        final rights = Uri.tryParse(artwork.rightsEvidenceUrl);
        if (rights == null || rights.scheme != 'https' ||
            rights.userInfo.isNotEmpty) continue;
        unique[artwork.catalogKey] = artwork;
      }
      return List.unmodifiable(unique.values);
    } catch (_) {
      // A missing new asset bundle must NEVER blank the 72-work AIC gallery.
      return const [];
    }
  }

  /// Keep the original 72 bundled works first. This is deterministic,
  /// idempotent and does not mutate user-owned favorites or camera state.
  static List<Artwork> combine(
    Iterable<Artwork> original, Iterable<Artwork> additional) {
    final unique = <String, Artwork>{};
    for (final work in original.followedBy(additional)) {
      if (work.displayable) unique.putIfAbsent(work.catalogKey, () => work);
    }
    return List.unmodifiable(unique.values);
  }
}
