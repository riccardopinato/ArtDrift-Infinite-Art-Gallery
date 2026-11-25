import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_joyful_palette.dart';
import 'package:artdrift/services/art_mobile_canvas_selection.dart';
import 'package:artdrift/services/art_offline_thumbnail_index.dart';
import 'package:artdrift/services/catalog_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

Artwork sample(int id) => Artwork(
  id: id, title: 'Painting', artist: 'A', date: '1880',
  imageId: '01234567-0123-0123-0123-0123456789ab',
  publicDomain: true, artworkType: 'Painting',
  bootstrapAsset: 'assets/gallery/thumbs/' + id.toString() + '.webp',
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('v2 extends pinned playlist once, preserving every earlier source ID',
      () async {
    final works = List.generate(500, (i) => sample(i + 1));
    final primary = works.take(320).toList();
    final extras = works.skip(320).take(150).toList();
    // Simulate an existing v1 installation, before the v2 migration marker.
    SharedPreferences.setMockInitialValues({
      ArtMobileCanvasSelection.preferenceKey:
          primary.map((a) => a.catalogKey).toList(),
    });
    final before = await ArtMobileCanvasSelection.select(works);
    expect(before.length, 320);
    final after = await ArtMobileCanvasSelection.select(works,
        additionalColorPlaylist: extras);
    expect(after.length, 470);
    expect(after.take(320).map((a) => a.catalogKey),
        primary.map((a) => a.catalogKey));
    final again = await ArtMobileCanvasSelection.select(
        [...works, sample(501)], additionalColorPlaylist: [
      ...extras, sample(501),
    ]);
    expect(again.map((a) => a.catalogKey).toList(),
        after.map((a) => a.catalogKey).toList());
    expect(after.map((a) => a.catalogKey).toSet().length, after.length);
  });

  test('actual 4500 catalog contains 800 additional backed paintings',
      () async {
    await ArtOfflineThumbnailIndex.instance.initialize();
    final catalogClient = CatalogService();
    addTearDown(catalogClient.close);
    final catalog = await catalogClient.load();
    final scores = await ArtJoyfulPalette.load(catalog);
    final primary = ArtJoyfulPalette.select(catalog, scores);
    final extra = ArtJoyfulPalette.supplement(catalog, scores, primary);
    expect(catalog.length, 4500);
    expect(primary.length, 2400);
    expect(extra.length, 800);
    final allKeys = [...primary, ...extra].map((a) => a.catalogKey).toSet();
    expect(allKeys.length, 3200);
    expect(extra.every((a) => a.hasBundledPreview ||
        ArtOfflineThumbnailIndex.instance.has(a)), isTrue);
  });
}
