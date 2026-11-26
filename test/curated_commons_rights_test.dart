import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/museums/museum_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const page = 'https://commons.wikimedia.org/wiki/File:Painting.jpg';
  const image = 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Painting.jpg';
  const license = 'https://creativecommons.org/licenses/by-sa/4.0/';

  Map<String, dynamic> candidate() => <String, dynamic>{
    'id': 57672559,
    'museum_source': 'commons',
    'museum_name': 'Wikimedia Commons',
    'museum_native_id': '57672559',
    'source_identity': 'commons:57672559',
    'title': 'A painting',
    'artist_title': 'Alfred Sisley',
    'is_public_domain': true, // underlying original painting only
    'artwork_type_title': 'Painting',
    'remote_preview_url': image,
    'remote_museum_url': page,
    'rights_evidence_url': page,
    'rights_license': 'CC BY-SA 4.0',
    'image_license_url': license,
    'image_creator': 'Example photographer',
    'image_attribution': 'Photograph: Example photographer; CC BY-SA 4.0',
    'credit_line': 'Alfred Sisley; photograph: Example photographer',
    'image_modifications': 'Scaled to 500 px',
    'commercially_approved': true,
    'source_provenance_verified': true,
    'worldwide_distribution_reviewed': true,
    'rights_review_reference': 'test-only-fake-approval-not-in-runtime',
  };

  test('Commons images default to blocked even if the painting is PD', () {
    final row = candidate()
      ..remove('commercially_approved')
      ..remove('source_provenance_verified')
      ..remove('worldwide_distribution_reviewed')
      ..remove('rights_review_reference');
    final work = Artwork.fromJson(row);
    expect(work.publicDomain, isTrue);
    expect(work.displayable, isFalse);
    expect(work.curatedCommonsReleaseReady, isFalse);
    expect(work.displayedLicense, 'CC BY-SA 4.0');
  });

  test('synthetic fully signed-off record passes structural validation', () {
    final work = Artwork.fromJson(candidate());
    expect(work.curatedCommonsReleaseReady, isTrue);
    expect(work.displayable, isTrue);
    expect(work.imageLicenseRequiresAttribution, isTrue);
    expect(work.validImageLicenseLink, isTrue);
    expect(work.wallpaperAllowed, isFalse);
    expect(work.imageUrl(width: 400), image);
    final restored = Artwork.fromJson(work.toJson());
    expect(restored.sourceIdentity, work.sourceIdentity);
    expect(restored.imageAttribution, work.imageAttribution);
    expect(restored.imageLicenseUrl, license);
    expect(restored.displayable, isTrue);
  });

  test('missing independent gates, attribution or valid proof blocks import', () {
    for (final deletion in [
      'commercially_approved', 'source_provenance_verified',
      'worldwide_distribution_reviewed', 'rights_review_reference',
      'image_attribution', 'credit_line', 'rights_evidence_url',
      'remote_museum_url', 'museum_native_id',
    ]) {
      final work = Artwork.fromJson(candidate()..remove(deletion));
      expect(work.displayable, isFalse, reason: deletion);
    }
    for (final patch in [
      {'rights_license': 'CC BY-NC 4.0'},
      {'rights_license': 'CC BY-ND 4.0'},
      {'rights_license': 'CC BY-SA 4.0', 'image_license_url':
          'https://creativecommons.org/licenses/by/4.0/'},
      {'remote_preview_url':
          'https://upload.wikimedia.org.attacker.test/wikipedia/commons/a.jpg'},
      {'remote_preview_url': 'http://upload.wikimedia.org/wikipedia/commons/a.jpg'},
      {'remote_preview_url': 'https://upload.wikimedia.org/private/a.jpg'},
      {'remote_museum_url':
          'https://commons.wikimedia.org.attacker.test/wiki/File:A.jpg'},
      {'source_identity': 'commons:111'},
      {'is_public_domain': false},
      {'artwork_type_title': 'Photograph'},
    ]) {
      final work = Artwork.fromJson({...candidate(), ...patch});
      expect(work.displayable, isFalse, reason: patch.toString());
    }
  });

  test('unknown image license must not be silently relabeled CC0', () {
    final common = Artwork.fromJson(candidate()..remove('rights_license'));
    expect(common.displayedLicense, 'Licenza immagine da verificare');
    expect(common.displayable, isFalse);
    final unknown = Artwork.fromJson({
      ...candidate(), 'museum_source': 'met', 'rights_license': '',
    });
    expect(unknown.displayedLicense, 'Licenza immagine da verificare');
    final aic = Artwork(id: 1, title: 'AIC', artist: 'Painter', date: '',
      imageId: '0123456789abcdef01234567', publicDomain: true);
    expect(aic.displayedLicense, 'Public Domain');
  });

  test('Städel is held even when upstream falsely marks it approved', () {
    final x = Artwork.fromJson({
      ...candidate(), 'museum_source': 'staedel', 'id': 1350,
      'museum_name': '',
      'museum_native_id': '1350',
      'source_identity': 'staedel:DE-MUS-048017/lido/1350',
      'remote_preview_url':
          'https://cdn.staedelmuseum.de/images/20/88/1350/thumb-lg.jpg',
      'remote_museum_url':
          'https://sammlung.staedelmuseum.de/en/work/bank-of-the-seine-in-autumn',
    });
    expect(x.displayable, isFalse);
    expect(x.displayedMuseum, 'Städel Museum');
  });

  test('existing bundled catalog remains at 4,428 museum paintings', () async {
    final list = await const MuseumCatalog().bundled();
    expect(list.length, 4428);
    expect(list.where((w) => w.isCuratedCommons), isEmpty);
  });
}
