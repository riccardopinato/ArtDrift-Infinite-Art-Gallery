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
  List<WorldTile> visible(Rect world, int artworkCount, {int limit = 180}) {
    if (artworkCount == 0 || world.isEmpty) return const [];
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
            if (tiles.length >= limit) return tiles;
          }
          y += height + gap;
        }
      }
    }
    return tiles;
  }
}
