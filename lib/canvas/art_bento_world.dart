import 'dart:ui';
import 'package:drift_core/drift_core.dart';
import '../models/artwork.dart';

/// Art-only deterministic colorful bento world. The generic canvas still
/// handles gestures, camera, culling and prefetch; GalleryDrift keeps columns.
class ArtBentoWorld {
  ArtBentoWorld(this.items, this.scores)
      : _ranked = List<int>.generate(items.length, (i) => i) {
    _ranked.sort((a, b) {
      final diff = _quality(items[b]).compareTo(_quality(items[a]));
      return diff != 0 ? diff : items[a].catalogKey.compareTo(items[b].catalogKey);
    });
  }

  final List<Artwork> items;
  final Map<String, int> scores;
  final List<int> _ranked;
  static const double cell = 150, block = 450, gap = 5;

  static final _scenery = RegExp(
    r'landscape|paesagg|paysage|seascape|sea\b|coast|garden|giardin|'
    r'flower|fiori|fleur|blossom|lake|river|mountain|forest|sunset|'
    r'water lilies|meadow|sky|harbor|village|spring', caseSensitive: false);
  static final _portrait = RegExp(
    r'portrait|ritratto|portr[aä]t|bust of|head of|autoritratto',
    caseSensitive: false);

  double _quality(Artwork a) {
    final text = a.title + ' ' + a.subjectTerms.join(' ');
    return (scores[a.catalogKey] ?? 0).toDouble() +
        (_scenery.hasMatch(text) ? 14 : 0) -
        (_portrait.hasMatch(a.title) ? 22 : 0);
  }

  static int _hash(int x, int y, int salt) {
    var h = ((x * 73856093) ^ (y * 19349663) ^ (salt * 83492791))
        & 0x7fffffff;
    h ^= h >> 13;
    h = (h * 1274126177) & 0x7fffffff;
    h ^= h >> 16;
    return h & 0x7fffffff;
  }

  /// Each pattern tiles exactly the 3x3 grid without overlaps.
  static const patterns = <List<_Cell>>[
    [_Cell(0,0,2,2), _Cell(2,0,1,2), _Cell(0,2,1,1), _Cell(1,2,2,1)],
    [_Cell(0,0,3,2), _Cell(0,2,1,1), _Cell(1,2,1,1), _Cell(2,2,1,1)],
    [_Cell(0,0,1,2), _Cell(1,0,2,1), _Cell(1,1,2,2), _Cell(0,2,1,1)],
    [_Cell(0,0,2,1), _Cell(2,0,1,1), _Cell(0,1,1,2),
     _Cell(1,1,2,1), _Cell(1,2,1,1), _Cell(2,2,1,1)],
    [_Cell(0,0,1,1), _Cell(1,0,2,2), _Cell(0,1,1,2), _Cell(1,2,2,1)],
    [_Cell(0,0,1,3), _Cell(1,0,2,2), _Cell(1,2,2,1)],
    [_Cell(0,0,2,2), _Cell(2,0,1,1), _Cell(2,1,1,2), _Cell(0,2,2,1)],
    [_Cell(0,0,2,3), _Cell(2,0,1,1), _Cell(2,1,1,1), _Cell(2,2,1,1)],
  ];

  /// XL draws from top 12% measured real pixels, L from next 24%, M from
  /// middle 39%, S from remaining 25%. Aspect ratio reduces bad cropping.
  int _pick(int x, int y, int slot, _Cell shape, Set<int> used) {
    final area = shape.w * shape.h;
    final xl = area >= 6, large = area >= 4 || shape.h == 3;
    final low = xl ? 0.0 : large ? .12 : area >= 2 ? .36 : .75;
    final high = xl ? .12 : large ? .36 : area >= 2 ? .75 : 1.0;
    final n = _ranked.length;
    final begin = (n * low).floor().clamp(0, n - 1).toInt();
    final end = (n * high).ceil().clamp(begin + 1, n).toInt();
    final span = end - begin;
    final seed = _hash(x, y, slot + 100);
    final target = (shape.w * cell - gap) / (shape.h * cell - gap);
    var chosen = _ranked[begin + seed % span];
    var best = double.negativeInfinity;
    final attempts = span < 13 ? span : 13;
    for (var k = 0; k < attempts; k++) {
      final candidate = _ranked[begin + (seed + k * 29) % span];
      if (used.contains(candidate)) continue;
      final a = items[candidate];
      final visual = _quality(a) -
          (a.naturalAspectRatio - target).abs() * 18;
      if (visual > best) { chosen = candidate; best = visual; }
    }
    if (used.contains(chosen)) {
      for (var k = 0; k < span; k++) {
        final candidate = _ranked[begin + (seed + k) % span];
        if (!used.contains(candidate)) { chosen = candidate; break; }
      }
    }
    used.add(chosen);
    return chosen;
  }

  /// Pure sparse lookup: world position, shape and IDs are viewport-independent.
  List<WorldTile> visible(Rect world, int count,
      {int limit = 180, Rect? priorityViewport}) {
    if (world.isEmpty || count <= 0 || count != items.length ||
        limit <= 0) return const [];
    final result = <WorldTile>[];
    final left = (world.left / block).floor();
    final right = (world.right / block).floor();
    final top = (world.top / block).floor();
    final bottom = (world.bottom / block).floor();
    for (var x = left; x <= right; x++) {
      for (var y = top; y <= bottom; y++) {
        final cells = patterns[_hash(x,y,0) % patterns.length];
        final used = <int>{};
        for (var slot = 0; slot < cells.length; slot++) {
          final s = cells[slot];
          final rect = Rect.fromLTWH(x * block + s.x * cell,
              y * block + s.y * cell, s.w * cell - gap, s.h * cell - gap);
          // Select even offscreen slots to preserve IDs as viewport moves.
          final index = _pick(x, y, slot, s, used);
          if (!rect.overlaps(world)) continue;
          result.add(WorldTile(column: x, row: y * 8 + slot,
              rect: rect, artworkIndex: index));
          if (priorityViewport == null && result.length >= limit) return result;
        }
      }
    }
    if (priorityViewport != null && result.length > limit) {
      final center = priorityViewport.center;
      result.sort((a,b) {
        final aa = a.rect.overlaps(priorityViewport) ? 0 : 1;
        final bb = b.rect.overlaps(priorityViewport) ? 0 : 1;
        if (aa != bb) return aa.compareTo(bb);
        final d = (a.rect.center - center).distanceSquared.compareTo(
            (b.rect.center - center).distanceSquared);
        return d != 0 ? d : a.key.compareTo(b.key);
      });
      return result.take(limit).toList(growable: false);
    }
    return result;
  }
}

class _Cell {
  const _Cell(this.x,this.y,this.w,this.h);
  final int x,y,w,h;
}
