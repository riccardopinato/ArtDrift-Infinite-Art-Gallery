import 'dart:math' as math;
import 'dart:ui';

import 'package:drift_core/drift_core.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/artwork.dart';
import 'art_offline_thumbnail_index.dart';

/// Chooses a world camera destination without reordering or renaming art.
/// It is never invoked unless a user explicitly enabled its preference.
abstract final class ArtJoyfulStart {
  static const enabledKey = 'artdrift.discovery.random_start.v1';
  static const _lastX = 'artdrift.discovery.last.x';
  static const _lastY = 'artdrift.discovery.last.y';

  static final _landscape = RegExp(
    r'landscape|paesagg|paysage|landschaft|seascape|marine|'
    r'garden|giardin|flower|fleur|marin|river|sea\b|lake|'
    r'mountain|forest|valley|sky|meadow|sunset',
    caseSensitive: false);
  static final _portrait = RegExp(
    r'portrait|ritratto|retrato|porträt|self.portrait',
    caseSensitive: false);

  static Offset choose(List<Artwork> artworks, {
    required Size viewport,
    math.Random? random,
    Offset? previous,
    bool Function(Artwork)? imageAvailable,
  }) {
    if (artworks.isEmpty) return Offset.zero;
    final rng = random ?? math.Random();
    final hasImage = imageAvailable ??
      (Artwork art) => art.hasBundledPreview ||
          ArtOfflineThumbnailIndex.instance.has(art);
    final width = viewport.width.clamp(320.0, 1600.0).toDouble();
    final height = viewport.height.clamp(450.0, 1200.0).toDouble();
    final world = const InfiniteWorld();
    final selections = <({Offset center, double score})>[];
    final used = <String>{};

    for (var i = 0; i < 96; i++) {
      final col = rng.nextInt(91) - 45;
      final row = rng.nextInt(91) - 45;
      final center = Offset(col * 426.0, row * 270.0);
      if (center.distanceSquared < 1100.0 * 1100.0 ||
          previous != null &&
            (center - previous).distanceSquared < 1100.0 * 1100.0 ||
          !used.add('$col:$row')) continue;
      final view = Rect.fromCenter(center: center, width: width,
        height: height);
      final tiles = world.visible(view, artworks.length,
        limit: 100, priorityViewport: view);
      if (tiles.isEmpty) continue;
      var total = 0.0;
      var count = 0;
      final unique = <int>{};
      for (final tile in tiles) {
        if (!unique.add(tile.artworkIndex) || !tile.rect.overlaps(view)) continue;
        final art = artworks[tile.artworkIndex];
        total += hasImage(art) ? 5 : -30;
        final name = '${art.title} ${art.subjectTerms.join(' ')}';
        if (_landscape.hasMatch(name)) total += 4;
        if (_portrait.hasMatch(art.title)) total -= 3;
        count++;
      }
      if (count > 0) selections.add((
        center: center,
        score: total / count + rng.nextDouble() * 0.3,
      ));
    }
    if (selections.isEmpty) {
      return (previous ?? Offset.zero) + const Offset(1278, 1620);
    }
    selections.sort((a,b) => b.score.compareTo(a.score));
    return selections[rng.nextInt(math.min(3, selections.length))].center;
  }

  static Future<Offset> chooseForLaunch(List<Artwork> artworks, {
    required Size viewport, math.Random? random,
  }) async {
    SharedPreferences? prefs;
    Offset? previous;
    try {
      prefs = await SharedPreferences.getInstance();
      final x = prefs.getDouble(_lastX), y = prefs.getDouble(_lastY);
      if (x != null && y != null && x.isFinite && y.isFinite) {
        previous = Offset(x, y);
      }
    } catch (_) {}
    final selected = choose(artworks,
      viewport: viewport, random: random, previous: previous);
    try {
      if (prefs != null) {
        await prefs.setDouble(_lastX, selected.dx);
        await prefs.setDouble(_lastY, selected.dy);
      }
    } catch (_) {}
    return selected;
  }
}
