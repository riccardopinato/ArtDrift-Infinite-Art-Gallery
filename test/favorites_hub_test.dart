import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/favorites.dart';
import 'package:artdrift/screens/favorites_sheet.dart';
import 'package:artdrift/ui/gallery_toolbar.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  const aic = Artwork(id: 123, title: 'Old Garden', artist: 'One',
    date: '', imageId: '', publicDomain: true);
  const met = Artwork(id: 123, title: 'Other Painting', artist: 'Two',
    date: '', imageId: '', publicDomain: true, museumSource: 'met',
    artworkType: 'Painting',
    remotePreviewUrl: 'https://images.metmuseum.org/example.jpg');

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ArtDriftLocale.current.value = 'it';
  });

  test('legacy numeric AIC favorites migrate without losing selections', () async {
    SharedPreferences.setMockInitialValues({
      Favorites.legacyKey: <String>['123', 'not-a-number'],
    });
    final store = Favorites();
    await store.load();
    expect(store.contains(aic), isTrue);
    expect(store.contains(met), isFalse);
    expect(store.savedFrom([aic]), [aic]);
    await store.toggle(met);
    final restored = Favorites();
    await restored.load();
    expect(restored.contains(aic), isTrue);
    expect(restored.contains(met), isTrue);
    expect(restored.savedFrom([aic]).map((a) => a.catalogKey).toSet(),
      {'aic:123', 'met:123'});
  });

  test('remote-only favorites survive restart and can be removed', () async {
    final store = Favorites();
    await store.load();
    await store.toggle(met);
    final restored = Favorites();
    await restored.load();
    expect(restored.savedFrom([]).single.catalogKey, 'met:123');
    await restored.toggle(met);
    final emptied = Favorites();
    await emptied.load();
    expect(emptied.savedFrom([aic, met]), isEmpty);
  });

  testWidgets('favorites heart preserves 1/3-width search and gear',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    var count = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: ArtDriftToolbar(
      onSearch: () {}, onSettings: () {}, onFavorites: () => count++,
    ))));
    expect(tester.getSize(
      find.byKey(const Key('artdrift-search-control'))).width,
      closeTo(130, 1));
    final heart = find.byKey(const Key('artdrift-favorites-control'));
    expect(heart, findsOneWidget);
    await tester.tap(heart);
    expect(count, 1);
    expect(find.byKey(const Key('artdrift-settings-control')), findsOneWidget);
  });

  testWidgets('saved artwork is visible and removable inside shelf',
      (tester) async {
    final store = Favorites();
    await store.load();
    await store.toggle(aic);
    await tester.pumpWidget(MaterialApp(home: Builder(
      builder: (context) => Scaffold(body: TextButton(
        child: const Text('Open favorites'),
        onPressed: () => showArtFavoritesSheet(context,
          favorites: store, catalog: const [aic],
          onToggleFavorite: store.toggle),
      )),
    )));
    await tester.tap(find.text('Open favorites'));
    await tester.pumpAndSettle();
    expect(find.text('Preferiti'), findsOneWidget);
    expect(find.text('Old Garden'), findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-unfavorite-aic:123')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Nessuna opera tra i preferiti'), findsOneWidget);
    expect(store.keys, isEmpty);
  });

  testWidgets('empty favorite shelf renders guidance',
      (tester) async {
    final store = Favorites();
    await store.load();
    await tester.pumpWidget(MaterialApp(home: Builder(
      builder: (context) => Scaffold(body: TextButton(
        child: const Text('Open'),
        onPressed: () => showArtFavoritesSheet(context,
          favorites: store, catalog: const [aic],
          onToggleFavorite: store.toggle),
      )),
    )));
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Nessuna opera tra i preferiti'), findsOneWidget);
  });
}
