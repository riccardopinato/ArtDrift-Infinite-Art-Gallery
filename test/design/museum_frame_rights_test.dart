import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/screens/artwork_detail.dart';

void main() {
  const works = [
    Artwork(id: 101, title: 'The Hill', artist: 'First Painter',
      date: '1882', imageId: '', museumSource: 'met',
      imageWidth: 400, imageHeight: 800, publicDomain: true,
      medium: 'Oil on canvas', rightsLicense: 'CC0 1.0'),
    Artwork(id: 102, title: 'The Bay', artist: 'Second Painter',
      date: '1905', imageId: '', museumSource: 'met',
      imageWidth: 1200, imageHeight: 600, publicDomain: true,
      medium: 'Oil on wood', rightsLicense: 'CC0 1.0'),
  ];

  testWidgets('museum wood frame preserves artwork ID, shape and rights',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: ArtworkDetail(
      artworks: works, initialIndex: 0,
      isFavorite: (_) => false,
      onToggleFavorite: (_) async {},
    )));
    await tester.pump();
    final frame = find.byKey(const Key('artdrift-museum-wood-frame'));
    expect(frame, findsOneWidget);
    final firstSize = tester.getSize(frame);
    expect(firstSize.width / firstSize.height, closeTo(0.5, 0.04));
    expect(find.text('The Hill'), findsWidgets);
    expect(find.byKey(const Key('artdrift-image-license-label')),
      findsOneWidget);
    await tester.tap(find.byTooltip('Successivo'));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('The Bay'), findsWidgets);
    expect(tester.getSize(frame).height, closeTo(firstSize.height, 1));
    expect(find.byKey(const Key('artdrift-image-license-label')),
      findsOneWidget);
  });
}
