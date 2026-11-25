import 'dart:math' as math;
import 'dart:ui';

import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_joyful_start.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

Artwork art(int index, {required String title, String date = '1900'}) =>
  Artwork(
    id: index + 1, title: title, artist: 'Artist', date: date,
    imageId: '01234567-0123-0123-0123-0123456789ab',
    publicDomain: true, artworkType: 'Painting',
    bootstrapAsset: 'assets/gallery/thumbs/${index + 1}.webp',
  );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('new launches visit different world coordinates', () async {
    final items = List.generate(240, (i) => art(i,
        title: i.isEven ? 'Sunlit mountain landscape' : 'Garden flowers'));
    final first = await ArtJoyfulStart.chooseForLaunch(items,
        viewport: const Size(390, 844), random: math.Random(25));
    final second = await ArtJoyfulStart.chooseForLaunch(items,
        viewport: const Size(390, 844), random: math.Random(25));
    expect(second, isNot(first));
    expect((second - first).distance, greaterThanOrEqualTo(1100));
  });

  test('selection is repeatable for fixed random seed and does not edit list',
      () {
    final items = List.generate(200, (i) => art(i,
      title: i % 5 == 0 ? 'Portrait of a sitter' :
          i % 3 == 0 ? 'View of lake and meadows' : 'Summer blossoms'));
    final original = items.map((e) => e.catalogKey).toList();
    final a = ArtJoyfulStart.choose(items, viewport: const Size(820, 1180),
      random: math.Random(77));
    final b = ArtJoyfulStart.choose(items, viewport: const Size(820, 1180),
      random: math.Random(77));
    expect(a, b);
    expect(items.map((e) => e.catalogKey).toList(), original);
  });

  test('empty catalog cannot break startup', () {
    expect(ArtJoyfulStart.choose(const [],
      viewport: const Size(390, 844)), Offset.zero);
  });
}
