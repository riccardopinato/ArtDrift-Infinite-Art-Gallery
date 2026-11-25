import 'dart:ui';

import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_joyful_palette.dart';
import 'package:flutter_test/flutter_test.dart';

/// Fully synthetic Web QA: no museum HTTP, asset bundle or plugin I/O.
/// Proves JavaScript FNV-1a precision and the actual editorial geometry.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Chrome has exact 32-bit image-ID fingerprints and varied bento tiles', () {
    final keys = List<String>.generate(
        4500, (i) => 'met:' + (i + 1).toString())..sort();
    expect(ArtJoyfulPalette.fingerprint(keys), 660349192);

    final artworks = List<Artwork>.generate(240, (i) => Artwork(
      id: i + 1, title: i % 7 == 0 ? 'Flower landscape' : 'Painting',
      artist: 'Artist', date: '1890',
      imageId: '01234567-0123-0123-0123-0123456789ab',
      publicDomain: true, artworkType: 'Painting',
      imageWidth: i.isEven ? 800 : 600,
      imageHeight: i.isEven ? 600 : 800,
      bootstrapAsset: 'assets/gallery/thumbs/' + (i + 1).toString() + '.webp',
    ));
    final scores = <String, int>{
      for (var i = 0; i < artworks.length; i++)
        artworks[i].catalogKey: i,
    };
    final bento = ArtBentoWorld(artworks, scores);
    const area = Rect.fromLTWH(-900, -1200, 2700, 2400);
    final tiles = bento.visible(area, artworks.length, limit: 900);
    expect(tiles, isNotEmpty);
    expect(tiles.map((t) => t.rect.width).toSet(),
        containsAll([145.0, 295.0, 445.0]));
    expect(tiles.map((t) => t.rect.height).toSet(),
        containsAll([145.0, 295.0, 445.0]));
    expect(tiles.any((t) => t.rect.width > t.rect.height), isTrue);
    expect(tiles.any((t) => t.rect.height > t.rect.width), isTrue);
  });
}
