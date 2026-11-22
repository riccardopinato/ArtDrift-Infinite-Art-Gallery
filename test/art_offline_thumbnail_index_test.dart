import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_offline_thumbnail_index.dart';

void main() {
  test('accepts only versioned, exact source IDs', () {
    final index = ArtOfflineThumbnailIndex.instance;
    index.loadFromManifest(
      '{"schema_version":1,"keys":["met:77","cleveland:100003"]}');
    expect(index.availableCount, 2);
    expect(() => index.loadFromManifest(
      '{"schema_version":1,"keys":["met:77","https://evil.test/x"]}'),
      throwsFormatException);
    expect(index.availableCount, 2);
  });

  test('only advertised, non-bundled paintings may use Web local previews', () {
    final index = ArtOfflineThumbnailIndex.instance;
    index.loadFromManifest('{"schema_version":1,"keys":["met:77"]}');
    const known = Artwork(
      id: 77, title: 'Painting', artist: '', date: '',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'met',
      remotePreviewUrl: 'https://images.metmuseum.org/CRDImages/ep/example.jpg',
    );
    const missing = Artwork(
      id: 78, title: 'Another', artist: '', date: '',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'met',
      remotePreviewUrl: 'https://images.metmuseum.org/CRDImages/ep/example2.jpg',
    );
    if (kIsWeb) {
      expect(index.has(known), isTrue);
      expect(index.urlFor(known), contains('museum_thumbs/met_77.webp'));
    } else {
      expect(index.has(known), isFalse);
      expect(index.urlFor(known), isNull);
    }
    expect(index.urlFor(missing), isNull);
  });
}
