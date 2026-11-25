import 'dart:convert';
import 'dart:ui';

import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/services/art_real_preview_dimensions.dart';
import 'package:artdrift/services/catalog_service.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('real 4,499 bundled-WebP dimensions override museum crop metadata',
      () async {
    final client = CatalogService();
    addTearDown(client.close);
    final catalog = await client.load();
    expect(catalog.length, 4500);
    final ratio = await ArtRealPreviewDimensions.load(catalog);
    expect(ratio.length, 4499);

    // Museum thumbnail widths/heights are not the dimensions of the local
    // picture frame. This regression MUST stay nonzero to catch accidental
    // fallback to cropped/mismatched frames.
    final mismatch = catalog.where((a) =>
        ratio.containsKey(a.catalogKey) &&
        (ratio[a.catalogKey]! - a.naturalAspectRatio).abs() > 0.01).length;
    expect(mismatch, greaterThan(0));

    final world = ArtBentoWorld(
        catalog,
        {for (final a in catalog) a.catalogKey: a.id % 256},
        actualRatios: ratio);
    final tiles = world.visible(const Rect.fromLTWH(
        -1400, -1800, 3600, 4200), catalog.length, limit: 1500);
    expect(tiles.length, greaterThan(100));
    for (final tile in tiles) {
      final original = catalog[tile.artworkIndex];
      final expected = ratio[original.catalogKey] ??
          original.naturalAspectRatio;
      expect((tile.rect.width / tile.rect.height - expected).abs(),
          lessThan(0.00000001));
    }
    expect(tiles.map((t) => t.artworkIndex).toSet().length, tiles.length);
  });

  test('manifest is bound to exact source IDs and rejects tampering',
      () async {
    final client = CatalogService();
    addTearDown(client.close);
    final catalog = await client.load();
    final raw = await rootBundle.loadString(
        ArtRealPreviewDimensions.assetPath);
    final parsed = jsonDecode(raw) as Map<String,dynamic>;
    final original = ArtRealPreviewDimensions.decode(catalog, raw);
    expect(original.length, 4499);

    parsed['catalog_fingerprint_fnv1a32'] = 0;
    expect(ArtRealPreviewDimensions.decode(catalog, jsonEncode(parsed)),
        isEmpty);
    expect(ArtRealPreviewDimensions.decode(
        catalog.reversed.toList().skip(1).toList(), raw), isEmpty);
  });
}
