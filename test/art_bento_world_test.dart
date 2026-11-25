import 'dart:ui';
import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:flutter_test/flutter_test.dart';

Artwork sample(int i) => Artwork(
  id: i + 1, title: i % 7 == 0 ? 'Flower landscape' : 'Painting',
  artist: 'Artist', date: '1890',
  imageId: '01234567-0123-0123-0123-0123456789ab',
  publicDomain: true, artworkType: 'Painting',
  imageWidth: i.isEven ? 800 : 600,
  imageHeight: i.isEven ? 600 : 800,
  bootstrapAsset: 'assets/gallery/thumbs/' + (i + 1).toString() + '.webp',
);

void main() {
  final items = List.generate(240, sample);
  final pixelScores = <String,int>{
    for (var i = 0; i < items.length; i++) items[i].catalogKey: i,
  };
  final bento = ArtBentoWorld(items, pixelScores);

  test('actual widths, heights, square/horizontal/portrait/XL vary', () {
    final tiles = bento.visible(const Rect.fromLTWH(0, 0, 3150, 3150),
        items.length, limit: 1000);
    expect(tiles.length, greaterThan(100));
    expect(tiles.map((t) => t.rect.width).toSet(),
        containsAll([145.0, 295.0, 445.0]));
    expect(tiles.map((t) => t.rect.height).toSet(),
        containsAll([145.0, 295.0, 445.0]));
    expect(tiles.any((t) => t.rect.width > t.rect.height), isTrue);
    expect(tiles.any((t) => t.rect.height > t.rect.width), isTrue);
  });

  test('tile ID, geometry, collision-free placement are deterministic', () {
    const area = Rect.fromLTWH(-1000, -800, 2200, 1800);
    final first = bento.visible(area, items.length, limit: 800);
    final second = bento.visible(area, items.length, limit: 800);
    expect(first.map((t) => t.key + '/' + t.artworkIndex.toString() +
        '/' + t.rect.toString()).toList(),
      second.map((t) => t.key + '/' + t.artworkIndex.toString() +
        '/' + t.rect.toString()).toList());
    expect(first.map((t) => t.key).toSet().length, first.length);
    for (var i = 0; i < first.length; i++) {
      for (var j = i + 1; j < first.length; j++) {
        expect(first[i].rect.overlaps(first[j].rect), isFalse);
      }
    }
  });

  test('XL and long large tiles outrank small by source image color', () {
    final tiles = bento.visible(const Rect.fromLTWH(-1800, -900, 3600, 2200),
        items.length, limit: 900);
    final large = tiles.where((t) =>
        t.rect.width >= 440 || t.rect.height >= 440).toList();
    final small = tiles.where((t) =>
        t.rect.width == 145 && t.rect.height == 145).toList();
    expect(large, isNotEmpty);
    expect(small, isNotEmpty);
    final minLarge = large.map((t) =>
      pixelScores[items[t.artworkIndex].catalogKey]!).reduce(
        (a,b) => a < b ? a : b);
    final maxSmall = small.map((t) =>
      pixelScores[items[t.artworkIndex].catalogKey]!).reduce(
        (a,b) => a > b ? a : b);
    expect(minLarge, greaterThan(maxSmall));
  });

  test('far coordinates and viewport priority respect render cap', () {
    const viewport = Rect.fromLTWH(0, 0, 660, 1000);
    final onscreen = bento.visible(viewport, items.length, limit: 180)
        .map((t) => t.key).toSet();
    final render = bento.visible(
        const Rect.fromLTWH(-1500, -1200, 3500, 3700),
        items.length, limit: 180, priorityViewport: viewport);
    expect(render.length, lessThanOrEqualTo(180));
    expect(onscreen.difference(render.map((t) => t.key).toSet()), isEmpty);
    expect(bento.visible(
        const Rect.fromLTWH(-2000000, 1000000, 900, 1600),
        items.length, limit: 100), isNotEmpty);
  });
}
