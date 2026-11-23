import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/screens/artwork_detail.dart';

void main() {
  const works = [
    Artwork(id: 101, title: 'The Hill', artist: 'First Painter',
      date: '1882', imageId: '', museumSource: 'met',
      imageWidth: 400, imageHeight: 800,
      publicDomain: true, medium: 'Oil on canvas'),
    Artwork(id: 102, title: 'The Bay', artist: 'Second Painter',
      date: '1905', imageId: '', museumSource: 'met',
      imageWidth: 1200, imageHeight: 600,
      publicDomain: true, medium: 'Oil on wood'),
  ];
  testWidgets('frame stays stable while identity and caption follow next/prev',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: ArtworkDetail(
      artworks: works, initialIndex: 0,
      isFavorite: (art) => art.id == 101,
      onToggleFavorite: (_) async {},
    )));
    await tester.pump();
    expect(find.byKey(const Key('artdrift-museum-wood-frame')), findsOneWidget);
    final frame = find.byKey(const Key('artdrift-museum-wood-frame'));
    final initialSize = tester.getSize(frame);
    // Portrait artwork receives a proportionate, centered frame rather than
    // filling the entire viewer height with black letterbox around it.
    expect(initialSize.width / initialSize.height, closeTo(.5, .03));
    expect(find.text('The Hill'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-detail-counter')), findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-detail-next')));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('The Bay'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-museum-wood-frame')), findsOneWidget);
    final after = tester.getSize(frame);
    expect(after.width, closeTo(initialSize.width, .1));
    expect(after.height, closeTo(initialSize.height, .1));
    expect(find.byTooltip('Aggiungi ai preferiti'), findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-detail-prev')));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('The Hill'), findsOneWidget);
    expect(find.byTooltip('Rimuovi dai preferiti'), findsOneWidget);
  });

  testWidgets('room label expands only factual metadata',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: ArtworkDetail(
      artworks: works, initialIndex: 0,
      isFavorite: (_) => false,
      onToggleFavorite: (_) async {},
    )));
    await tester.pump();
    expect(find.text('ARTDRIFT · L’OPERA'), findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-room-expand')));
    await tester.pump();
    expect(find.textContaining('Tecnica e materiali: Oil on canvas'), findsWidgets);
    expect(find.text('Scheda originale del museo'), findsOneWidget);
  });
}
