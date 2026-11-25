import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/services/art_bento_vivid_ranking.dart';
import 'package:artdrift/services/art_joyful_palette.dart';
import 'package:artdrift/services/art_offline_thumbnail_index.dart';
import 'package:artdrift/services/catalog_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'dart:ui';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('top 800 genuinely vivid images lead XL; exact 4500 IDs preserved',
      () async {
    await ArtOfflineThumbnailIndex.instance.initialize();
    final client = CatalogService();
    addTearDown(client.close);
    final artworks = await client.load();
    final pixels = await ArtJoyfulPalette.load(artworks);
    expect(pixels.length, 4500);
    final boosted = ArtBentoVividRanking.prioritize(artworks, pixels);
    expect(boosted.length, 4500);
    expect(boosted['cleveland:20083462'], 255);
    expect(boosted['getty:5681994609'], 255);
    expect(boosted.values.where((x) => x > 70).length, 800);
    expect(boosted.values.every((x) => x >= 0 && x <= 255), true);

    final chosen = ArtJoyfulPalette.select(artworks, pixels);
    final extras = ArtJoyfulPalette.supplement(artworks, pixels, chosen);
    final canvas = [...chosen, ...extras];
    expect(canvas.length, 3200);
    final world = ArtBentoWorld(canvas, boosted);
    final tiles = world.visible(const Rect.fromLTWH(-1000, -2000, 3600, 3800),
        canvas.length, limit: 2000);
    final heroes = tiles.where((tile) =>
        tile.rect.width >= 440 || tile.rect.height >= 440);
    expect(heroes, isNotEmpty);
    expect(heroes.every((tile) =>
      boosted[canvas[tile.artworkIndex].catalogKey]! >= 100), true);
  });

  test('source identity mismatch returns prior scores unchanged', () {
    const existing = <String,int>{'a': 122};
    expect(ArtBentoVividRanking.prioritize([], existing), same(existing));
  });
}
