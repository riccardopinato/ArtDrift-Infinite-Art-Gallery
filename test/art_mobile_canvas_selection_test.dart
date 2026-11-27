import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_mobile_canvas_selection.dart';

Artwork _painting(int id) => Artwork(
  id: id, title: 'Painting $id', artist: '', date: '',
  imageId: 'abcdefabcdefabcdefabcdefabcdefab', publicDomain: true,
  artworkType: 'Painting', bootstrapAsset: 'assets/gallery/thumbs/$id.webp');

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('fresh mobile install selects curated verified IDs and pins them', () async {
    final works = List.generate(400, (i) => _painting(i + 1));
    final color = works.reversed.take(320).toList();
    final first = await ArtMobileCanvasSelection.select(works,
        initialColorPlaylist: color);
    expect(first.map((a) => a.catalogKey).toList(),
        (color).map((a) => a.catalogKey).toList());
    final grown = [...works, _painting(401)];
    final second = await ArtMobileCanvasSelection.select(grown,
        initialColorPlaylist: grown.take(320).toList());
    expect(second.map((a) => a.catalogKey).toList(),
        (color).map((a) => a.catalogKey).toList());
  });

  test('legacy saved camera keeps original full artwork order after upgrade',
      () async {
    SharedPreferences.setMockInitialValues({
      'artdrift.camera.x': 12.0,
      'artdrift.camera.y': -7.0,
      'artdrift.camera.zoom': 1.35,
    });
    final works = List.generate(400, (i) => _painting(i + 1));
    final first = await ArtMobileCanvasSelection.select(works,
        initialColorPlaylist: works.reversed.take(320).toList());
    expect(first.map((a) => a.catalogKey).toList(),
        works.map((a) => a.catalogKey).toList());
    final grown = [...works, _painting(401)];
    final second = await ArtMobileCanvasSelection.select(grown,
        initialColorPlaylist: grown.reversed.take(320).toList());
    expect(second.map((a) => a.catalogKey).toList(),
        (works).map((a) => a.catalogKey).toList());
  });

  test('stored playlist never substitutes unrelated art on updates', () async {
    final originals = List.generate(330, (i) => _painting(i + 1));
    await ArtMobileCanvasSelection.select(originals,
        initialColorPlaylist: originals.reversed.toList());
    final other = [...originals, _painting(331)];
    final selected = await ArtMobileCanvasSelection.select(other);
    expect(selected.map((x) => x.catalogKey).toSet(),
      (originals).map((x) => x.catalogKey).toSet());
  });
}
