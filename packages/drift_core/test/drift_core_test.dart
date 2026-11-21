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
