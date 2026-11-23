import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/art_creation_date.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/collections/art_collections.dart';

void main() {
  Artwork commons({
    String date = '2023',
    String license = 'CC BY-SA 4.0',
    bool isPublicDomain = false,
    String thumb = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/img.jpg/400px-img.jpg',
  }) => Artwork(
      id: 10000001234,
      title: 'Self-authored Color Field',
      artist: 'Artist from original upload',
      date: date,
      imageId: '',
      publicDomain: isPublicDomain,
      artworkType: 'Painting',
      museumSource: 'commons',
      museumNativeId: '1234',
      museumName: 'Wikimedia Commons · Artist uploads',
      rightsLicense: license,
      rightsLicenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/',
      rightsEvidenceUrl: 'https://commons.wikimedia.org/wiki/File:Art.jpg',
      remotePreviewUrl: thumb,
      remoteMuseumUrl: 'https://commons.wikimedia.org/wiki/File:Art.jpg',
      creditLine: 'Artist · CC BY-SA 4.0');

  test('1950+ date filter excludes boundary-spanning and uncertain dates', () {
    expect(ArtCreationDate.explicitYearFrom1950('1950'), 1950);
    expect(ArtCreationDate.explicitYearFrom1950('1955–1957'), 1955);
    expect(ArtCreationDate.explicitYearFrom1950('1949–1951'), isNull);
    expect(ArtCreationDate.explicitYearFrom1950('late 20th century'), isNull);
    expect(ArtCreationDate.explicitYearFrom1950('1887'), isNull);
    expect(ArtCreationDate.explicitYearFrom1950('2027'), isNull);
  });

  test('independently licensed modern art never becomes fake public domain', () {
    final modern = commons();
    expect(modern.publicDomain, isFalse);
    expect(modern.displayable, isTrue);
    expect(modern.displayedLicense, 'CC BY-SA 4.0');
    expect(modern.museumUrl, startsWith('https://commons.wikimedia.org/'));
    expect(modern.shortDescription, contains('Wikimedia Commons'));
    expect(modern.catalogKey, 'commons:10000001234');
    expect(Artwork.fromJson(modern.toJson()).displayable, isTrue);
    expect(ArtCollections.matches(
        ArtCollections.all.firstWhere((item) =>
          item.id == 'modern-from-1950'), modern), isTrue);
  });

  test('Commons gate rejects unknown license, wrong flag, old and evil hosts', () {
    expect(commons(license:'CC BY-NC 4.0').displayable, isFalse);
    expect(commons(isPublicDomain:true).displayable, isFalse);
    expect(commons(date:'1944').displayable, isFalse);
    expect(commons(thumb:'https://upload.wikimedia.org.evil.test/i.jpg')
        .displayable, isFalse);
    expect(commons(thumb:'http://upload.wikimedia.org/i.jpg')
        .displayable, isFalse);
  });

  test('Commons technical source markers never appear as art titles', () {
    final dirty = {
      ...commons().toJson(),
      'title': 'German: Allegorie des Herbstes label QS:Lde, 1983',
    };
    expect(Artwork.fromJson(dirty).title, 'Allegorie des Herbstes');
    expect(commons().title, 'Self-authored Color Field');
  });

  test('historic museums retain public domain gate', () {
    final historic = Artwork(id: 10000099, title:'Historic Work',
      artist:'Artist', date:'1880', imageId:'',
      publicDomain:false, museumSource:'met',
      artworkType:'Painting',
      remotePreviewUrl:'https://images.metmuseum.org/paint.jpg');
    expect(historic.displayable, isFalse);
  });
}
