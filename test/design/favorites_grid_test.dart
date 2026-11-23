import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/screens/favorites_sheet.dart';
import 'package:artdrift/services/favorites.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  const first = Artwork(
    id: 12, title: 'Mountain Garden', artist: 'Painter One',
    date: '', imageId: '', publicDomain: true);
  const second = Artwork(
    id: 13, title: 'Quiet Sea', artist: 'Painter Two',
    date: '', imageId: '', publicDomain: true);

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ArtDriftLocale.current.value = 'it';
  });

  testWidgets('collection uses a grid and preserves per-item unfavorite',
      (tester) async {
    final favorites = Favorites();
    await favorites.load();
    await favorites.toggle(first);
    await favorites.toggle(second);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Builder(
      builder: (context) => TextButton(
        onPressed: () => showArtFavoritesSheet(context,
          favorites: favorites, catalog: const [first, second],
          onToggleFavorite: favorites.toggle),
        child: const Text('Open shelf')),
    ))));
    await tester.tap(find.text('Open shelf'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('artdrift-favorites-grid')), findsOneWidget);
    expect(find.byKey(const Key('artdrift-favorite-open-aic:12')),
      findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-unfavorite-aic:12')));
    await tester.pumpAndSettle();
    expect(favorites.contains(first), isFalse);
    expect(favorites.contains(second), isTrue);
    expect(find.text('Quiet Sea'), findsOneWidget);
  });
}
