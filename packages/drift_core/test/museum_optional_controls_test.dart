import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:drift_core/drift_core.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));
  testWidgets('museum controls are opt-in and speed menu persists a selection',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: DriftCanvas<String>(
      items: const ['art'], onOpen: (_) {}, tileBuilder: (context, item, zoom) =>
          const ColoredBox(color: Colors.black),
      cameraKey: 'test.museum.menu', compactBrand: 'A∞',
      fullBrand: 'artdrift ∞', hintText: 'Canvas',
      recenterTooltip: 'Center', museumControls: true,
    ))));
    expect(find.byKey(const ValueKey('drift-museum-immersive')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('drift-auto-speed')));
    await tester.pump();
    expect(find.byKey(const ValueKey('drift-museum-speed-75')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('drift-museum-speed-75')));
    await tester.pump();
    expect(find.text('75% ▾'), findsOneWidget);
    final p = await SharedPreferences.getInstance();
    expect(p.getInt('test.museum.menu.autoSpeed'), 75);
  });

  testWidgets('museum tile emits its real viewport-local anchor',
      (tester) async {
    Rect? opened, longPressed;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: DriftCanvas<String>(
      items: const ['art'], onOpen: (_) {}, tileBuilder: (context, item, zoom) =>
          const ColoredBox(color: Colors.black),
      cameraKey: 'test.museum.anchor', compactBrand: 'A∞',
      fullBrand: 'artdrift ∞', hintText: 'Canvas',
      recenterTooltip: 'Center',
      onOpenAtRect: (_, rect) => opened = rect,
      onTileLongPress: (_, rect) => longPressed = rect,
    ))));
    final tile = find.byKey(const ValueKey('0:0'));
    await tester.longPress(tile);
    await tester.pump();
    expect(longPressed, isNotNull);
    expect(longPressed!.width, greaterThan(0));
    await tester.tap(tile);
    await tester.pump();
    expect(opened, isNotNull);
    expect(opened!.width, greaterThan(0));
  });

  testWidgets('museum immersive state is controllable and Gallery default intact',
      (tester) async {
    bool? current;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: DriftCanvas<String>(
      items: const ['a'], onOpen: (_) {}, tileBuilder: (context, item, zoom) =>
          const ColoredBox(color: Colors.black),
      cameraKey: 'test.museum.quiet', compactBrand: 'A∞',
      fullBrand: 'artdrift ∞', hintText: 'Canvas',
      recenterTooltip: 'Center', museumControls: true,
      onImmersiveChanged: (value) => current = value,
    ))));
    await tester.tap(find.byKey(const ValueKey('drift-museum-immersive')));
    await tester.pump();
    expect(current, isTrue);
    expect(find.byKey(const ValueKey('drift-auto-toggle')), findsNothing);
    await tester.tap(find.byKey(const ValueKey('drift-museum-immersive')));
    await tester.pump();
    expect(current, isFalse);
    expect(find.byKey(const ValueKey('drift-auto-toggle')), findsOneWidget);
  });
}
