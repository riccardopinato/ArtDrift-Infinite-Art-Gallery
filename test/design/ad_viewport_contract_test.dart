import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/ui/art_ad_aware_viewport.dart';

void main() {
  Future<void> mount(WidgetTester tester, double height) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: ArtAdAwareViewport(
        bannerHeight: height,
        child: const ColoredBox(
          color: Colors.black, child: Center(child: Text('Museum Canvas'))),
      ))));
    await tester.pump();
  }

  testWidgets('absent ad => no ghost bottom gap', (tester) async {
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    await mount(tester, 0);
    final r = tester.getRect(
      find.byKey(const Key('artdrift-ad-aware-canvas-region')));
    expect(find.byKey(const Key('artdrift-qa-ad-reserved-region')),
      findsNothing);
    expect(r.height, closeTo(844, 0.1));
  });

  testWidgets('simulated 50 / 90 dp banners exclude gestures region',
      (tester) async {
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    for (final height in const [50.0, 90.0]) {
      await mount(tester, height);
      final canvas = tester.getRect(
        find.byKey(const Key('artdrift-ad-aware-canvas-region')));
      final banner = tester.getRect(
        find.byKey(const Key('artdrift-qa-ad-reserved-region')));
      expect(canvas.bottom, closeTo(banner.top, .1));
      expect(banner.height, closeTo(height, .1));
      expect(canvas.height, closeTo(844 - height, .1));
    }
  });

  testWidgets('runtime ad appearance/disappearance updates canvas height',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    final banner = ValueNotifier<double>(0);
    addTearDown(banner.dispose);
    await tester.pumpWidget(MaterialApp(home: Scaffold(body:
      ValueListenableBuilder<double>(
        valueListenable: banner,
        builder: (context, height, child) => ArtAdAwareViewport(
          bannerHeight: height,
          child: const Center(child: Text('Canvas state remains mounted'))),
      ))));
    final canvas = find.byKey(const Key('artdrift-ad-aware-canvas-region'));
    expect(tester.getSize(canvas).height, closeTo(844, .1));
    banner.value = 90;
    await tester.pump();
    expect(tester.getSize(canvas).height, closeTo(754, .1));
    banner.value = 0;
    await tester.pump();
    expect(tester.getSize(canvas).height, closeTo(844, .1));
    expect(find.text('Canvas state remains mounted'), findsOneWidget);
  });
}
