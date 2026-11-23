import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/ui/artwork_preview_image.dart';
import 'package:artdrift/ui/museum_wood_frame.dart';
import 'package:artdrift/ui/tile_origin_flight.dart';

const artwork = Artwork(
  id: 874,
  title: 'Landscape',
  artist: 'Jean Charles Cazin',
  date: 'c. 1895',
  imageId: '3a34f988-f779-2e96-1786-8945b6b9c87d',
  bootstrapAsset: 'assets/gallery/thumbs/874.webp',
  imageWidth: 2829,
  imageHeight: 2250,
  publicDomain: true,
);

/// Review harness: authentic bundled painting, actual flight component,
/// simplified stationary viewer background. NOT a pixel-reference mock-up.
class MuseumBackground extends StatelessWidget {
  const MuseumBackground({super.key});

  @override
  Widget build(BuildContext context) => ColoredBox(
    color: const Color(0xFF0E1019),
    child: SafeArea(child: Column(children: [
      const SizedBox(height: 52),
      Expanded(child: Row(children: [
        const SizedBox(width: 43),
        Expanded(child: Center(child: AspectRatio(
          aspectRatio: artwork.imageWidth! / artwork.imageHeight!,
          child: MuseumWoodFrame(child: ArtworkPreviewImage(
            artwork: artwork, fit: BoxFit.contain,
            cacheWidth: 360,
          )),
        ))),
        const SizedBox(width: 43),
      ])),
      const SizedBox(height: 22),
      Container(
        height: 274,
        color: const Color(0xFFF1E6D4),
        alignment: Alignment.topLeft,
        child: const Padding(
          padding: EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('ARTDRIFT · L’OPERA',
                style: TextStyle(fontSize: 12, color: Color(0xFF997149))),
              SizedBox(height: 14),
              Text('Landscape',
                style: TextStyle(fontFamily: 'serif',
                  fontSize: 22, color: Color(0xFF33261B))),
              SizedBox(height: 7),
              Text('Jean Charles Cazin · c. 1895',
                style: TextStyle(fontSize: 14, color: Color(0xFF71553C))),
            ]),
        ),
      ),
    ])),
  );
}


/// A schematic dark canvas composed only from bundled Art Drift WebP works.
/// It is a visual test fixture, not a screenshot of Drift's world layout.
class IllustrativeCanvas extends StatelessWidget {
  const IllustrativeCanvas({super.key});

  @override
  Widget build(BuildContext context) => ColoredBox(
    color: const Color(0xFF111219),
    child: Stack(children: [
      Positioned(left: 18, top: 32, width: 145, height: 115,
        child: Image.asset('assets/gallery/thumbs/2169.webp',
          fit: BoxFit.cover)),
      Positioned(left: 190, top: 56, width: 160, height: 182,
        child: Image.asset('assets/gallery/thumbs/4749.webp',
          fit: BoxFit.cover)),
      Positioned(left: 43, top: 220, width: 112, height: 132,
        child: Image.asset('assets/gallery/thumbs/874.webp',
          fit: BoxFit.cover)),
      Positioned(left: 179, top: 410, width: 167, height: 136,
        child: Image.asset('assets/gallery/thumbs/2169.webp',
          fit: BoxFit.cover)),
      Positioned(left: 27, top: 601, width: 130, height: 165,
        child: Image.asset('assets/gallery/thumbs/4749.webp',
          fit: BoxFit.cover)),
    ]),
  );
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    for (final entry in <String, String?>{
      'Roboto': Platform.environment['ARTDRIFT_G3_SANS_FONT'],
      'serif': Platform.environment['ARTDRIFT_G3_SERIF_FONT'],
      'MaterialIcons': Platform.environment['ARTDRIFT_G3_ICONS_FONT'],
    }.entries) {
      final path = entry.value;
      if (path == null || path.isEmpty || !File(path).existsSync()) {
        if (entry.key == 'MaterialIcons') continue;
        throw StateError('Missing G3 font ${entry.key}: $path');
      }
      final bytes = await File(path).readAsBytes();
      await (FontLoader(entry.key)
        ..addFont(Future<ByteData>.value(ByteData.sublistView(bytes))))
          .load();
    }
  });

  testWidgets('G3 five phases capture the actual painting-only flight',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    final identity = ValueNotifier<String>('aic:874');
    addTearDown(identity.dispose);

    // Warm the exact licensed package assets BEFORE phase 0. The first
    // frame should never show an artificial blank placeholder caused solely
    // by the golden harness loading an image for the first time.
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: IllustrativeCanvas())));
    await tester.pumpAndSettle();

    for (final phase in const [
      (0.0, '00'), (.25, '25'), (.5, '50'), (.75, '75'), (1.0, '100'),
    ]) {
      await tester.pumpWidget(MaterialApp(
        theme: ThemeData.dark().copyWith(
          scaffoldBackgroundColor: const Color(0xFF111219)),
        home: Scaffold(body: Stack(fit: StackFit.expand, children: [
          const IllustrativeCanvas(),
          TileOriginFlight(
            animation: AlwaysStoppedAnimation<double>(phase.$1),
            originRect: const Rect.fromLTWH(43, 220, 112, 132),
            originArtwork: artwork,
            originalArtworkKey: artwork.catalogKey,
            currentArtworkKey: identity,
            child: const MuseumBackground(),
          ),
        ])),
      ));
      await tester.pump(const Duration(milliseconds: 70));
      final rect = find.byKey(const Key('artdrift-origin-flight'));
      expect(rect, phase.$1 < 1 ? findsOneWidget : findsNothing);
      expect(tester.takeException(), isNull);
      await expectLater(find.byType(Scaffold), matchesGoldenFile(
        'goldens/g3_tile_flight_${phase.$2}.png'));
    }

    // When the visited painting changes, the original one must never fly
    // back to its tile on exit. The view switches to a neutral fade.
    identity.value = 'aic:2169';
    await tester.pumpWidget(MaterialApp(
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF111219)),
      home: Scaffold(body: Stack(fit: StackFit.expand, children: [
        const IllustrativeCanvas(),
        TileOriginFlight(
          animation: const AlwaysStoppedAnimation<double>(.5),
          originRect: const Rect.fromLTWH(43, 220, 112, 132),
          originArtwork: artwork,
          originalArtworkKey: artwork.catalogKey,
          currentArtworkKey: identity,
          child: const MuseumBackground(),
        ),
      ])),
    ));
    await tester.pump(const Duration(milliseconds: 70));
    expect(find.byKey(const Key('artdrift-origin-flight')), findsNothing);
    await expectLater(find.byType(Scaffold),
      matchesGoldenFile('goldens/g3_tile_flight_changed_identity.png'));
  });
}
