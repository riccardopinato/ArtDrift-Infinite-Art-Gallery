import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_mobile_canvas_selection.dart';

Artwork _bundled(int id) => Artwork(
  id: id, title: 'Painting $id', artist: 'Artist', date: '1880',
  imageId: '1234567890abcdef', publicDomain: true,
  artworkType: 'Painting',
  bootstrapAsset: 'assets/gallery/thumbs/$id.webp',
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('mobile canvas retains stable artwork ordering when catalog grows', () async {
    final originals = [_bundled(1), _bundled(2)];
    final first = await ArtMobileCanvasSelection.select(originals);
    expect(first.map((a) => a.catalogKey).toList(),
        originals.map((a) => a.catalogKey).toList());

    final expanded = [...originals, _bundled(3)];
    final second = await ArtMobileCanvasSelection.select(expanded);
    if (kIsWeb) {
      expect(second, hasLength(3));
    } else {
      expect(second.map((a) => a.catalogKey).toList(), ['aic:1', 'aic:2']);
    }
  });

  test('saved selection never includes an unrelated painting', () async {
    final first = [_bundled(5), _bundled(6)];
    await ArtMobileCanvasSelection.select(first);
    final altered = [_bundled(5), _bundled(6), _bundled(7)];
    final selected = await ArtMobileCanvasSelection.select(altered);
    expect(selected.every((a) => altered.contains(a)), isTrue);
    if (!kIsWeb) {
      expect(selected.any((a) => a.id == 7), isFalse);
    }
  });
}
