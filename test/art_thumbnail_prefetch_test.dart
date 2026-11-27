import 'dart:async';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:artdrift/services/art_offline_thumbnail_index.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_thumbnail_prefetch.dart';

Artwork remoteArt(int id) => Artwork(
  id: id, title: 'Artwork $id', artist: '', date: '',
  imageId: '', publicDomain: true, artworkType: 'Painting',
  museumSource: 'met',
  remotePreviewUrl:
      'https://images.metmuseum.org/CRDImages/ep/web-large/$id.jpg',
);

void main() {
  testWidgets('museum warmup bounds concurrency and speculative queue',
      (tester) async {
    final gate = Completer<bool>();
    var inFlight = 0;
    var peak = 0;
    var started = 0;
    final prefetcher = ArtThumbnailPrefetch.testing(
      warmer: (_, artwork, bundled, highDetail) async {
        inFlight++;
        started++;
        if (inFlight > peak) peak = inFlight;
        final success = await gate.future;
        inFlight--;
        return success;
      },
    );

    late BuildContext context;
    await tester.pumpWidget(MaterialApp(home:
      Builder(builder: (c) {
        context = c;
        return const SizedBox(width: 200, height: 200);
      }),
    ));

    final pending = <Future<void>>[];
    for (var i = 1; i <= 50; i++) {
      pending.add(prefetcher.warm(context, remoteArt(i), 1));
    }
    expect(peak, ArtThumbnailPrefetch.maxConcurrent);
    expect(prefetcher.activeCount, ArtThumbnailPrefetch.maxConcurrent);
    expect(prefetcher.queuedCount, ArtThumbnailPrefetch.maxQueued);
    expect(started, ArtThumbnailPrefetch.maxConcurrent);

    gate.complete(true);
    await Future.wait(pending);
    expect(prefetcher.activeCount, 0);
    expect(prefetcher.queuedCount, 0);
    expect(peak, ArtThumbnailPrefetch.maxConcurrent);
  });

  testWidgets('duplicate URLs warm once while cached cooldown is valid',
      (tester) async {
    var started = 0;
    final prefetcher = ArtThumbnailPrefetch.testing(
      warmer: (_, art, bundled, highDetail) async {
        started++;
        return true;
      },
    );
    late BuildContext context;
    await tester.pumpWidget(MaterialApp(home: Builder(builder: (c) {
      context = c;
      return const SizedBox();
    })));

    await prefetcher.warm(context, remoteArt(5), 1);
    await prefetcher.warm(context, remoteArt(5), 1);
    expect(started, 1);
  });
  testWidgets('prefetch switches to the actual high-detail source at zoom',
      (tester) async {
    final seen = <String>[];
    final prefetcher = ArtThumbnailPrefetch.testing(
      warmer: (_, artwork, bundled, highDetail) async {
        seen.add('bundle:$bundled/detail:$highDetail');
        return true;
      },
    );
    late BuildContext context;
    await tester.pumpWidget(MaterialApp(home: Builder(builder: (c) {
      context = c;
      return const SizedBox();
    })));
    final art = Artwork(
      id: 501, title: 'Verified preview', artist: '', date: '',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'met', bootstrapAsset: 'assets/museums/thumbs/met_501.webp',
      remotePreviewUrl: 'https://images.metmuseum.org/example/501.jpg',
    );
    await prefetcher.warm(context, art, 1.0);
    await prefetcher.warm(context, art, 2.0);
    expect(seen, ['bundle:true/detail:false',
      'bundle:false/detail:true']);
    await prefetcher.warm(context, art, 2.0);
    expect(seen.length, 2); // High-detail cooldown deduplicates.
  });

  testWidgets('on Web offline-manifest tiles keep the same prefetch source at high zoom',
      (tester) async {
    if (!kIsWeb) return;
    ArtOfflineThumbnailIndex.instance.loadFromManifest(
      '{"schema_version":1,"keys":["met:502"]}');
    final calls = <String>[];
    final prefetcher = ArtThumbnailPrefetch.testing(
      warmer: (_, artwork, bundled, highDetail) async {
        calls.add('bundle:$bundled/detail:$highDetail');
        return true;
      },
    );
    late BuildContext context;
    await tester.pumpWidget(MaterialApp(home: Builder(builder: (c) {
      context = c;
      return const SizedBox();
    })));
    final artwork = Artwork(
      id: 502, title: 'Offline source preview', artist: '', date: '',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'met',
      remotePreviewUrl: 'https://images.metmuseum.org/example/502.jpg',
    );
    expect(ArtOfflineThumbnailIndex.instance.urlFor(artwork), isNotNull);
    await prefetcher.warm(context, artwork, 1.0);
    await prefetcher.warm(context, artwork, 2.0);
    expect(calls, ['bundle:false/detail:false'],
      reason: 'high zoom still renders the cached same-origin Web thumbnail');
  });

}
