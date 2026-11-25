import 'package:shared_preferences/shared_preferences.dart';

import '../models/artwork.dart';
import 'art_offline_thumbnail_index.dart';

/// Stable native/Web selection. The canonical canvas hashes tile coordinates by
/// list length, so old installs MUST preserve their original ordered IDs.
class ArtMobileCanvasSelection {
  ArtMobileCanvasSelection._();

  static const preferenceKey = 'artdrift.canvas.offline.v1.keys';

  static Future<List<Artwork>> select(List<Artwork> catalog, {
    List<Artwork> initialColorPlaylist = const [],
  }) async {
    if (catalog.isEmpty) return catalog;
    final prefs = await SharedPreferences.getInstance();
    final byKey = {for (final art in catalog) art.catalogKey: art};
    final saved = prefs.getStringList(preferenceKey);
    if (saved != null && saved.isNotEmpty) {
      final seen = <String>{};
      final pinned = <Artwork>[];
      for (final id in saved) {
        final artwork = byKey[id];
        if (artwork != null && seen.add(id)) pinned.add(artwork);
      }
      if (pinned.isNotEmpty) return List.unmodifiable(pinned);
    }

    // Legacy 0.3.5 users have persisted camera coordinates but never stored a
    // source-ID playlist. Preserve the full exact list, including any one
    // metadata-only tile, rather than silently remapping almost every tile.
    const cameraKey = 'artdrift.camera';
    final legacyCamera = prefs.containsKey('$cameraKey.x') ||
        prefs.containsKey('$cameraKey.y') ||
        prefs.containsKey('$cameraKey.zoom');
    if (legacyCamera) {
      await prefs.setStringList(preferenceKey,
          catalog.map((art) => art.catalogKey).toList(growable: false));
      return List.unmodifiable(catalog);
    }

    // Only fresh installations receive the artwork-backed color-first seed.
    final available = catalog.where((art) => art.hasBundledPreview ||
        ArtOfflineThumbnailIndex.instance.has(art))
        .toList(growable: false);
    final availableByKey = {for (final art in available) art.catalogKey: art};
    final curated = <Artwork>[];
    final seen = <String>{};
    for (final art in initialColorPlaylist) {
      final backed = availableByKey[art.catalogKey];
      if (backed != null && seen.add(art.catalogKey)) curated.add(backed);
    }
    final first = curated.length >= 300 ? curated :
        (available.isNotEmpty ? available : catalog);
    await prefs.setStringList(preferenceKey,
        first.map((art) => art.catalogKey).toList(growable: false));
    return List.unmodifiable(first);
  }
}
