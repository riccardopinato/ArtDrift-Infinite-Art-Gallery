import 'dart:ui';

import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:flutter_test/flutter_test.dart';

Artwork picture(int i) => Artwork(
  id: i + 1,
  title: i % 13 == 0 ? 'Flower landscape' : 'Painting',
  artist: 'Artist',
  date: '1890',
  imageId: '01234567-0123-0123-0123-0123456789ab',
  publicDomain: true,
  artworkType: 'Painting',
  imageWidth: i.isEven ? 800 : 600,
  imageHeight: i.isEven ? 600 : 800,
  bootstrapAsset: 'assets/gallery/thumbs/' + (i + 1).toString() + '.webp',
);

void main() {
  final paintings = List.generate(3200, picture);
  final scores = <String, int>{
    for (var i = 0; i < paintings.length; i++)
      paintings[i].catalogKey: i % 256,
  };
  final world = ArtBentoWorld(paintings, scores);

  test('every 450px macroblock is exactly covered by four puzzle pieces', () {
    for (var x = -5; x <= 5; x++) {
      for (var y = -5; y <= 5; y++) {
        final box = Rect.fromLTWH(x * 450.0, y * 450.0, 450, 450);
        final tiles = world.visible(box, paintings.length, limit: 20);
        expect(tiles.length, 4);
        var area = 0.0;
        for (final tile in tiles) {
          expect(tile.rect.left >= box.left, isTrue);
          expect(tile.rect.top >= box.top, isTrue);
          expect(tile.rect.right <= box.right, isTrue);
          expect(tile.rect.bottom <= box.bottom, isTrue);
          area += tile.rect.width * tile.rect.height;
        }
        for (var i = 0; i < tiles.length; i++) {
          for (var j = i + 1; j < tiles.length; j++) {
            expect(tiles[i].rect.overlaps(tiles[j].rect), isFalse);
          }
        }
        expect(area, 450.0 * 450.0,
            reason: 'Any uncovered or overlapping pixel is a layout bug');
      }
    }
  });

  test('there are no repeated source artworks on a large desktop window', () {
    const view = Rect.fromLTWH(-2700, -2700, 5400, 5400);
    final tiles = world.visible(view, paintings.length, limit: 1000);
    expect(tiles.length, greaterThan(500));
    expect(tiles.map((t) => t.artworkIndex).toSet().length, tiles.length);
    expect(tiles.map((t) => t.key).toSet().length, tiles.length);
    final returned = world.visible(view, paintings.length, limit: 1000);
    expect(returned.map((t) => t.artworkIndex).toList(),
        tiles.map((t) => t.artworkIndex).toList(),
        reason: 'Revisiting a coordinate must show the same unique painting');
  });

  test('a whole horizontal 800-block cycle consumes all 3200 paintings', () {
    const all = Rect.fromLTWH(0, 0, 800 * 450.0, 450);
    final tiles = world.visible(all, paintings.length, limit: 3300);
    expect(tiles.length, 3200);
    expect(tiles.map((t) => t.artworkIndex).toSet().length, 3200);
    expect(tiles.map((t) => t.artworkIndex).toSet(),
        Set<int>.from(List<int>.generate(3200, (i) => i)));
  });

  test('a whole vertical 800-block cycle also exhausts the source catalog',
      () {
    const all = Rect.fromLTWH(0, 0, 450, 800 * 450.0);
    final tiles = world.visible(all, paintings.length, limit: 3300);
    expect(tiles.length, 3200);
    expect(tiles.map((t) => t.artworkIndex).toSet().length, 3200);
  });

  test('negative and distant coordinates are locally repeat-free', () {
    const regions = [
      Rect.fromLTWH(-2000000, 1000000, 1800, 1800),
      Rect.fromLTWH(1500000, -1200000, 1800, 1800),
      Rect.fromLTWH(-2700, -2700, 1800, 1800),
    ];
    for (final area in regions) {
      final tiles = world.visible(area, paintings.length, limit: 100);
      expect(tiles, isNotEmpty);
      expect(tiles.map((t) => t.artworkIndex).toSet().length,
          tiles.length);
    }
  });

  test('puzzle frame orientation follows original painting orientation', () {
    List<Artwork> oriented(bool wide) => List.generate(240, (i) => Artwork(
      id: i + 1,
      title: 'Example painting',
      artist: 'Painter',
      date: '1890',
      imageId: '01234567-0123-0123-0123-0123456789ab',
      publicDomain: true,
      artworkType: 'Painting',
      imageWidth: wide ? 1000 : 500,
      imageHeight: wide ? 500 : 1000,
    ));

    for (final wide in [true, false]) {
      final works = oriented(wide);
      final adaptive = ArtBentoWorld(works, const {});
      final tiles = adaptive.visible(
          const Rect.fromLTWH(0, 0, 450, 450), works.length);
      expect(tiles.length, 4);
      final hero = tiles.reduce((a, b) =>
        a.rect.width * a.rect.height >= b.rect.width * b.rect.height
          ? a : b);
      if (wide) {
        expect(hero.rect.width, greaterThan(hero.rect.height));
      } else {
        expect(hero.rect.height, greaterThan(hero.rect.width));
      }
    }
  });

  test('all on-screen tiles survive priority culling and prefetch limits', () {
    const screen = Rect.fromLTWH(0, 0, 650, 1000);
    const bounds = Rect.fromLTWH(-1500, -1200, 3500, 3700);
    final keys = world.visible(screen, paintings.length, limit: 180)
        .map((t) => t.key).toSet();
    final capped = world.visible(bounds, paintings.length,
        limit: 180, priorityViewport: screen);
    expect(capped.length, lessThanOrEqualTo(180));
    expect(keys.difference(capped.map((t) => t.key).toSet()), isEmpty);
  });
}
