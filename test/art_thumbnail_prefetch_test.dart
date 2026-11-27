import 'dart:async';

import 'package:flutter/material.dart';
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
      museumSource: 'met', bootstrapAsset: 'assets/gallery/thumbs/501.webp',
      remotePreviewUrl: 'https://images.metmuseum.org/example/501.jpg',
    );
    await prefetcher.warm(context, art, 1.0);
    await prefetcher.warm(context, art, 2.0);
    expect(seen, ['bundle:true/detail:false',
      'bundle:false/detail:true']);
    await prefetcher.warm(context, art, 2.0);
    expect(seen.length, 2); // High-detail cooldown deduplicates.
  });

}
