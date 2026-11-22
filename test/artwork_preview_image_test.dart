import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_offline_thumbnail_index.dart';
import 'package:artdrift/ui/artwork_preview_image.dart';

void main() {
  test('search/detail/favorite preview selects exact packaged source ID', () {
    final index = ArtOfflineThumbnailIndex.instance;
    index.loadFromManifest('{"schema_version":1,"keys":["met:77"]}');
    const art = Artwork(
      id: 77, museumSource: 'met', title: 'Portrait',
      artist: 'Artist', date: '1900', imageId: '',
      publicDomain: true, artworkType: 'Painting',
      remotePreviewUrl:
        'https://images.metmuseum.org/CRDImages/ep/web-large/test.jpg',
    );
    if (!kIsWeb) {
      expect(ArtworkPreviewImage.bundledAssetFor(art),
          'web/museum_thumbs/met_77.webp');
    } else {
      expect(ArtworkPreviewImage.bundledAssetFor(art), isNull);
    }
    const other = Artwork(
      id: 78, museumSource: 'met', title: 'Another Portrait',
      artist: 'Artist', date: '1901', imageId: '',
      publicDomain: true, artworkType: 'Painting',
      remotePreviewUrl:
        'https://images.metmuseum.org/CRDImages/ep/web-large/test2.jpg',
    );
    expect(ArtworkPreviewImage.bundledAssetFor(other), isNull);
  });

  test('original AIC bundled asset wins without remote substitution', () {
    const original = Artwork(
      id: 100191, title: 'Original', artist: '', date: '',
      imageId: '1234567890abcdef',
      artworkType: 'Painting', publicDomain: true,
      bootstrapAsset: 'assets/gallery/thumbs/100191.webp',
    );
    expect(ArtworkPreviewImage.bundledAssetFor(original),
        'assets/gallery/thumbs/100191.webp');
  });
}
