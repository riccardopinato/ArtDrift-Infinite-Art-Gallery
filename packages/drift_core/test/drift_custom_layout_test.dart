import 'package:drift_core/drift_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('opt-in geometry used for render + prefetch; legacy stays intact',
      (tester) async {
    var calls = 0, warmed = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: DriftCanvas<int>(
      items: const [7], onOpen: (_) {},
      tileBuilder: (_, value, zoom) => const Text('legacy'),
      tileBuilderWithTile: (_, value, zoom, tile) =>
          Text('custom ' + tile.key),
      tileLayout: (area, count, {limit = 180, priorityViewport}) {
        calls++;
        return const InfiniteWorld().visible(area, count,
            limit: limit, priorityViewport: priorityViewport);
      },
      prefetchItem: (_, value, zoom) async { warmed++; },
      cameraKey: 'core.custom', compactBrand: 'A',
      fullBrand: 'Art', hintText: 'Canvas',
      recenterTooltip: 'Center',
    ))));
    await tester.pump(const Duration(milliseconds: 310));
    expect(calls, greaterThanOrEqualTo(2));
    expect(warmed, greaterThan(0));
    expect(find.text('legacy'), findsNothing);
    expect(find.textContaining('custom '), findsWidgets);
  });
}
