import 'dart:ui';

import 'package:drift_core/drift_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  Widget canvas({Offset? start}) => MaterialApp(home: Scaffold(
    body: DriftCanvas<String>(
      items: const ['image'], onOpen: (_) {},
      initialWorldCenter: start,
      tileBuilder: (_, __, ___) => const ColoredBox(color: Colors.blue),
      cameraKey: 'test.random', compactBrand: 'A∞',
      fullBrand: 'artdrift ∞', hintText: 'Canvas',
      recenterTooltip: 'Center',
    ),
  ));

  testWidgets('explicit initial world center is applied to camera',
      (tester) async {
    await tester.pumpWidget(canvas(start: const Offset(1200, 800)));
    await tester.pump();
    expect(find.byKey(const ValueKey('drift-museum-immersive')), findsNothing);
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.containsKey('test.random.x'), isFalse);
    expect(tester.takeException(), isNull);
  });

  testWidgets('random visits never overwrite the existing saved camera',
      (tester) async {
    SharedPreferences.setMockInitialValues({
      'test.random.x': 44.0, 'test.random.y': 22.0,
      'test.random.zoom': 1.45,
    });
    await tester.pumpWidget(canvas(start: const Offset(1300, 900)));
    await tester.pump();
    await tester.drag(find.byType(DriftCanvas<String>),
      const Offset(30, 0));
    await tester.pump();
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getDouble('test.random.x'), 44.0);
    expect(prefs.getDouble('test.random.y'), 22.0);
    expect(prefs.getDouble('test.random.zoom'), 1.45);
  });

  testWidgets('default camera contract remains unchanged',
      (tester) async {
    SharedPreferences.setMockInitialValues({
      'test.random.x': 44.0, 'test.random.y': 22.0,
      'test.random.zoom': 1.45,
    });
    await tester.pumpWidget(canvas());
    await tester.pump();
    expect(tester.takeException(), isNull);
    expect(find.byTooltip('Center'), findsOneWidget);
  });
}
