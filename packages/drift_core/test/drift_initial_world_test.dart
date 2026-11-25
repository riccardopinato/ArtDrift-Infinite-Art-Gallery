import 'dart:ui';
import 'package:drift_core/drift_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

Widget sample({Offset? center}) => MaterialApp(
  home: Scaffold(body: SizedBox(
    width: 390, height: 800,
    child: DriftCanvas<int>(
      items: List<int>.generate(500, (i) => i),
      cameraKey: 'test.camera',
      initialWorldCenter: center,
      onOpen: (_) {},
      tileBuilder: (_, i, zoom) => Text('Tile $i'),
      compactBrand: 'C', fullBrand: 'Canvas',
      hintText: 'Explore', recenterTooltip: 'Reset',
    ),
  )),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => SharedPreferences.setMockInitialValues({
    'test.camera.x': 195.0,
    'test.camera.y': 400.0,
    'test.camera.zoom': 1.0,
  }));

  testWidgets('opt-in initial world destination overrides legacy saved camera',
      (tester) async {
    const center = Offset(5100, -3400);
    await tester.pumpWidget(sample(center: center));
    await tester.pump();
    final expected = const InfiniteWorld().visible(
      Rect.fromCenter(center: center, width: 390, height: 800), 500);
    expect(expected, isNotEmpty);
    expect(find.byKey(ValueKey(expected.first.key)), findsOneWidget);
  });

  testWidgets('default camera restores saved coordinates as before',
      (tester) async {
    await tester.pumpWidget(sample());
    await tester.pump();
    final expected = const InfiniteWorld().visible(
      const Rect.fromLTWH(-195, -400, 390, 800), 500);
    expect(expected, isNotEmpty);
    expect(find.byKey(ValueKey(expected.first.key)), findsOneWidget);
  });
}
