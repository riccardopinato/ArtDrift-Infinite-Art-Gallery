import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/artwork.dart';
import 'art_offline_thumbnail_index.dart';

/// Pins the initial mobile mosaic identity to stable artwork IDs, not the
/// current catalog length. A future update may add local previews without
/// reshuffling every previously visited canvas coordinate.
///
/// Deliberately does not grow an existing pinned playlist automatically:
/// the shared core currently maps tile hashes modulo item count. Appending
/// items here would remap almost every tile. A future shared-core revision
/// can adopt consistent hashing for explicit catalogue expansion.
class ArtMobileCanvasSelection {
  ArtMobileCanvasSelection._();

  static const preferenceKey = 'artdrift.canvas.offline.v1.keys';

  static Future<List<Artwork>> select(List<Artwork> catalog, {
      List<Artwork> initialColorPlaylist = const [],
    }) async {
    if (kIsWeb) return catalog;
    final available = catalog.where((art) => art.hasBundledPreview ||
        ArtOfflineThumbnailIndex.instance.assetFor(art) != null)
        .toList(growable: false);
    if (available.isEmpty) return catalog;

    final prefs = await SharedPreferences.getInstance();
    final pinned = prefs.getStringList(preferenceKey);
    if (pinned == null || pinned.isEmpty) {
      final byKey = {for (final art in available) art.catalogKey: art};
      final curated = <Artwork>[];
      for (final art in initialColorPlaylist) {
        final backed = byKey[art.catalogKey];
        if (backed != null) curated.add(backed);
      }
      final initial = curated.length >= 300 ? curated : available;
      await prefs.setStringList(preferenceKey,
          initial.map((art) => art.catalogKey).toList(growable: false));
      return List.unmodifiable(initial);
    }

    final byKey = {for (final art in available) art.catalogKey: art};
    final selected = <Artwork>[];
    final visited = <String>{};
    for (final key in pinned) {
      final item = byKey[key];
      if (item != null && visited.add(key)) selected.add(item);
    }
    if (selected.isNotEmpty) return List.unmodifiable(selected);

    // The entire previously pinned content pack is no longer present.
    // Recover to still-available real thumbnails rather than an empty canvas.
    await prefs.setStringList(preferenceKey,
        available.map((art) => art.catalogKey).toList(growable: false));
    return available;
  }
}
