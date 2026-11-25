import 'package:artdrift/screens/doppleganger.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('opens a bundled portrait, reveals its match and advances',
      (tester) async {
    await tester.runAsync(() async {
      await rootBundle.loadString('assets/doppleganger.json');
    });
    await tester.pumpWidget(
      const MaterialApp(home: DopplegangerScreen()),
    );
    await tester.pumpAndSettle();
    expect(find.byType(OutlinedButton), findsNWidgets(3));
    final firstRound = tester.widget<ListView>(find.byType(ListView)).key;

    await tester.tap(find.byType(OutlinedButton).first);
    await tester.pumpAndSettle();
    expect(find.byType(OutlinedButton), findsNothing);
    final next = find.text('Prossimo ritratto');
    await tester.scrollUntilVisible(next, 150);
    await tester.tap(next);
    await tester.pumpAndSettle();
    expect(tester.widget<ListView>(find.byType(ListView)).key,
        isNot(firstRound));
    expect(find.byType(OutlinedButton), findsNWidgets(3));

    final reveal = find.text('Mostra la risposta');
    await tester.scrollUntilVisible(reveal, 150);
    await tester.tap(reveal);
    await tester.pumpAndSettle();
    expect(find.byType(OutlinedButton), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
