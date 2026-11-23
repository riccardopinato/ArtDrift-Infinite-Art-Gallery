import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:artdrift/collections/art_collections.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/screens/collection_canvas.dart';
import 'package:artdrift/screens/search_sheet.dart';

Artwork _painting(int id) => Artwork(
  id: id,
  title: 'Landscape on the coast',
  date: '1887',
  artist: 'Unknown',
  imageId: '',
  publicDomain: true,
  artworkType: 'Painting',
  museumSource: 'met',
  remotePreviewUrl:
    'https://images.metmuseum.org/CRDImages/ep/web-large/test.jpg',
  subjectTerms: const ['Landscape', 'Coast'],
);

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('collection opens from search without entering a remote query',
      (tester) async {
    ArtCollection? selected;
    final catalog = [_painting(1), _painting(2), _painting(3)];
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: Builder(builder: (context) => TextButton(
        onPressed: () => showArtSearchSheet(context, catalog,
          onOpenCollection: (collection) => selected = collection),
        child: const Text('Open search'),
      )),
    )));
    await tester.tap(find.text('Open search'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('collection-landscapes')),
        findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('collection-landscapes')));
    await tester.pumpAndSettle();
    expect(selected?.id, 'landscapes');
  });

  testWidgets('collection back action does not overlap Auto controls',
      (tester) async {
    const art = Artwork(
      id: 100191,
      title: 'Landscape', date: '1880', artist: 'Artist',
      imageId: '1234567890abcdef',
      artworkType: 'Painting', publicDomain: true,
      bootstrapAsset: 'assets/gallery/thumbs/100191.webp',
    );
    final collection = ArtCollections.all.first;
    await tester.pumpWidget(MaterialApp(home: ArtCollectionCanvasScreen(
      collection: collection,
      artworks: const [art],
      onOpen: (_, items) {},
    )));
    await tester.pump();
    final back = find.byKey(const ValueKey('collection-back'));
    final auto = find.byKey(const ValueKey('drift-auto-toggle'));
    expect(back, findsOneWidget);
    expect(auto, findsOneWidget);
    expect(tester.getRect(back).overlaps(tester.getRect(auto)), isFalse);
  });
}
