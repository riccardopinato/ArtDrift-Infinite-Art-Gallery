import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/models/art_creation_date.dart';
import 'package:artdrift/collections/art_collections.dart';
import 'package:artdrift/museums/museum_catalog.dart';
import 'package:artdrift/services/catalog_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const museums = <String, String>{
    'chndm': 'Cooper Hewitt, Smithsonian Design Museum',
    'hmsg': 'Hirshhorn Museum and Sculpture Garden',
    'nmafa': 'Smithsonian National Museum of African Art',
    'nmaahc':
      'Smithsonian National Museum of African American History and Culture',
  };

  test('new museum catalog keeps four distinct source-verified institutions',
      () async {
    final raw = jsonDecode(await rootBundle.loadString(
        'assets/museums/catalog_new_museums.json')) as List<dynamic>;
    // Import diagnostic report stays out of the customer APK asset bundle.
    final report = jsonDecode(await File(
        'assets/museums/new_museums_report.json').readAsString())
        as Map<String,dynamic>;
    expect(raw.length, report['record_count']);
    expect(raw.length, greaterThanOrEqualTo(400));
    expect(raw.map((item) => (item as Map)['id']).toSet().length, raw.length);
    expect(report['museums_added'], 4);
    final newArtworks = raw.map((r) => Artwork.fromJson(
        Map<String, dynamic>.from(r as Map))).toList(growable: false);
    final found = <String>{};
    for (final art in newArtworks) {
      expect(art.museumSource, 'smithsonian');
      expect(art.displayable, isTrue, reason: art.catalogKey);
      expect(art.hasBundledPreview, isFalse);
      expect(art.rightsLicense, 'CC0');
      expect(art.publicDomain, isTrue);
      expect(art.rightsEvidenceUrl, 'https://www.si.edu/openaccess');
      expect(art.remotePreviewUrl, startsWith('https://ids.si.edu/'));
      expect(art.museumNativeId, contains(':'));
      expect(art.museumUrl, startsWith('https://'));
      found.add(art.museumName);
      expect(art.shortDescription, contains(art.museumName));
      expect(Artwork.fromJson(art.toJson()).catalogKey, art.catalogKey);
    }
    expect(found, museums.values.toSet());
    expect(newArtworks.where((a) =>
      ArtCreationDate.explicitYearFrom1950(a.date) != null).length,
      report['post_1950_records']);
  });

  test('each genuinely new museum is a discoverable collection in six locales',
      () async {
    final artworks = await const MuseumCatalog().bundled();
    final expected = <String, String>{
      'museum-cooper-hewitt': museums['chndm']!,
      'museum-hirshhorn': museums['hmsg']!,
      'museum-african-art': museums['nmafa']!,
      'museum-african-american-history': museums['nmaahc']!,
    };
    final available = ArtCollections.available(artworks);
    for (final item in expected.entries) {
      final collection = available.singleWhere((c) => c.id == item.key);
      final members = ArtCollections.members(collection, artworks);
      expect(members.length, greaterThanOrEqualTo(3));
      expect(members.every((a) => a.museumName == item.value), isTrue);
      for (final language in const ['it','en','fr','es','de','pt']) {
        expect(collection.title(language), isNotEmpty);
        expect(collection.subtitle(language), isNotEmpty);
      }
    }
  });

  test('historical paintings and favorites IDs stay intact after new museums',
      () async {
    final service = CatalogService();
    addTearDown(service.close);
    final originals = await service.bundled();
    final all = await service.load();
    expect(originals.length, 72);
    expect(all.take(72).map((a) => a.catalogKey).toList(),
        originals.map((a) => a.catalogKey).toList());
    expect(all.map((a) => a.catalogKey).toSet().length, all.length);
    expect(all.where((a) =>
      const ['chndm:', 'hmsg:', 'nmafa:', 'nmaahc:']
          .any((prefix) => a.museumNativeId.startsWith(prefix))).length,
      greaterThanOrEqualTo(400));
  });

  test('new museum non-painting gate cannot spoof an unrelated institution', () {
    Artwork item({String museumName = 'Hirshhorn Museum and Sculpture Garden',
                  String medium = 'Sculpture',
                  String native = 'hmsg:hmsg_123',
                  String rights = 'CC0'}) =>
        Artwork(id:60000123,title:'Art',artist:'Creator',date:'1968',
          imageId:'',publicDomain:true,artworkType:medium,
          museumSource:'smithsonian',museumNativeId:native,
          museumName:museumName,rightsLicense:rights,
          remotePreviewUrl:'https://ids.si.edu/ids/deliveryService?id=X',
          rightsEvidenceUrl:'https://www.si.edu/openaccess');

    expect(item().displayable, isTrue);
    expect(item(medium:'Fossil specimen').displayable, isFalse);
    expect(item(rights:'Copyrighted').displayable, isFalse);
    expect(item(museumName:'Other institution').displayable, isFalse);
    expect(item(native:'unknown:123').displayable, isFalse);
  });
}
