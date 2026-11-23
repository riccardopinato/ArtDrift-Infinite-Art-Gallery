import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/ui/tile_origin_flight.dart';

void main() {
  const original = Artwork(
    id: 1, title: 'Original', artist: 'Artist',
    imageId: '', date: '1888', publicDomain: true,
    imageWidth: 400, imageHeight: 800,
  );

  test('flight originates at actual tile center, never viewport center', () {
    const screen = Size(400, 800);
    const tile = Rect.fromLTWH(42, 170, 125, 190);
    expect(TileOriginFlight.startingScale(screen, tile),
        closeTo(125 / 400, .00001));
    expect(TileOriginFlight.originDelta(screen, tile),
        const Offset(-95.5, -135));
    final target = TileOriginFlight.targetFrameRect(
      screen, EdgeInsets.zero, TileOriginFlight.frameAspectFor(original));
    expect(target.width / target.height, closeTo(.5, .001));
    expect(target.center.dx, closeTo(200, .001));
    expect(target.top, greaterThan(0));
    expect(target.bottom, lessThan(screen.height));
  });

  testWidgets('only painting preview moves, not the entire route',
      (tester) async {
    final selected = ValueNotifier<String>('aic:1');
    addTearDown(selected.dispose);
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: TileOriginFlight(
        animation: const AlwaysStoppedAnimation<double>(.5),
        originRect: const Rect.fromLTWH(32, 125, 110, 150),
        originArtwork: original,
        originalArtworkKey: 'aic:1',
        currentArtworkKey: selected,
        child: const Text('Room plaque and viewer controls'),
      ),
    )));
    final flight = find.byKey(const Key('artdrift-origin-flight'));
    expect(flight, findsOneWidget);
    expect(find.descendant(of: flight,
      matching: find.byKey(const Key('artdrift-flight-artwork-only'))),
      findsOneWidget);
    expect(find.descendant(of: flight,
      matching: find.text('Room plaque and viewer controls')),
      findsNothing);
    expect(find.text('Room plaque and viewer controls'), findsOneWidget);
  });

  testWidgets('reverse becomes neutral after browsing another artwork',
      (tester) async {
    final selected = ValueNotifier<String>('aic:1');
    addTearDown(selected.dispose);
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: TileOriginFlight(
        animation: const AlwaysStoppedAnimation<double>(.5),
        originRect: const Rect.fromLTWH(20, 100, 110, 160),
        originArtwork: original,
        originalArtworkKey: 'aic:1',
        currentArtworkKey: selected,
        child: const SizedBox(width: 20, height: 20),
      ),
    )));
    expect(find.byKey(const Key('artdrift-origin-flight')), findsOneWidget);
    selected.value = 'met:2';
    await tester.pump();
    expect(find.byKey(const Key('artdrift-origin-flight')), findsNothing);
    expect(find.descendant(
      of: find.byType(TileOriginFlight),
      matching: find.byType(FadeTransition),
    ), findsOneWidget);
  });
}
