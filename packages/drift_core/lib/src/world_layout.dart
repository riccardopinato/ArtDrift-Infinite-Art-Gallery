import 'dart:ui';

/// Stable virtual coordinates. No giant Stack; visible tiles are computed from
/// the viewport only, independent of how far the user has panned.
class WorldTile {
  const WorldTile({required this.column, required this.row,
    required this.rect, required this.artworkIndex});
  final int column;
  final int row;
  final Rect rect;
  final int artworkIndex;
  String get key => '$column:$row';
}

class InfiniteWorld {
  const InfiniteWorld();

  static const double columnWidth = 208;
  static const double gap = 5;
  static const int cycleLength = 32;

  static int _hash(int a, int b) {
    int h = ((a * 73856093) ^ (b * 19349663)) & 0x7fffffff;
    h ^= h >> 13;
    h = (h * 1274126177) & 0x7fffffff;
    h ^= h >> 16;
    return h & 0x7fffffff;
  }

  /// Height varies per column and tile, making a dense independent-column
  /// mosaic with narrow dark gutters rather than a uniform card grid.
  double _height(int column, int slot) =>
      126 + (_hash(column, slot) % 184).toDouble();

  double _cycleHeight(int column) {
    var height = 0.0;
    for (var i = 0; i < cycleLength; i++) {
      height += _height(column, i) + gap;
    }
    return height;
  }

  /// Sparse lookup is O(visible columns * visible rows), not O(distance).
  /// A strict cap also protects the image decoder during extreme zoom-outs.
  List<WorldTile> visible(Rect world, int artworkCount,
      {int limit = 180, Rect? priorityViewport}) {
    if (artworkCount == 0 || world.isEmpty || limit <= 0) return const [];
    final tiles = <WorldTile>[];
    final left = (world.left / (columnWidth + gap)).floor() - 1;
    final right = (world.right / (columnWidth + gap)).ceil() + 1;
    for (var column = left; column <= right; column++) {
      final cycleHeight = _cycleHeight(column);
      final startCycle = (world.top / cycleHeight).floor() - 1;
      final endCycle = (world.bottom / cycleHeight).ceil() + 1;
      for (var cycle = startCycle; cycle <= endCycle; cycle++) {
        var y = cycle * cycleHeight;
        for (var slot = 0; slot < cycleLength; slot++) {
          final height = _height(column, slot);
          final rect = Rect.fromLTWH(
            column * (columnWidth + gap).toDouble(), y,
            columnWidth, height,
          );
          if (rect.overlaps(world)) {
            final row = cycle * cycleLength + slot;
            tiles.add(WorldTile(column: column, row: row, rect: rect,
              artworkIndex: _hash(column + 4567, row - 891) % artworkCount));
            // Default callers keep the original fast bounded traversal.
            // With a priority viewport we collect the nearby overdraw too,
            // then choose on-screen tiles first. This prevents the 180-tile
            // limit from blanking the right side at low zoom.
            if (priorityViewport == null && tiles.length >= limit) {
              return tiles;
            }
          }
          y += height + gap;
        }
      }
    }
    if (priorityViewport != null && tiles.length > limit) {
      final center = priorityViewport.center;
      tiles.sort((a, b) {
        final aOnScreen = a.rect.overlaps(priorityViewport) ? 0 : 1;
        final bOnScreen = b.rect.overlaps(priorityViewport) ? 0 : 1;
        if (aOnScreen != bOnScreen) {
          return aOnScreen.compareTo(bOnScreen);
        }
        final aDistance = (a.rect.center - center).distanceSquared;
        final bDistance = (b.rect.center - center).distanceSquared;
        final difference = aDistance.compareTo(bDistance);
        if (difference != 0) return difference;
        final columns = a.column.compareTo(b.column);
        return columns != 0 ? columns : a.row.compareTo(b.row);
      });
      return tiles.take(limit).toList(growable: false);
    }
    return tiles;
  }
}

/// Source-agnostic, deterministic look-ahead for the paired Drift canvases.
/// The actual image loader stays with each consumer (museum vs local photos).
class DriftPrefetchPlan {
  DriftPrefetchPlan._();

  static Offset direction(Offset delta, {bool auto = false}) {
    if (auto) return const Offset(0, 1);
    if (delta.distanceSquared < 4) return Offset.zero;
    return delta / delta.distance;
  }

  static Rect window(Rect visible, Offset movement, {bool auto = false}) {
    final dir = direction(movement, auto: auto);
    const side = 0.65;
    const ahead = 0.9;
    return Rect.fromLTRB(
      visible.left - visible.width *
          (side + (-dir.dx).clamp(0.0, 1.0) * ahead),
      visible.top - visible.height *
          (side + (-dir.dy).clamp(0.0, 1.0) * ahead),
      visible.right + visible.width *
          (side + dir.dx.clamp(0.0, 1.0) * ahead),
      visible.bottom + visible.height *
          (side + dir.dy.clamp(0.0, 1.0) * ahead),
    );
  }

  static Offset focus(Rect visible, Offset movement, {bool auto = false}) {
    final dir = direction(movement, auto: auto);
    return visible.center + Offset(
        dir.dx * visible.width * 0.55,
        dir.dy * visible.height * 0.55);
  }
}
