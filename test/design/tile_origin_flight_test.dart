import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/ui/tile_origin_flight.dart';

void main() {
  test('flight is anchored to the exact tile center, not viewport center', () {
    const screen = Size(400, 800);
    const tile = Rect.fromLTWH(42, 170, 125, 190);
    expect(TileOriginFlight.startingScale(screen, tile),
      closeTo(125/400, .00001));
    expect(TileOriginFlight.originDelta(screen, tile),
      const Offset(-95.5, -135));
  });

  testWidgets('reverse becomes neutral when browsing to another artwork',
      (tester) async {
    final current = ValueNotifier<String>('aic:1');
    addTearDown(current.dispose);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: TileOriginFlight(
      animation: const AlwaysStoppedAnimation<double>(.5),
      originRect: const Rect.fromLTWH(20, 100, 110, 160),
      originalArtworkKey: 'aic:1',
      currentArtworkKey: current,
      child: const SizedBox(width: 20, height: 20),
    ))));
    expect(find.byKey(const Key('artdrift-origin-flight')), findsOneWidget);
    current.value = 'met:2';
    await tester.pump();
    expect(find.byKey(const Key('artdrift-origin-flight')), findsNothing);
    expect(find.byType(FadeTransition), findsOneWidget);
  });
}
