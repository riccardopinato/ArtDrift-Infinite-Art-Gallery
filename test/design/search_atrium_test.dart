import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/screens/search_sheet.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  const artworks = [
    Artwork(id: 3, title: 'Golden Night', artist: 'Painter',
      date: '', imageId: '', publicDomain: true),
  ];
  setUp(() => ArtDriftLocale.current.value = 'it');

  testWidgets('museum search uses original local engine and retains query',
      (tester) async {
    String latest = '';
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Builder(
      builder: (context) => TextButton(
        onPressed: () => showArtSearchSheet(context, artworks,
          initialQuery: latest, onQueryChanged: (text) => latest = text),
        child: const Text('Apri ricerca')),
    ))));
    await tester.tap(find.text('Apri ricerca'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('artdrift-atrium-field')),
      'Golden');
    await tester.pump();
    expect(latest, 'Golden');
    expect(find.text('Golden Night'), findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-atrium-close')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Apri ricerca'));
    await tester.pumpAndSettle();
    expect(find.text('Golden Night'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-atrium-field')), findsOneWidget);
  });
}
