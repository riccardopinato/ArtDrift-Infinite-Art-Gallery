import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/catalog_service.dart';
import 'package:artdrift/museums/museum_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Open Access museum records, full provenance, rights and tiny WebP', () async {
    final works = await const MuseumCatalog().bundled();
    expect(works.length, greaterThanOrEqualTo(385));
    expect(works.map((a) => a.museumSource).toSet(),
      containsAll({'met','cleveland','rijks','nga','smithsonian','getty'}));
    expect(works.map((a) => a.catalogKey).toSet().length, works.length);
    var total = 0;
    for (final art in works) {
      expect(art.displayable && art.hasBundledPreview, isTrue,
        reason: art.catalogKey);
      expect(art.title.trim(), isNotEmpty);
      expect(art.displayedMuseum.trim(), isNotEmpty);
      expect(art.museumNativeId.trim(), isNotEmpty);
      final license = art.rightsLicense.toLowerCase();
      expect(license.contains('cc0') || license.contains('public domain'), isTrue);
      expect(Uri.parse(art.rightsEvidenceUrl).scheme, 'https');
      expect(Artwork.officialImageUrl(art.remotePreviewUrl,art.museumSource),isTrue);
      expect(art.shortDescription, contains(art.title));
      final restored=Artwork.fromJson(art.toJson());
      expect(restored.catalogKey, art.catalogKey);
      expect(restored.dimensions, art.dimensions);
      expect(restored.displayedMuseum, art.displayedMuseum);
      final blob=await rootBundle.load(art.bootstrapAsset);
      expect(blob.lengthInBytes, greaterThan(249));
      expect(blob.lengthInBytes, lessThanOrEqualTo(22000));
      total += blob.lengthInBytes;
    }
    final getty = works.where((w) => w.museumSource == 'getty').toList();
    expect(getty, isNotEmpty);
    expect(getty.first.title, 'Irises');
    expect(getty.first.artist, 'Vincent van Gogh');
    expect(getty.first.date, '1889');
    expect(getty.first.rightsEvidenceUrl,
      startsWith('https://media.getty.edu/iiif/manifest/3/'));
    expect(total, lessThanOrEqualTo(2600000));
  });

  test('72 AIC paintings remain first and international are really in canvas', () async {
    final service=CatalogService();
    addTearDown(service.close);
    final local=await service.bundled();
    final museum=await const MuseumCatalog().bundled();
    expect(local.length,72);
    final all=await service.load();
    expect(all.length,local.length+museum.length);
    for (var i=0;i<local.length;i++) {
      expect(all[i].catalogKey,local[i].catalogKey);
    }
    expect(all.map((a)=>a.catalogKey).toSet().length,all.length);
    expect(all.every((a)=>a.hasBundledPreview),isTrue);
  });

  test('source host, license and materials captured in fact-only description', () {
    const art=Artwork(id:10000314,title:'Oil on Canvas',artist:'Painter',
      date:'1850',imageId:'',publicDomain:true,artworkType:'Painting',
      museumSource:'met',museumNativeId:'314',
      museumName:'The Metropolitan Museum of Art',
      rightsLicense:'CC0',rightsEvidenceUrl:'https://www.metmuseum.org/hubs/open-access',
      remotePreviewUrl:'https://images.metmuseum.org/works/i.jpg',
      medium:'Oil on canvas',dimensions:'45 x 70 cm',
      bootstrapAsset:'assets/museums/thumbs/met_10000314.webp');
    expect(art.displayable,isTrue);
    expect(art.hasBundledPreview,isTrue);
    expect(art.shortDescription,contains('Oil on canvas'));
    expect(art.shortDescription,contains('45 x 70 cm'));
    expect(art.shortDescription,contains('The Metropolitan'));
    expect(Artwork.officialImageUrl('https://images.metmuseum.org.evil.test/a.jpg',
      'met'),isFalse);
    expect(Artwork.officialImageUrl('http://images.metmuseum.org/a.jpg',
      'met'),isFalse);
    expect(Artwork.officialImageUrl('https://iiif.micr.io/id/full/400,/0/default.jpg',
      'rijks'),isTrue);
    expect(Artwork.fromJson({...art.toJson(),'is_public_domain':false})
      .displayable,isFalse);
  });
}
