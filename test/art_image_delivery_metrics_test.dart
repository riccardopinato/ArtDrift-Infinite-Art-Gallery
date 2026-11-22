import 'package:flutter_test/flutter_test.dart';

import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_image_delivery_metrics.dart';

void main() {
  test('image failures are counted by museum, without retaining image URL', () {
    final metrics = ArtImageDeliveryMetrics.instance;
    metrics.clear();
    const art = Artwork(
      id: 77, title: 'Example Painting', artist: '', date: '',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'met',
      remotePreviewUrl: 'https://images.metmuseum.org/private-path.jpg',
    );
    metrics.recordFailure(art, StateError('secret?key=a-test-value'));
    metrics.recordFailure(art, const FormatException('bad image header'));
    expect(metrics.trackedSourceCount, 1);
    expect(metrics.report, contains('met: network_or_decode=2'));
    expect(metrics.report, isNot(contains('private-path')));
    expect(metrics.report, isNot(contains('a-test-value')));
    metrics.clear();
    expect(metrics.trackedSourceCount, 0);
    expect(metrics.report, contains('none recorded'));
  });

  test('invalid media source cannot grow telemetry state', () {
    final metrics = ArtImageDeliveryMetrics.instance;
    metrics.clear();
    const invalid = Artwork(
      id: 1, title: 'Unknown', artist: '', date: '', imageId: '',
      publicDomain: true, museumSource: 'a/b',
      artworkType: 'Painting',
    );
    metrics.recordFailure(invalid, StateError('denied'));
    expect(metrics.trackedSourceCount, 0);
  });
}
