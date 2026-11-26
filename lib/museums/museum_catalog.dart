import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/artwork.dart';

/// An immutable, source-traceable museum catalog; no changes to Drift Core.
/// First tier contains WebP previews (available offline), second tier is an
/// extensive metadata index with low-resolution previews fetched when visible.
/// A broken optional catalog never removes the original paintings.
class MuseumCatalog {
  const MuseumCatalog();

  Future<List<Artwork>> bundled({AssetBundle? bundle}) async {
    final source = bundle ?? rootBundle;
    final unique = <String, Artwork>{};
    for (final file in <String>[
      'assets/museums/catalog.json',
      'assets/museums/catalog_global.json',
      // Intentionally empty until per-image provenance and rights approval.
      'assets/museums/catalog_curated_commons.json',
    ]) {
      final isPreviewPack = file.endsWith('/catalog.json');
      try {
        final decoded = jsonDecode(await source.loadString(file));
        if (decoded is! List) continue;
        for (final item in decoded) {
          if (item is! Map<String, dynamic>) continue;
          final artwork = Artwork.fromJson(item);
          if (!artwork.displayable ||
              artwork.museumName.trim().isEmpty ||
              artwork.museumNativeId.trim().isEmpty ||
              artwork.rightsEvidenceUrl.trim().isEmpty) continue;
          final license = artwork.rightsLicense.toLowerCase();
          if (artwork.isCuratedCommons) {
            // CC BY / BY-SA are distinct from public domain. They require
            // independently reviewed image credits and worldwide rights.
            if (!artwork.curatedCommonsReleaseReady) continue;
          } else if (!license.contains('cc0') &&
              !license.contains('public domain')) {
            continue;
          }
          final rights = Uri.tryParse(artwork.rightsEvidenceUrl);
          if (rights == null || rights.scheme != 'https' ||
              rights.userInfo.isNotEmpty ||
              (rights.hasPort && rights.port != 443)) continue;
          // A metadata-only entry MUST NOT claim a packaged WebP exists.
          if (isPreviewPack && !artwork.hasBundledPreview) continue;
          if (!isPreviewPack && artwork.bootstrapAsset.isNotEmpty) continue;
          unique.putIfAbsent(artwork.catalogKey, () => artwork);
        }
      } catch (_) {
        // Fail this pack closed, not the entire already-readable collection.
      }
    }
    return List.unmodifiable(unique.values);
  }

  /// Preserve 72 original local AIC records and stable museum identity.
  static List<Artwork> combine(
      Iterable<Artwork> original, Iterable<Artwork> additional) {
    final unique = <String, Artwork>{};
    for (final work in original.followedBy(additional)) {
      if (work.displayable) unique.putIfAbsent(work.catalogKey, () => work);
    }
    return List.unmodifiable(unique.values);
  }
}
