import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/search/gallery_search.dart';
import 'package:artdrift/ui/gallery_toolbar.dart';
import 'package:artdrift/screens/search_sheet.dart';
import 'package:artdrift/screens/settings_sheet.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  const sample = Artwork(
    id: 27992, title: 'Park and a Garden',
    artist: 'Claude Monet', date: '1890', publicDomain: true,
    imageId: '2d484387-2509-5e8e-2c43-22f9981972eb',
    artworkType: 'Painting', bootstrapAsset: 'assets/gallery/thumbs/27992.webp',
    subjectTerms: ['park', 'garden'],
  );

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ArtDriftLocale.current.value = 'it';
  });

  test('autocompletion by artist and title is immediate', () {
    final engine = GallerySearch([sample]);
    expect(engine.suggest('Mon').contains('Claude Monet'), isTrue);
    expect(engine.suggest('Park').contains('Park and a Garden'), isTrue);
    expect(engine.find('Monet',scope: ArtworkSearchScope.artist), [sample]);
    expect(engine.find('Claude',scope: ArtworkSearchScope.title), isEmpty);
    expect(engine.find('parco',scope: ArtworkSearchScope.subject), [sample]);
    expect(engine.find('barca',scope: ArtworkSearchScope.subject), isEmpty);
  });

  test('search scope index is reused across repeated queries', () {
    final engine = GallerySearch([sample]);
    expect(engine.cachedScopeCount, 0);
    expect(engine.find('Monet'), [sample]);
    expect(engine.cachedScopeCount, 1);
    expect(engine.find('Park'), [sample]);
    expect(engine.cachedScopeCount, 1);
    expect(engine.find('garden', scope: ArtworkSearchScope.subject), [sample]);
    expect(engine.cachedScopeCount, 2);
    expect(engine.find('barca', scope: ArtworkSearchScope.subject), isEmpty);
    expect(engine.cachedScopeCount, 2);
  });

  testWidgets('framed search occupies exactly one third of 390px screen',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(() { tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio(); });
    var opened = false;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: ArtDriftToolbar(
      onSearch: () => opened = true,
      onSettings: () {},
      onFavorites: () {},
    ))));
    final control = find.byKey(const Key('artdrift-search-control'));
    expect(control, findsOneWidget);
    expect(tester.getSize(control).width, closeTo(130, 1));
    await tester.tap(control);
    expect(opened, isTrue);
    expect(find.byKey(const Key('artdrift-settings-control')), findsOneWidget);
  });

  testWidgets('parchment search suggests before submitting to any museum',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Builder(
      builder: (context) => Scaffold(body: TextButton(
        child: const Text('Open'),
        onPressed: () => showArtSearchSheet(context, const [sample]),
      )),
    )));
    await tester.tap(find.text('Open'));
    await tester.pumpAndSettle();
    expect(find.text('Cerca nell’arte'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'Mon');
    await tester.pump();
    expect(find.text('Claude Monet'), findsWidgets);
    expect(find.text('Cerca anche nei musei'), findsOneWidget);
  });

  testWidgets('language change stays in same design and no fake Pro purchase',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Builder(
      builder: (context) => Scaffold(body: TextButton(
        child: const Text('Open settings'),
        onPressed: () => showArtDriftSettings(context),
      )),
    )));
    await tester.tap(find.text('Open settings'));
    await tester.pumpAndSettle();
    expect(find.text('Impostazioni'), findsOneWidget);
    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();
    expect(find.text('Settings'), findsOneWidget);
    expect(find.text('Current plan: Free'), findsOneWidget);
  });
}
