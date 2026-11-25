import 'dart:ui';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/services/catalog_service.dart';
import 'package:artdrift/services/art_joyful_palette.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Web and native agree on full catalog color identity and bento size',
      () async {
    final service = CatalogService();
    addTearDown(service.close);
    final catalog = await service.load();
    expect(catalog.length, 4500);
    final keys = catalog.map((a) => a.catalogKey).toList()..sort();
    expect(ArtJoyfulPalette.fingerprint(keys), 2742452096,
        reason: 'FNV-1a must not lose precision in JavaScript arithmetic');
    final scores = await ArtJoyfulPalette.load(catalog);
    expect(scores.length, 4500,
        reason: 'Browser must enable real pixel-based XL selection');
    final world = ArtBentoWorld(catalog, scores);
    const view = Rect.fromLTWH(-900, -1200, 2700, 2400);
    final tiles = world.visible(view, catalog.length, limit: 900);
    expect(tiles, isNotEmpty);
    expect(tiles.map((t) => t.rect.width).toSet(),
        containsAll([145.0, 295.0, 445.0]));
    expect(tiles.map((t) => t.rect.height).toSet(),
        containsAll([145.0, 295.0, 445.0]));
  });
}
