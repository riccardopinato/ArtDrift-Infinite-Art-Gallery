import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/canvas/infinite_gallery.dart';
import 'package:artdrift/models/artwork.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  const artwork = Artwork(
    id: 11, title: 'The Valley', artist: 'Original Painter',
    date: '1890', imageId: '', publicDomain: true,
  );

  testWidgets('long press opens an anchored factual museum plaque',
      (tester) async {
    var opened = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: InfiniteGallery(
        artworks: const [artwork],
        onOpen: (_) => opened++,
      ),
    )));
    await tester.longPress(find.byKey(const ValueKey('0:0')));
    await tester.pump();
    expect(find.text('The Valley'), findsWidgets);
    expect(find.byKey(const Key('artdrift-museum-plaque-open')),
      findsOneWidget);
    expect(opened, 0);
    await tester.tap(find.byKey(const Key('artdrift-museum-plaque-open')));
    await tester.pump();
    expect(opened, 1);
    expect(find.byKey(const Key('artdrift-museum-plaque-open')), findsNothing);
  });

  testWidgets('Art museum opt-in exposes contemplation control',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(
      body: InfiniteGallery(artworks: [artwork], onOpen: _ignore),
    )));
    expect(find.byKey(const ValueKey('drift-museum-immersive')),
      findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('drift-museum-immersive')));
    await tester.pump();
    expect(find.textContaining('Mostra comandi'), findsOneWidget);
  });
}
void _ignore(Artwork art) {}
