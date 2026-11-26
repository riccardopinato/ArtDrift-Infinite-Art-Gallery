import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:drift_core/drift_core.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('on-screen tiles win over far overdraw when the render cap hits', () {
    const world = InfiniteWorld();
    const actual = Rect.fromLTWH(0, 0, 620, 800);
    const overdraw = Rect.fromLTWH(-3000, -2000, 6800, 6000);
    final required = world.visible(actual, 400, limit: 180);
    final prioritized = world.visible(overdraw, 400,
        limit: 180, priorityViewport: actual);
    expect(prioritized.length, lessThanOrEqualTo(180));
    final actualKeys = required.map((e) => e.key).toSet();
    final renderKeys = prioritized.map((e) => e.key).toSet();
    expect(actualKeys.difference(renderKeys), isEmpty,
        reason: 'No on-screen image may be dropped for offscreen overdraw');
  });

  test('look-ahead grows toward manual pan, auto moves downward', () {
    const visible = Rect.fromLTWH(0, 0, 400, 800);
    final movingRight = DriftPrefetchPlan.window(
        visible, const Offset(120, 0));
    final movingLeft = DriftPrefetchPlan.window(
        visible, const Offset(-120, 0));
    final stopped = DriftPrefetchPlan.window(visible, Offset.zero);
    expect(movingRight.right, greaterThan(stopped.right));
    expect(movingLeft.left, lessThan(stopped.left));
    expect(movingRight.left, greaterThan(movingLeft.left));
    final auto = DriftPrefetchPlan.window(visible, Offset.zero, auto: true);
    expect(auto.bottom, greaterThan(stopped.bottom));
    expect(DriftPrefetchPlan.focus(visible, Offset.zero, auto: true).dy,
        greaterThan(visible.center.dy));
  });

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

  testWidgets('Auto moves actual tiles on 60 Hz frames and stops on pause',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: DriftCanvas<String>(
        items: const ['art'], onOpen: (_) {},
        tileBuilder: (_, item, zoom) => const ColoredBox(color: Colors.black),
        cameraKey: 'test.60hz', compactBrand: 'A∞',
        fullBrand: 'artdrift ∞', hintText: 'Canvas',
        recenterTooltip: 'Center'),
    )));
    await tester.pump();
    final tile = find.byKey(const ValueKey('0:0'));
    expect(tile, findsOneWidget);
    final startY = tester.widget<Positioned>(tile).top!;

    await tester.tap(find.byKey(const ValueKey('drift-auto-toggle')));
    await tester.pump();
    expect(find.text('Pausa'), findsOneWidget);

    // 16 ms is deliberately shorter than the 30 ms render throttle.
    // Previous code reset its reference on every frame and never moved.
    for (var i = 0; i < 36; i++) {
      await tester.pump(const Duration(milliseconds: 16));
    }
    final movedY = tester.widget<Positioned>(tile).top!;
    expect(movedY, lessThan(startY - 8));

    await tester.tap(find.byKey(const ValueKey('drift-auto-toggle')));
    await tester.pump();
    expect(find.text('Auto'), findsOneWidget);
    final pausedY = tester.widget<Positioned>(tile).top!;
    for (var i = 0; i < 16; i++) {
      await tester.pump(const Duration(milliseconds: 16));
    }
    expect(tester.widget<Positioned>(tile).top!, closeTo(pausedY, 0.001));
  });

  testWidgets('Auto also accumulates high-refresh 120 Hz frames',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: DriftCanvas<String>(
        items: const ['art'], onOpen: (_) {},
        tileBuilder: (_, item, zoom) => const ColoredBox(color: Colors.black),
        cameraKey: 'test.120hz', compactBrand: 'A∞',
        fullBrand: 'artdrift ∞', hintText: 'Canvas',
        recenterTooltip: 'Center'),
    )));
    await tester.pump();
    final tile = find.byKey(const ValueKey('0:0'));
    expect(tile, findsOneWidget);
    final startY = tester.widget<Positioned>(tile).top!;
    await tester.tap(find.byKey(const ValueKey('drift-auto-toggle')));
    await tester.pump();
    for (var i = 0; i < 72; i++) {
      await tester.pump(const Duration(milliseconds: 8));
    }
    expect(tester.widget<Positioned>(tile).top!, lessThan(startY - 8));
    await tester.tap(find.byKey(const ValueKey('drift-auto-toggle')));
    await tester.pump();
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

  testWidgets('tile motion zooms 12% on mouse hover and restores on exit',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: DriftCanvas<String>(
        items: const ['image'], onOpen: (_) {},
        tileBuilder: (_, item, zoom) =>
            const ColoredBox(color: Colors.blue),
        cameraKey: 'test.hover', compactBrand: 'A∞',
        fullBrand: 'artdrift ∞', hintText: 'Canvas',
        recenterTooltip: 'Center'),
    )));
    await tester.pump();
    final tile = find.byKey(const ValueKey('0:0'));
    final motion = find.byKey(const ValueKey('drift-motion-0:0'));
    expect(tester.widget<AnimatedScale>(motion).scale, 1.0);
    final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
    await mouse.addPointer(location: const Offset(1, 1));
    await mouse.moveTo(tester.getCenter(tile));
    await tester.pump();
    expect(tester.widget<AnimatedScale>(motion).scale, 1.12);
    await mouse.moveTo(const Offset(1, 1));
    await tester.pump();
    expect(tester.widget<AnimatedScale>(motion).scale, 1.0);
    await mouse.removePointer();
  });

  testWidgets('touch zoom resets without stealing canvas gestures',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: DriftCanvas<String>(
        items: const ['image'], onOpen: (_) {},
        tileBuilder: (_, item, zoom) =>
            const ColoredBox(color: Colors.blue),
        cameraKey: 'test.touch-motion', compactBrand: 'A∞',
        fullBrand: 'artdrift ∞', hintText: 'Canvas',
        recenterTooltip: 'Center'),
    )));
    await tester.pump();
    final motion = find.byKey(const ValueKey('drift-motion-0:0'));
    final gesture = await tester.startGesture(
        tester.getCenter(find.byKey(const ValueKey('0:0'))));
    await tester.pump();
    expect(tester.widget<AnimatedScale>(motion).scale, 1.12);
    await gesture.up();
    await tester.pump();
    expect(tester.widget<AnimatedScale>(motion).scale, 1.0);
  });
}
