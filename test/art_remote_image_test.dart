import 'package:flutter/painting.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/ui/art_remote_image.dart';

void main() {
  test('browser retries cross-origin images through HTML; Android unchanged', () {
    expect(ArtRemoteImage.strategyFor(isWeb: true),
        WebHtmlElementStrategy.fallback);
    expect(ArtRemoteImage.strategyFor(isWeb: false),
        WebHtmlElementStrategy.never);
  });

  test('full resolution tries a distinct museum preview on failure', () {
    final art = Artwork(
      id: 437655, title: 'Forest', artist: 'Seurat', date: '1881',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'met',
      remotePreviewUrl: 'https://images.metmuseum.org/CRDImages/ep/web-large/preview.jpg',
      remoteFullUrl: 'https://images.metmuseum.org/CRDImages/ep/original/full.jpg',
    );
    // The Met uses its official preview for both sizes; duplicate requests
    // must be suppressed.
    expect(ArtRemoteImage.candidateUrls(art, width: 843),
        ['https://images.metmuseum.org/CRDImages/ep/web-large/preview.jpg']);
  });

  test('full-resolution remote sources fall back to the verified preview', () {
    final art = Artwork(
      id: 100, title: 'Example', artist: '', date: '',
      imageId: '', publicDomain: true, artworkType: 'Painting',
      museumSource: 'rijks',
      remotePreviewUrl: 'https://iiif.micr.io/example/preview.jpg',
      remoteFullUrl: 'https://iiif.micr.io/example/full.jpg',
    );
    expect(ArtRemoteImage.candidateUrls(art, width: 843), [
      'https://iiif.micr.io/example/full.jpg',
      'https://iiif.micr.io/example/preview.jpg',
    ]);
  });
}
