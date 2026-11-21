import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/catalog_service.dart';
import 'package:artdrift/museums/museum_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('previous 385 offline thumbnails remain intact and provenance-verified', () async {
    final art = await const MuseumCatalog().bundled();
    final pinned = art.where((a) => a.hasBundledPreview).toList();
    expect(pinned.length, 385);
    expect(pinned.map((a) => a.museumSource).toSet(),
      containsAll({'met','cleveland','rijks','nga','smithsonian','getty'}));
    var totalBytes = 0;
    for (final a in pinned) {
      expect(a.displayable && a.hasBundledPreview, isTrue, reason:a.catalogKey);
      expect(a.title, isNotEmpty);
      expect(a.displayedMuseum, isNotEmpty);
      expect(a.museumNativeId, isNotEmpty);
      expect(a.rightsEvidenceUrl,startsWith('https://'));
      final bytes = await rootBundle.load(a.bootstrapAsset);
      expect(bytes.lengthInBytes, inInclusiveRange(250, 22000));
      totalBytes += bytes.lengthInBytes;
    }
    expect(totalBytes, lessThan(2600000));
    final getty = pinned.singleWhere((a) => a.museumSource == 'getty');
    expect(getty.title, 'Irises');
    expect(getty.artist, 'Vincent van Gogh');
    expect(getty.date, '1889');
  });

  test('global source-gated catalog has thousands of non-bundled real URL records',
      () async {
    final art=await const MuseumCatalog().bundled();
    final global=art.where((a) => !a.hasBundledPreview).toList();
    expect(global.length, greaterThanOrEqualTo(1200));
    expect(global.map((a)=>a.museumName).toSet().length,
      greaterThanOrEqualTo(7));
    expect(global.map((a)=>a.catalogKey).toSet().length, global.length);
    final metadata=await rootBundle.loadString('assets/museums/catalog_global.json');
    expect(metadata.length, lessThan(7500000));
    for (final a in global) {
      expect(a.displayable, isTrue, reason:a.catalogKey);
      expect(a.bootstrapAsset, isEmpty);
      expect(a.imageUrl(width:400).startsWith('https://'), isTrue);
      expect(a.title.trim(), isNotEmpty);
      expect(a.displayedMuseum.trim(),isNotEmpty);
      expect(a.museumNativeId.trim(),isNotEmpty);
      expect(a.rightsLicense.toLowerCase().contains('cc0') ||
         a.rightsLicense.toLowerCase().contains('public domain'),isTrue);
      expect(a.rightsEvidenceUrl, startsWith('https://'));
      final restored=Artwork.fromJson(a.toJson());
      expect(restored.catalogKey,a.catalogKey);
      expect(restored.museumNativeId,a.museumNativeId);
      expect(restored.shortDescription, contains(a.title));
    }
  });

  test('all 72 original works retained first in worldwide gallery', () async {
    final c=CatalogService();
    addTearDown(c.close);
    final originals=await c.bundled();
    final more=await const MuseumCatalog().bundled();
    final all=await c.load();
    expect(originals.length,72);
    expect(all.length, originals.length+more.length);
    for (var i=0;i<72;i++) {
      expect(all[i].catalogKey,originals[i].catalogKey);
      expect(all[i].hasBundledPreview,isTrue);
    }
    expect(all.map((a)=>a.catalogKey).toSet().length,all.length);
    expect(all.every((a)=>a.displayable),isTrue);
  });

  test('source host, rights and materials construct truthful captions', () {
    const art=Artwork(id:10000314,title:'Oil on Canvas',
      artist:'A. Painter',date:'1850',imageId:'',
      publicDomain:true,artworkType:'Painting',
      museumSource:'met',museumNativeId:'314',
      museumName:'The Metropolitan Museum of Art',
      rightsLicense:'CC0',rightsEvidenceUrl:'https://www.metmuseum.org/hubs/open-access',
      remotePreviewUrl:'https://images.metmuseum.org/works/i.jpg',
      medium:'Oil on canvas',dimensions:'45 x 70 cm');
    expect(art.displayable,isTrue);
    expect(art.hasBundledPreview,isFalse);
    expect(art.shortDescription,contains('Oil on canvas'));
    expect(art.shortDescription,contains('45 x 70 cm'));
    expect(art.shortDescription,contains('The Metropolitan'));
    expect(Artwork.officialImageUrl('https://images.metmuseum.org.evil.test/a.jpg',
      'met'),isFalse);
    expect(Artwork.officialImageUrl('http://images.metmuseum.org/a.jpg',
      'met'),isFalse);
    expect(Artwork.officialImageUrl('https://iiif.micr.io/id/full/400,/0/default.jpg',
      'rijks'),isTrue);
    expect(Artwork.officialImageUrl(
      'https://iip.smk.dk/iiif/jp2/id/full/300,/0/default.jpg','smk'),isTrue);
    expect(Artwork.fromJson({...art.toJson(),'is_public_domain':false})
      .displayable,isFalse);
  });
}
