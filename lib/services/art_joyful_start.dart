import 'dart:math' as math;
import 'dart:ui';

import 'package:drift_core/drift_core.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/artwork.dart';
import 'art_offline_thumbnail_index.dart';

/// Art-only discovery entry points. The InfiniteWorld hash/ID order is NEVER
/// modified; this only decides which immutable coordinates are initially seen.
class ArtJoyfulStart {
  ArtJoyfulStart._();

  static const _prefX = 'artdrift.discovery.last.x';
  static const _prefY = 'artdrift.discovery.last.y';
  static const _radius = 1100.0;
  static final _landscape = RegExp(
    r'landscape|paesagg|paysage|landschaft|seascape|marin|sea\b|ocean|'
    r'coast|beach|shore|lake|river|mountain|hill|forest|woodland|'
    r'waterfall|water lilies|waterlilies|garden|giardin|park|countryside|'
    r'meadow|field|sunset|sunrise|sky|cielo|cloud|fjord|valley|view of|'
    r'village|countryside|harbor|harbour|citt[aà]|cityscape',
    caseSensitive: false,
  );
  static final _floral = RegExp(
    r'flower|fiori|fleur|blossom|botanical|spring|primavera|summer|estate',
    caseSensitive: false,
  );
  static final _portrait = RegExp(
    r'portrait|ritratto|portr[aä]t|self.portrait|bust of|head of|'
    r'portrait of|autoritratto',
    caseSensitive: false,
  );
  static final _modern = RegExp(r'18[8-9]\d|19\d\d|20\d\d');

  /// Pure, seeded/testable decision. Samples multiple distant world regions
  /// and chooses among the best with real thumbnails and inviting metadata.
  /// Never changes the source IDs or substitutes images.
  static Offset choose(
    List<Artwork> items, {
    required Size viewport,
    math.Random? random,
    Offset? previous,
    bool Function(Artwork)? hasImage,
    int candidates = 96,
    Map<String,int> pixelScores = const {},
  }) {
    if (items.isEmpty) return Offset.zero;
    final rng = random ?? math.Random();
    final source = hasImage ?? (art) =>
      art.hasBundledPreview || ArtOfflineThumbnailIndex.instance.has(art);
    final w = viewport.width.clamp(320.0, 1600.0).toDouble();
    final h = viewport.height.clamp(450.0, 1200.0).toDouble();
    final world = const InfiniteWorld();
    final scored = <({Offset center, double score})>[];
    final checked = <String>{};
    for (var i = 0; i < candidates; i++) {
      final column = rng.nextInt(91) - 45;
      final band = rng.nextInt(91) - 45;
      final location = Offset(column * 426.0, band * 270.0);
      if (location.distanceSquared < _radius * _radius ||
          (previous != null &&
           (location - previous).distanceSquared < _radius * _radius) ||
          !checked.add('$column:$band')) continue;
      final view = Rect.fromCenter(center: location, width: w, height: h);
      final tiles = world.visible(view, items.length,
          limit: 100, priorityViewport: view);
      if (tiles.isEmpty) continue;
      var score = 0.0;
      var landscapes = 0;
      final unique = <int>{};
      for (final tile in tiles) {
        if (!tile.rect.overlaps(view) || !unique.add(tile.artworkIndex)) continue;
        final art = items[tile.artworkIndex];
        final text = '${art.title} ${art.subjectTerms.join(' ')}';
        if (source(art)) {
          final measured = pixelScores[art.catalogKey];
          // The photographed pixels outrank title-only classifications.
          // Low-saturation / dark tiles should not dominate the first view.
          if (measured == null) {
            score += 2;
          } else {
            score += 2 + measured / 255.0 * 36;
            if (measured < 50) score -= 8;
          }
        } else {
          score -= 24;
        }
        if (_landscape.hasMatch(text)) { score += 4; landscapes++; }
        if (_floral.hasMatch(text)) score += 4;
        if (_portrait.hasMatch(art.title)) score -= 6;
        if (_modern.hasMatch(art.date)) score += 1.5;
      }
      if (unique.isNotEmpty) {
        score = score / unique.length + landscapes * 0.45 +
            rng.nextDouble() * 0.3;
        scored.add((center: location, score: score));
      }
    }
    if (scored.isEmpty) {
      // Deterministic fallback, still different from the previous launch.
      return (previous ?? Offset.zero) + const Offset(1278, 1620);
    }
    scored.sort((a, b) => b.score.compareTo(a.score));
    final best = math.min(3, scored.length);
    return scored[rng.nextInt(best)].center;
  }

  static Future<Offset> chooseForLaunch(List<Artwork> artworks, {
    required Size viewport,
    math.Random? random,
    Map<String,int> pixelScores = const {},
  }) async {
    SharedPreferences? prefs;
    Offset? previous;
    try {
      prefs = await SharedPreferences.getInstance();
      final x = prefs.getDouble(_prefX);
      final y = prefs.getDouble(_prefY);
      if (x != null && y != null && x.isFinite && y.isFinite) {
        previous = Offset(x, y);
      }
    } catch (_) {
      // Browsing still works without local preferences.
    }
    final choice = choose(artworks, viewport: viewport,
        random: random, previous: previous, pixelScores: pixelScores);
    try {
      if (prefs != null) {
        await prefs.setDouble(_prefX, choice.dx);
        await prefs.setDouble(_prefY, choice.dy);
      }
    } catch (_) {}
    return choice;
  }
}
