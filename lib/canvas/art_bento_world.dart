import 'dart:math' as math;
import 'dart:ui';

import 'package:drift_core/drift_core.dart';
import '../models/artwork.dart';

/// Gapless, infinite Art-only jigsaw. GalleryDrift retains its original core.
///
/// Each 450x450 macroblock contains four non-overlapping S/M/L/XL rectangles
/// that tessellate the complete 3x3 cell grid. The tile gutters are zero.
///
/// Worldwide unique paintings on an infinite plane with a finite catalog
/// are mathematically impossible. For the normal 3,200-item playlist, four
/// disjoint 800-image score bands map to a stable 2-D sequence: no painting
/// repeats in any 12x12 neighboring macroblock window. Distant regions
/// reuse images only after a much larger amount of exploration.
class ArtBentoWorld {
  ArtBentoWorld(this.items, this.scores)
      : _ranked = List<int>.generate(items.length, (i) => i) {
    _ranked.sort((a, b) {
      final diff = _quality(items[b]).compareTo(_quality(items[a]));
      return diff != 0
          ? diff
          : items[a].catalogKey.compareTo(items[b].catalogKey);
    });
  }

  final List<Artwork> items;
  final Map<String, int> scores;
  final List<int> _ranked;
  static const double cell = 150, block = 450;

  static final _scenery = RegExp(
    r'landscape|paesagg|paysage|seascape|sea\b|coast|garden|giardin|'
    r'flower|fiori|fleur|blossom|lake|river|mountain|forest|sunset|'
    r'water lilies|meadow|sky|harbor|village|spring',
    caseSensitive: false);
  static final _portrait = RegExp(
    r'portrait|ritratto|portr[aä]t|bust of|head of|autoritratto',
    caseSensitive: false);

  double _quality(Artwork art) {
    final labels = art.title + ' ' + art.subjectTerms.join(' ');
    return (scores[art.catalogKey] ?? 0).toDouble() +
        (_scenery.hasMatch(labels) ? 14 : 0) -
        (_portrait.hasMatch(art.title) ? 22 : 0);
  }

  // Every pattern contains precisely four pieces covering all nine 150px
  // cells. Unlike the old layout there are no three- or six-piece templates.
  static const List<List<_Cell>> _patterns = [
    [_Cell(0, 0, 2, 2), _Cell(2, 0, 1, 2),
     _Cell(0, 2, 1, 1), _Cell(1, 2, 2, 1)],
    [_Cell(0, 0, 3, 2), _Cell(0, 2, 1, 1),
     _Cell(1, 2, 1, 1), _Cell(2, 2, 1, 1)],
    [_Cell(0, 0, 1, 2), _Cell(1, 0, 2, 1),
     _Cell(1, 1, 2, 2), _Cell(0, 2, 1, 1)],
    [_Cell(0, 0, 1, 1), _Cell(1, 0, 2, 2),
     _Cell(0, 1, 1, 2), _Cell(1, 2, 2, 1)],
    [_Cell(0, 0, 2, 2), _Cell(2, 0, 1, 1),
     _Cell(2, 1, 1, 2), _Cell(0, 2, 2, 1)],
    [_Cell(0, 0, 2, 3), _Cell(2, 0, 1, 1),
     _Cell(2, 1, 1, 1), _Cell(2, 2, 1, 1)],
  ];

  /// Browser-safe coordinate permutation with deterministic negative axes.
  /// For a band of 800, the step is 29 and the horizontal period is 800.
  static int _cycle(int x, int y, int span) {
    if (span <= 1) return 0;
    final stride = math.sqrt(span).floor() | 1;
    var index = (x + y * stride) % span;
    if (index < 0) index += span;
    return index;
  }

  /// Select four unique works independently of the chosen puzzle geometry.
  /// Each image comes from a separate color-ranked quarter of the playlist.
  List<int> _bandSelection(int x, int y) {
    final count = _ranked.length;
    final result = <int>[];
    for (var band = 0; band < 4; band++) {
      final begin = count * band ~/ 4;
      final end = count * (band + 1) ~/ 4;
      final span = end - begin;
      result.add(span > 0
          ? _ranked[begin + _cycle(x, y, span)]
          : _ranked[(band + _cycle(x, y, count)) % count]);
    }
    return result;
  }

  /// Choose a gapless puzzle arrangement by comparing the actual source
  /// artwork aspect ratios to each of six full-coverage templates. The
  /// most colorful work always owns the largest tile. Slight layout-rhythm
  /// variation avoids monotonous repeated macroblock shapes, without
  /// overriding a strong source/image aspect-ratio mismatch.
  ({List<_Cell> shapes, List<int> indices}) _layout(int x, int y) {
    final paintings = _bandSelection(x, y);
    var bestScore = double.negativeInfinity;
    late List<_Cell> chosenShapes;
    late List<int> chosenIndices;

    for (var pattern = 0; pattern < _patterns.length; pattern++) {
      final shapes = _patterns[pattern];
      final sortedSlots = [0, 1, 2, 3]..sort((a, b) {
        final diff = shapes[b].area.compareTo(shapes[a].area);
        return diff != 0 ? diff : a.compareTo(b);
      });
      final indices = List<int>.filled(4, 0);
      var score = 0.0;
      var heroFit = 0.0;
      for (var band = 0; band < 4; band++) {
        final slot = sortedSlots[band];
        final shape = shapes[slot];
        final targetAspect = shape.w / shape.h;
        final imageAspect = items[paintings[band]].naturalAspectRatio;
        final retained = math.min(
            imageAspect / targetAspect, targetAspect / imageAspect);
        score += shape.area * retained;
        if (band == 0) heroFit = retained;
        indices[slot] = paintings[band];
      }

      // For broadly compatible images, allow more compact 2x2 hero frames
      // to add visual rhythm without sacrificing image coverage excessively.
      if (shapes[sortedSlots.first].area == 4 && heroFit >= 0.7) {
        score += 1.4;
      }
      var tie = (x * 17 + y * 11 + pattern * 13) % 11;
      if (tie < 0) tie += 11;
      score += tie * 0.08;

      if (score > bestScore) {
        bestScore = score;
        chosenShapes = shapes;
        chosenIndices = indices;
      }
    }
    return (shapes: chosenShapes, indices: chosenIndices);
  }

  /// Stateless: same world position always yields the same painting and rect.
  /// Infinite panning, prefetch and recenter remain bounded and deterministic.
  List<WorldTile> visible(Rect world, int count,
      {int limit = 180, Rect? priorityViewport}) {
    if (world.isEmpty || count <= 0 || count != items.length || limit <= 0) {
      return const [];
    }
    final output = <WorldTile>[];
    final left = (world.left / block).floor();
    final right = (world.right / block).floor();
    final top = (world.top / block).floor();
    final bottom = (world.bottom / block).floor();
    for (var x = left; x <= right; x++) {
      for (var y = top; y <= bottom; y++) {
        final selected = _layout(x, y);
        final shapes = selected.shapes;
        final indices = selected.indices;
        for (var slot = 0; slot < shapes.length; slot++) {
          final shape = shapes[slot];
          final rect = Rect.fromLTWH(
            x * block + shape.x * cell,
            y * block + shape.y * cell,
            shape.w * cell,
            shape.h * cell,
          );
          if (!rect.overlaps(world)) continue;
          output.add(WorldTile(
            column: x, row: y * 8 + slot, rect: rect,
            artworkIndex: indices[slot]));
          if (priorityViewport == null && output.length >= limit) {
            return output;
          }
        }
      }
    }
    if (priorityViewport != null && output.length > limit) {
      final focus = priorityViewport.center;
      output.sort((a, b) {
        final aOnScreen = a.rect.overlaps(priorityViewport) ? 0 : 1;
        final bOnScreen = b.rect.overlaps(priorityViewport) ? 0 : 1;
        if (aOnScreen != bOnScreen) return aOnScreen.compareTo(bOnScreen);
        final delta = (a.rect.center - focus).distanceSquared.compareTo(
          (b.rect.center - focus).distanceSquared);
        return delta != 0 ? delta : a.key.compareTo(b.key);
      });
      return output.take(limit).toList(growable: false);
    }
    return output;
  }
}

class _Cell {
  const _Cell(this.x, this.y, this.w, this.h);
  final int x, y, w, h;
  int get area => w * h;
}
