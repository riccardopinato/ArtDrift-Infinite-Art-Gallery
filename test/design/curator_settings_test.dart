import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:artdrift/screens/settings_sheet.dart';
import 'package:artdrift/ui/localization.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ArtDriftLocale.current.value = 'it';
  });

  Future<void> open(WidgetTester tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Builder(
      builder: (context) => TextButton(
        onPressed: () => showArtDriftSettings(context),
        child: const Text('Apri impostazioni')),
    ))));
    await tester.tap(find.text('Apri impostazioni'));
    await tester.pumpAndSettle();
  }

  testWidgets('curator settings keep six languages and original sections',
      (tester) async {
    await open(tester);
    expect(find.text('Il tuo'), findsOneWidget);
    expect(find.text('museo.'), findsOneWidget);
    expect(find.byKey(const Key('artdrift-curator-scroll')), findsOneWidget);
    for (final code in ArtDriftLocale.codes) {
      expect(find.byKey(Key('artdrift-language-$code')), findsOneWidget);
    }
    final scroll = find.byKey(const Key('artdrift-curator-scroll'));
    await tester.scrollUntilVisible(
      find.byKey(const Key('artdrift-google-account-section')), 170,
      scrollable: scroll);
    expect(find.byKey(const Key('artdrift-google-account-section')),
      findsOneWidget);
    await tester.scrollUntilVisible(find.text('Prestazioni Android'), 180,
      scrollable: scroll);
    expect(find.text('Prestazioni Android'), findsWidgets);
  });

  testWidgets('language selection persists and the diagnostic tile remains',
      (tester) async {
    await open(tester);
    await tester.tap(find.byKey(const Key('artdrift-language-fr')));
    await tester.pumpAndSettle();
    expect(ArtDriftLocale.current.value, 'fr');
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('artdrift.locale'), 'fr');
    expect(find.text('Votre'), findsOneWidget);
    expect(find.text('musée.'), findsOneWidget);
    await tester.tap(find.byKey(const Key('artdrift-curator-close')));
    await tester.pumpAndSettle();
    expect(find.text('Apri impostazioni'), findsOneWidget);
  });

  testWidgets('curator settings remain scrollable on compact screen',
      (tester) async {
    tester.view.physicalSize = const Size(320, 600);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    await open(tester);
    expect(tester.takeException(), isNull);
    expect(find.byKey(const Key('artdrift-curator-close')), findsOneWidget);
    await tester.drag(find.byKey(const Key('artdrift-curator-scroll')),
      const Offset(0, -480));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}
