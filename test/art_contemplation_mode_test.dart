import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/screens/artwork_detail.dart';

void main() {
  testWidgets('a tap enters and exits distraction-free painting mode',
      (tester) async {
    const art = Artwork(
      id: 1, title: 'Example artwork', artist: 'Artist', date: '1901',
      imageId: '', publicDomain: false, museumSource: 'met',
      artworkType: 'Painting',
    );
    await tester.pumpWidget(MaterialApp(home: ArtworkDetail(
      artworks: const [art], initialIndex: 0,
      isFavorite: (_) => false, onToggleFavorite: (_) async {},
    )));
    await tester.pump();
    expect(find.text('ARTDRIFT · L’OPERA'), findsOneWidget);
    final viewer = find.byType(InteractiveViewer);
    expect(viewer, findsOneWidget);
    await tester.tap(viewer);
    await tester.pump();
    expect(find.text('ARTDRIFT · L’OPERA'), findsNothing);
    expect(find.byTooltip('Torna alla galleria'), findsNothing);
    await tester.tap(viewer);
    await tester.pump();
    expect(find.text('ARTDRIFT · L’OPERA'), findsOneWidget);
  });
}
