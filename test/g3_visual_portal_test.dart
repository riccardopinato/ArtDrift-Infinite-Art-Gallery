import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/ui/localization.dart';
import 'package:artdrift/ui/museum_portal.dart';

void main() {
  setUp(() => ArtDriftLocale.current.value = 'it');

  Future<void> setupCanvas(WidgetTester tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
  }

  testWidgets('G3 portal: exact approved Italian loading typography',
      (tester) async {
    await setupCanvas(tester);
    await tester.pumpWidget(const MaterialApp(
      home: MuseumPortal.loading()));
    await tester.pump(const Duration(milliseconds: 80));
    expect(find.text('Il museo sta aprendo'), findsOneWidget);
    expect(find.text('la visita sta per cominciare'), findsOneWidget);
    await expectLater(find.byType(MuseumPortal),
      matchesGoldenFile('goldens/g3_portal_loading_it.png'));
  });

  testWidgets('G3 portal: real offline/error and retry presentation',
      (tester) async {
    await setupCanvas(tester);
    await tester.pumpWidget(MaterialApp(
      home: MuseumPortal.unavailable(onRetry: () {})));
    await tester.pump();
    expect(find.text('La galleria non è disponibile'), findsOneWidget);
    expect(find.text('Riprova'), findsOneWidget);
    await expectLater(find.byType(MuseumPortal),
      matchesGoldenFile('goldens/g3_portal_unavailable_it.png'));
  });
}
