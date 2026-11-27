import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/museums/museum_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const enabled = bool.fromEnvironment('ARTDRIFT_ENABLE_CURATED_COMMONS',
      defaultValue: false);

  test('exact one image-specific review record, no unapproved images', () async {
    final text = await rootBundle.loadString(
        'assets/museums/catalog_curated_commons.json');
    final doc = jsonDecode(text) as List<dynamic>;
    expect(doc.length, 1);
    final map = Map<String, dynamic>.from(doc.single as Map);
    expect(map['source_identity'], 'commons:57672559');
    expect(map['rights_license'], 'CC0 1.0');
    expect(map['rights_review_reference'], isNotEmpty);
    expect(map['commercially_approved'], isTrue);
    expect(map['source_provenance_verified'], isTrue);
    expect(map['worldwide_distribution_reviewed'], isTrue);

    final a = Artwork.fromJson(map);
    expect(a.curatedCommonsRightsEvidenceComplete, isTrue);
    expect(a.curatedCommonsReleaseReady, enabled);
    expect(a.displayable, enabled);
    expect(a.imageUrl(width: 400), startsWith('https://thumb.wikimedia.org/'));
    expect(a.imageUrl(width: 843), startsWith('https://upload.wikimedia.org/'));
    expect(a.imageAttribution, contains('Metropolitan Museum'));
    expect(a.wallpaperAllowed, isFalse);
  });

  test('gated gallery has 4,500 original artworks and one optional Sisley', () async {
    final paintings = await const MuseumCatalog().bundled();
    expect(paintings.length, 4428 + (enabled ? 1 : 0));
    expect(paintings.where((x) => x.museumSource == 'commons').length,
        enabled ? 1 : 0);
    expect(paintings.map((x) => x.catalogKey).toSet().length,
        paintings.length);
  });
}
