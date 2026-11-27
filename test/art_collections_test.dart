import 'package:flutter_test/flutter_test.dart';

import 'package:artdrift/collections/art_collections.dart';
import 'package:artdrift/models/artwork.dart';

Artwork art(int id, String title, {String date = '', String source = 'met',
    List<String> subjects = const [], bool publicDomain = true}) => Artwork(
  id: id,
  title: title,
  date: date,
  artist: 'Artist',
  imageId: '',
  publicDomain: publicDomain,
  artworkType: 'Painting',
  museumSource: source,
  remotePreviewUrl: source == 'met'
      ? 'https://images.metmuseum.org/CRDImages/ep/test.jpg'
      : 'https://openaccess-cdn.clevelandart.org/test.jpg',
  subjectTerms: subjects,
);

void main() {
  test('six localizations and stable collection IDs are present', () {
    final ids = <String>{};
    for (final collection in ArtCollections.all) {
      expect(ids.add(collection.id), isTrue);
      for (final language in ['it','en','fr','es','de','pt']) {
        expect(collection.title(language).trim(), isNotEmpty);
        expect(collection.subtitle(language).trim(), isNotEmpty);
      }
    }
  });

  test('a collection never substitutes an unrelated museum artwork', () {
    final portraits = ArtCollections.all.singleWhere((x) => x.id == 'portraits');
    final candidate = art(100, 'Portrait of an artist', date: '1885');
    final unrelated = art(101, 'River bank', date: '1910');
    final denied = art(102, 'Portrait of a stranger', publicDomain: false);
    final matches = ArtCollections.members(portraits,
        [candidate, unrelated, denied]);
    expect(matches.map((x) => x.catalogKey), ['met:100']);
  });

  test('subject token matching avoids false positive substrings', () {
    final marine = ArtCollections.all.singleWhere((x) => x.id == 'seascapes');
    expect(marine.contains(art(1, 'Season of flowers')), isFalse);
    expect(marine.contains(art(2, 'Sea and coast')), isTrue);
    expect(marine.contains(art(3, 'Untitled',
        subjects: ['River', 'Landscape'])), isTrue);
  });

  test('period filters use explicit museum dates rather than guessed styles', () {
    final c19 = ArtCollections.all.singleWhere(
        (x) => x.id == 'nineteenth-century');
    final c20 = ArtCollections.all.singleWhere(
        (x) => x.id == 'twentieth-century');
    expect(c19.contains(art(1, 'Unknown', date: 'circa 1881')), isTrue);
    expect(c19.contains(art(2, 'Unknown', date: 'Unknown')), isFalse);
    expect(c20.contains(art(3, 'Unknown', date: '1902–1905')), isTrue);
    expect(c19.contains(art(4, 'Unknown', date: '2001')), isFalse);
  });

  test('museum groups are based on canonical source identity only', () {
    final c = ArtCollections.all.singleWhere((x) => x.id == 'museum-met');
    expect(c.contains(art(5, 'Landscape', source: 'met')), isTrue);
    expect(c.contains(art(6, 'Landscape', source: 'cleveland')), isFalse);
  });

  test('empty/small groups are hidden from discovery', () {
    final options = ArtCollections.available(
      [art(1,'Portrait'),art(2,'Portrait'),art(3,'Portrait')],
      minMembers: 3);
    expect(options.any((x) => x.id == 'portraits'), isTrue);
    expect(options.any((x) => x.id == 'seascapes'), isFalse);
  });
  test('documented multilingual scene terms enrich collections without guesses', () {
    final seascapes = ArtCollections.all.singleWhere(
      (c) => c.id == 'seascapes');
    final landscapes = ArtCollections.all.singleWhere(
      (c) => c.id == 'landscapes');
    final flowers = ArtCollections.all.singleWhere(
      (c) => c.id == 'flowers');
    expect(seascapes.contains(art(51, 'Cascata nel bosco')), isTrue);
    expect(landscapes.contains(art(52, 'Mountain valley')), isTrue);
    expect(flowers.contains(art(53, 'Tulips in a vase')), isTrue);
    expect(seascapes.contains(art(54, 'Oceania portrait')), isFalse);
  });

}
