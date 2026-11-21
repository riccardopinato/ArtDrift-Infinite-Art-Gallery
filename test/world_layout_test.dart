import 'dart:ui';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/canvas/world_layout.dart';

void main() {
  const world = InfiniteWorld();
  test('same region has the same stable tile coordinates and artwork IDs', () {
    const viewport = Rect.fromLTWH(-600, -500, 1400, 1000);
    final first = world.visible(viewport, 137);
    final second = world.visible(viewport, 137);
    expect(first.length, greaterThan(10));
    expect(first.map((e) => '${e.key}/${e.artworkIndex}/${e.rect}').toList(),
      second.map((e) => '${e.key}/${e.artworkIndex}/${e.rect}').toList());
  });

  test('very far movement needs no history and remains bounded', () {
    final far = world.visible(const Rect.fromLTWH(-2000000, 1000000, 900, 1600),
      82, limit: 100);
    expect(far, isNotEmpty);
    expect(far.length, lessThanOrEqualTo(100));
    expect(far.every((e) => e.artworkIndex >= 0 && e.artworkIndex < 82), isTrue);
  });

  test('no same-column tile overlaps another', () {
    final tiles = world.visible(const Rect.fromLTWH(-220, -800, 900, 2000), 60);
    for (var i = 0; i < tiles.length; i++) {
      for (var j = i + 1; j < tiles.length; j++) {
        if (tiles[i].column == tiles[j].column) {
          expect(tiles[i].rect.overlaps(tiles[j].rect), isFalse);
        }
      }
    }
  });
  test('empty catalog does not attempt to display placeholder art', () {
    expect(world.visible(const Rect.fromLTWH(0, 0, 400, 900), 0), isEmpty);
  });
}
