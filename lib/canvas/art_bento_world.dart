import 'dart:collection';
import 'dart:ui';

import 'package:drift_core/drift_core.dart';
import '../models/artwork.dart';

/// Art-only infinite full-image mosaic. GalleryDrift keeps the shared core.
///
/// A fixed rectangular bento macroblock cannot preserve the native aspect
/// ratio of four arbitrary paintings *and* fill the block: one of those
/// constraints must fail. Instead, adjacent horizontal strips have different
/// heights, with picture widths computed from each original image ratio.
/// The strips cover the world without holes; vertical joints are staggered.
/// No item is cropped, stretched, or substituted.
///
/// Every strip cycles through one of four disjoint color-ranked bands.
/// Adjacent strips offset their 800-image sequence deterministically. Thus
/// a normal viewport and its surrounding regions contain distinct paintings.
/// With finitely many works, remote repetition is unavoidable on an infinite
/// plane; painting identity is always stable when returning to coordinates.
class ArtBentoWorld {
  ArtBentoWorld(this.items, this.scores)
      : _ranked = List<int>.generate(items.length, (i) => i) {
    _ranked.sort((a, b) {
      final score = (scores[items[b].catalogKey] ?? 0)
          .compareTo(scores[items[a].catalogKey] ?? 0);
      return score != 0
          ? score
          : items[a].catalogKey.compareTo(items[b].catalogKey);
    });
  }

  final List<Artwork> items;
  final Map<String, int> scores;
  final List<int> _ranked;

  /// XL receives the top 25% score band, L the next 25%, and so on.
  /// Diverse heights plus variable picture widths create a natural-ratio
  /// editorial mosaic without empty slots or fixed aspect-ratio boxes.
  static const List<double> _heights =
      [260, 350, 215, 395, 285, 340, 230, 385];
  static const List<int> _bands = [2, 1, 3, 0, 2, 1, 3, 0];
  static const double _heightCycle = 2460;

  /// Sparse cache: each row stores one ranked-band cycle of at most 800 widths.
  /// Frames only calculate 4–20 nearby strips, not coordinates from origin.
  final LinkedHashMap<int, _Strip> _cache = LinkedHashMap<int, _Strip>();
  static const int _cacheLimit = 32;

  static int _phase(int row) => row % _heights.length;

  static ({int row, double top, double height}) _atY(double y) {
    final cycle = (y / _heightCycle).floor();
    var top = cycle * _heightCycle;
    final first = cycle * _heights.length;
    for (var i = 0; i < _heights.length; i++) {
      final height = _heights[i];
      if (y < top + height || i == _heights.length - 1) {
        return (row: first + i, top: top, height: height);
      }
      top += height;
    }
    // Every finite coordinate belongs to a strip.
    return (row: first, top: top, height: _heights.first);
  }

  _Strip _strip(int row) {
    final prior = _cache.remove(row);
    if (prior != null) {
      _cache[row] = prior;
      return prior;
    }
    final phase = _phase(row);
    final band = _bands[phase];
    final start = _ranked.length * band ~/ 4;
    final end = _ranked.length * (band + 1) ~/ 4;
    final count = end - start;
    // Non-empty catalogs smaller than four items still render safely.
    final offset = count > 0 ? (row * 89) % count : 0;
    final edges = <double>[0.0];
    if (count > 0) {
      for (var i = 0; i < count; i++) {
        final index = _ranked[start + (offset + i) % count];
        edges.add(edges.last +
            _heights[phase] * items[index].naturalAspectRatio);
      }
    } else if (_ranked.isNotEmpty) {
      edges.add(_heights[phase] *
          items[_ranked[row % _ranked.length]].naturalAspectRatio);
    }
    final value = _Strip(
      row: row, rankStart: start,
      count: count, offset: offset, edges: edges,
    );
    _cache[row] = value;
    if (_cache.length > _cacheLimit) {
      _cache.remove(_cache.keys.first);
    }
    return value;
  }

  /// Lower-bound tile lookup within one completed strip cycle.
  /// O(log N) even after panning millions of pixels in either direction.
  static int _tileAt(List<double> edges, double position) {
    var left = 0, right = edges.length - 1;
    while (left + 1 < right) {
      final middle = (left + right) >> 1;
      if (edges[middle] <= position) {
        left = middle;
      } else {
        right = middle;
      }
    }
    return left;
  }

  int _painting(_Strip strip, int index) {
    if (strip.count == 0) {
      return _ranked[strip.row % _ranked.length];
    }
    return _ranked[
      strip.rankStart + (strip.offset + index) % strip.count
    ];
  }

  /// All positions are in infinite world coordinates, independent of screen,
  /// zoom, pan direction, elapsed time, or route of traversal.
  List<WorldTile> visible(Rect world, int count,
      {int limit = 180, Rect? priorityViewport}) {
    if (world.isEmpty || items.isEmpty || count != items.length ||
        limit <= 0) {
      return const [];
    }
    final result = <WorldTile>[];
    var current = _atY(world.top);
    while (current.top < world.bottom) {
      final strip = _strip(current.row);
      final cycleWidth = strip.edges.last;
      final tileCount = strip.edges.length - 1;
      if (tileCount <= 0 || cycleWidth <= 0) break;

      var repetition = (world.left / cycleWidth).floor();
      var localX = world.left - repetition * cycleWidth;
      // Defensive floating-point correction at huge negative coordinates.
      if (localX < 0) {
        repetition--;
        localX += cycleWidth;
      } else if (localX >= cycleWidth) {
        repetition++;
        localX -= cycleWidth;
      }
      var slot = _tileAt(strip.edges, localX);
      var x = repetition * cycleWidth + strip.edges[slot];

      while (x < world.right) {
        final next = repetition * cycleWidth + strip.edges[slot + 1];
        final rect = Rect.fromLTRB(
            x, current.top, next, current.top + current.height);
        if (rect.overlaps(world)) {
          result.add(WorldTile(
            column: repetition * tileCount + slot,
            row: current.row,
            rect: rect,
            artworkIndex: _painting(strip, slot),
          ));
          if (priorityViewport == null && result.length >= limit) {
            return result;
          }
        }
        slot++;
        if (slot == tileCount) {
          slot = 0;
          repetition++;
        }
        x = repetition * cycleWidth + strip.edges[slot];
      }

      final newRow = current.row + 1;
      current = (
        row: newRow,
        top: current.top + current.height,
        height: _heights[_phase(newRow)],
      );
    }

    if (priorityViewport != null && result.length > limit) {
      final center = priorityViewport.center;
      result.sort((a, b) {
        final inA = a.rect.overlaps(priorityViewport) ? 0 : 1;
        final inB = b.rect.overlaps(priorityViewport) ? 0 : 1;
        if (inA != inB) return inA.compareTo(inB);
        final d = (a.rect.center - center).distanceSquared.compareTo(
            (b.rect.center - center).distanceSquared);
        return d != 0 ? d : a.key.compareTo(b.key);
      });
      return result.take(limit).toList(growable: false);
    }
    return result;
  }
}

class _Strip {
  const _Strip({
    required this.row,
    required this.rankStart,
    required this.count,
    required this.offset,
    required this.edges,
  });
  final int row, rankStart, count, offset;
  final List<double> edges;
}
