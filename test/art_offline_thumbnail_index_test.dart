import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
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

  test('only advertised, non-bundled paintings may use local previews', () {
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
    expect(index.has(known), isTrue);
    if (kIsWeb) {
      expect(index.urlFor(known), contains('museum_thumbs/met_77.webp'));
      expect(index.assetFor(known), isNull);
    } else {
      expect(index.urlFor(known), isNull);
      expect(index.assetFor(known), 'web/museum_thumbs/met_77.webp');
    }
    expect(index.has(missing), isFalse);
    expect(index.urlFor(missing), isNull);
    expect(index.assetFor(missing), isNull);
  });


  test('mobile package manifest loads actual image bytes without network', () async {
    if (kIsWeb) return;
    final index = ArtOfflineThumbnailIndex.instance;
    await index.initialize();
    expect(index.availableCount, greaterThanOrEqualTo(1100));
    const art = Artwork(
      id: 20075763, title: 'Known offline painting', artist: '', date: '',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'cleveland',
      remotePreviewUrl: 'https://openaccess-cdn.clevelandart.org/example.jpg',
    );
    expect(index.has(art), isTrue);
    final asset = index.assetFor(art);
    expect(asset, 'web/museum_thumbs/cleveland_20075763.webp');
    final bytes = await rootBundle.load(asset!);
    expect(bytes.lengthInBytes, greaterThan(250));
    expect(index.urlFor(art), isNull);
  });
}
