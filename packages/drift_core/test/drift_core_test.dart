import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:drift_core/drift_core.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('deterministic bounded tiles at distant coordinates', () {
    const world = InfiniteWorld();
    const bounds = Rect.fromLTWH(-100000, 123456, 900, 1000);
    final a = world.visible(bounds, 13, limit: 100);
    final b = world.visible(bounds, 13, limit: 100);
    expect(a, isNotEmpty);
    expect(a.length, lessThanOrEqualTo(100));
    expect(a.map((x) => x.key).toList(), b.map((x) => x.key).toList());
    expect(a.map((x) => x.artworkIndex).toList(), b.map((x) => x.artworkIndex).toList());
  });

  testWidgets('Auto and cycling 25/50/75/100 speeds share core behavior',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: DriftCanvas<String>(
        items: const ['art'], onOpen: (_) {},
        tileBuilder: (_, item, zoom) => const ColoredBox(color: Colors.black),
        cameraKey: 'test.auto', compactBrand: 'A∞',
        fullBrand: 'artdrift ∞', hintText: 'Canvas',
        recenterTooltip: 'Center'),
    )));
    await tester.pump();
    expect(find.text('25%'), findsOneWidget);
    for (final speed in ['50%', '75%', '100%', '25%']) {
      await tester.tap(find.byKey(const ValueKey('drift-auto-speed')));
      await tester.pump();
      expect(find.text(speed), findsOneWidget);
    }
    await tester.tap(find.byKey(const ValueKey('drift-auto-toggle')));
    await tester.pump(const Duration(milliseconds: 280));
    expect(find.text('Pausa'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('drift-auto-toggle')));
    await tester.pump();
    expect(find.text('Auto'), findsOneWidget);
    await tester.pump(const Duration(seconds: 3));
    expect(find.byKey(const ValueKey('drift-auto-speed')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('drift-auto-speed')));
    await tester.pump();
    expect(find.text('50%'), findsOneWidget);
  });

  testWidgets('ahead-of-viewport items are scheduled for warmup',
      (tester) async {
    var warmed = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: DriftCanvas<int>(
        items: List.generate(120, (i) => i), onOpen: (_) {},
        tileBuilder: (_, item, zoom) => const ColoredBox(color: Colors.black),
        prefetchItem: (_, item, zoom) async { warmed++; },
        cameraKey: 'test.prefetch', compactBrand: 'G∞',
        fullBrand: 'gallerydrift ∞', hintText: 'Canvas',
        recenterTooltip: 'Center'),
    )));
    await tester.pump(const Duration(milliseconds: 300));
    expect(warmed, greaterThan(0));
    expect(warmed, lessThanOrEqualTo(8));
  });

  testWidgets('generic canvas renders source-agnostic image and UI',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: DriftCanvas<String>(items: const ['tile'], onOpen: (_) {},
        tileBuilder: (context, item, zoom) => ColoredBox(
          color: Colors.black, child: Center(child: Text(item))),
        cameraKey: 'test.drift', compactBrand: 'T∞',
        fullBrand: 'test drift ∞', hintText: 'Generic canvas',
        recenterTooltip: 'Center'),
    )));
    await tester.pump();
    expect(find.text('tile'), findsWidgets);
    expect(find.text('Generic canvas'), findsOneWidget);
    expect(find.byTooltip('Center'), findsOneWidget);
  });
}
