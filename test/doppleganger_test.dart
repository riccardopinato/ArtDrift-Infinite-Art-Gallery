import 'dart:convert';

import 'package:artdrift/screens/doppleganger.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('opens a bundled portrait, reveals its match and advances',
      (tester) async {
    // Decode the actual bundled data outside Flutter test's fake-async zone.
    // The 1 MB JSON asset otherwise leaves an indeterminate loading indicator
    // active while pumpAndSettle waits for the screen to become idle.
    final loaded = await tester.runAsync(() async {
      final raw = await rootBundle.loadString('assets/doppleganger.json');
      return (jsonDecode(raw) as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .where((row) => row['status'] == 'verified')
          .toList();
    });
    expect(loaded, isNotNull);
    final catalog = loaded!;
    expect(catalog, hasLength(87));
    await tester.pumpWidget(
      MaterialApp(
        home: DopplegangerScreen(
          catalogLoader: () async => catalog,
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(OutlinedButton), findsNWidgets(3));
    final firstRound = tester.widget<ListView>(find.byType(ListView)).key;

    await tester.tap(find.byType(OutlinedButton).first);
    await tester.pumpAndSettle();
    expect(find.byType(OutlinedButton), findsNothing);
    final next = find.text('Prossimo ritratto');
    // ListView lazily builds distant actions: materialize then align.
    await tester.scrollUntilVisible(next, 150);
    await tester.ensureVisible(next);
    await tester.pumpAndSettle();
    await tester.tap(next);
    await tester.pumpAndSettle();
    expect(tester.widget<ListView>(find.byType(ListView)).key,
        isNot(firstRound));
    expect(find.byType(OutlinedButton), findsNWidgets(3));

    final reveal = find.text('Mostra la risposta');
    // On small viewports the answer action can be below the fold.
    // Bring the actual tappable TextButton into the viewport, rather
    // than only materializing the Text widget during sliver scrolling.
    await tester.ensureVisible(reveal);
    await tester.pumpAndSettle();
    await tester.tap(reveal);
    await tester.pumpAndSettle();
    expect(find.byType(OutlinedButton), findsNothing);
    expect(tester.takeException(), isNull);
  });
  testWidgets('a correct match updates the session score; reveal does not',
      (tester) async {
    final raw = await tester.runAsync(() =>
      rootBundle.loadString('assets/doppleganger.json'));
    final rows = (jsonDecode(raw!) as List<dynamic>)
      .cast<Map<String, dynamic>>()
      .where((row) => row['status'] == 'verified').toList();
    await tester.pumpWidget(MaterialApp(home: DopplegangerScreen(
      catalogLoader: () async => rows)));
    await tester.pumpAndSettle();
    expect(find.text('1/87  ·  0 corrette'), findsOneWidget);
    final person = (rows.first['person'] as Map)['name'] as String;
    final choice = find.widgetWithText(OutlinedButton, person);
    await tester.ensureVisible(choice);
    await tester.pumpAndSettle();
    await tester.tap(choice);
    await tester.pumpAndSettle();
    expect(find.text('1/87  ·  1 corrette'), findsOneWidget);
    final next = find.text('Prossimo ritratto');
    await tester.scrollUntilVisible(next, 150);
    await tester.ensureVisible(next);
    await tester.tap(next);
    await tester.pumpAndSettle();
    expect(find.text('2/87  ·  1 corrette'), findsOneWidget);
    final reveal = find.text('Mostra la risposta');
    await tester.ensureVisible(reveal);
    await tester.tap(reveal);
    await tester.pumpAndSettle();
    expect(find.text('2/87  ·  1 corrette'), findsOneWidget);
  });

}
