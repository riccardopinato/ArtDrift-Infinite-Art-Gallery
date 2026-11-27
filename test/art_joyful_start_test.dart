import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_joyful_start.dart';

Artwork art(int index) => Artwork(
  id: index + 1,
  title: index.isEven ? 'Garden landscape' : 'Portrait of a painter',
  artist: 'Original painter', date: '1892', imageId: '',
  publicDomain: true,
  bootstrapAsset: 'assets/gallery/thumbs/pinned.webp',
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('explicit opt-in is disabled unless saved otherwise', () async {
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getBool(ArtJoyfulStart.enabledKey) ?? false, false);
  });

  test('consecutive openings choose different world regions', () async {
    final items = List.generate(240, art);
    final a = await ArtJoyfulStart.chooseForLaunch(items,
      viewport: const Size(390, 844), random: math.Random(25));
    final b = await ArtJoyfulStart.chooseForLaunch(items,
      viewport: const Size(390, 844), random: math.Random(25));
    expect((b-a).distance, greaterThanOrEqualTo(1100));
  });

  test('candidate chooser leaves artwork IDs and ordering untouched', () {
    final items = List.generate(240, art);
    final original = items.map((e) => e.catalogKey).toList();
    final a = ArtJoyfulStart.choose(items,
      viewport: const Size(820,1180), random: math.Random(77));
    final b = ArtJoyfulStart.choose(items,
      viewport: const Size(820,1180), random: math.Random(77));
    expect(a, b);
    expect(items.map((e) => e.catalogKey).toList(), original);
    expect(ArtJoyfulStart.choose(const [], viewport: const Size(390,844)),
      Offset.zero);
  });
}
