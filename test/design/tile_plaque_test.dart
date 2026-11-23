import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/canvas/infinite_gallery.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  const art = Artwork(id: 11, title: 'The Valley', artist: 'Someone',
    date: '1890', imageId: '', publicDomain: true);
  testWidgets('long press previews the actual art without swapping identity',
      (tester) async {
    var openCount = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: InfiniteGallery(
      artworks: const [art], onOpen: (a) => openCount++,
    ))));
    await tester.longPress(find.byKey(const ValueKey('0:0')));
    await tester.pump();
    expect(find.byKey(const Key('artdrift-museum-tile-plaque')), findsOneWidget);
    expect(find.text('The Valley'), findsWidgets);
    expect(openCount, 0);
    await tester.tap(find.byKey(const Key('artdrift-museum-plaque-open')));
    await tester.pump();
    expect(openCount, 1);
  });
}
