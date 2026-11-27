import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/screens/search_sheet.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ArtDriftLocale.current.value = 'it';
  });

  testWidgets('Sosia appears in Explore, not as a canvas overlay',
      (tester) async {
    var opened = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: Builder(builder: (context) => TextButton(
        child: const Text('Apri ricerca'),
        onPressed: () => showArtSearchSheet(context, const [],
          onOpenDoppleganger: () => opened++),
      )),
    )));
    await tester.tap(find.text('Apri ricerca'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('artdrift-doppleganger-entry')),
      findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-doppleganger-entry')));
    await tester.pumpAndSettle();
    expect(opened, 1);
    expect(find.byKey(const Key('artdrift-doppleganger-entry')),
      findsNothing);
  });
}
