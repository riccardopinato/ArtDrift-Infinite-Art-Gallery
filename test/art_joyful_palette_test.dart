import 'dart:convert';
import 'package:artdrift/services/art_joyful_palette.dart';
import 'package:artdrift/services/art_offline_thumbnail_index.dart';
import 'package:artdrift/services/catalog_service.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('pixel manifest binds exact 4500 source IDs; colorful 2400 remain image-backed', () async {
    await ArtOfflineThumbnailIndex.instance.initialize();
    final source = CatalogService(); addTearDown(source.close);
    final catalog = await source.load();
    expect(catalog.length, 4500);
    final scores = await ArtJoyfulPalette.load(catalog);
    expect(scores.length, 4500);
    expect(scores.containsKey(catalog.first.catalogKey), true);
    final selected = ArtJoyfulPalette.select(catalog, scores);
    expect(selected.length, 2400);
    expect(selected.map((a) => a.catalogKey).toSet().length, 2400);
    expect(selected.every((a)=>a.hasBundledPreview ||
        ArtOfflineThumbnailIndex.instance.has(a)),true);
    final mean = selected.map((a)=>scores[a.catalogKey]!).reduce((a,b)=>a+b)
        / selected.length;
    expect(mean, greaterThan(85)); // original source playlist mean: 63.8
    expect(selected.any((a)=>a.artist.toLowerCase().contains('van gogh')),true);
  });

  test('changed/duplicate source-ID catalog fails closed rather than mislabels pixels', () async {
    final source = CatalogService(); addTearDown(source.close);
    final catalog = await source.load();
    final raw = await rootBundle.loadString(ArtJoyfulPalette.assetPath);
    expect(() => ArtJoyfulPalette.decode(catalog.skip(1).toList(),raw),
      throwsFormatException);
    final changed = [...catalog];
    changed[0] = changed.last;
    expect(() => ArtJoyfulPalette.decode(changed,raw),throwsFormatException);
    final decoded = jsonDecode(raw) as Map<String,dynamic>;
    decoded['score_bytes_base64'] = base64Encode([1,2,3]);
    expect(() => ArtJoyfulPalette.decode(catalog,jsonEncode(decoded)),
      throwsFormatException);
  });
}
