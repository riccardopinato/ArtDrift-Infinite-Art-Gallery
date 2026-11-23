import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/ui/localization.dart';
import 'package:artdrift/ui/museum_portal.dart';

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final fonts = <String, String?>{
      'Roboto': Platform.environment['ARTDRIFT_G3_SANS_FONT'],
      'serif': Platform.environment['ARTDRIFT_G3_SERIF_FONT'],
      'MaterialIcons': Platform.environment['ARTDRIFT_G3_ICONS_FONT'],
    };
    for (final entry in fonts.entries) {
      final path = entry.value;
      if (path == null || path.isEmpty || !File(path).existsSync()) {
        if (entry.key == 'MaterialIcons') continue;
        throw StateError('Missing G3 review font ${entry.key}: $path');
      }
      final bytes = await File(path).readAsBytes();
      await (FontLoader(entry.key)
        ..addFont(Future<ByteData>.value(ByteData.sublistView(bytes))))
          .load();
    }
  });

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
