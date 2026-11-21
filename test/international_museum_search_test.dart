import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/search/gallery_search.dart';
import 'package:artdrift/search/museum_search.dart';

void main() {
  test('Met is source-allowlisted and public domain only', () {
    final base = <String, dynamic>{
      'objectID': 123, 'isPublicDomain': true, 'classification': 'Paintings',
      'title': 'A Garden', 'artistDisplayName': 'Author',
      'primaryImageSmall': 'https://images.metmuseum.org/CRDImages/ep/web-large/X.jpg',
      'tags': [{'term': 'Garden'}],
    };
    final valid = MuseumSearchService.parseMet(base);
    expect(valid?.museumSource, 'met');
    expect(valid?.catalogKey, 'met:10000123');
    expect(MuseumSearchService.parseMet({...base, 'isPublicDomain': false}), isNull);
    expect(MuseumSearchService.parseMet({...base,
      'primaryImageSmall': 'https://evil.test/image.jpg'}), isNull);
    expect(MuseumSearchService.parseMet({...base,
      'classification': 'Photographs'}), isNull);
  });

  test('Cleveland requires image + CC0', () {
    final base = <String, dynamic>{
      'id': 123, 'share_license_status': 'CC0', 'type': 'Painting',
      'title': 'Park', 'images': {'web': {
        'url': 'https://openaccess-cdn.clevelandart.org/images/art.jpg'}},
    };
    expect(MuseumSearchService.parseCleveland(base)?.museumSource, 'cleveland');
    expect(MuseumSearchService.parseCleveland({...base,
      'share_license_status': 'Copyrighted'}), isNull);
    expect(MuseumSearchService.parseCleveland({...base, 'images': {
      'web': {'url': 'http://openaccess-cdn.clevelandart.org/image.jpg'}}}), isNull);
  });

  test('museum search is explicit, bounded, source unique and rights filtered', () async {
    var calls = 0;
    final mock = MockClient((req) async {
      calls++;
      if (req.url.host == 'collectionapi.metmuseum.org') {
        if (req.url.path.endsWith('/search')) {
          expect(req.url.path, contains('v1.1'));
          return http.Response(jsonEncode({'objectIDs': [123]}), 200);
        }
        return http.Response(jsonEncode({
          'objectID': 123, 'isPublicDomain': true, 'classification': 'Paintings',
          'title': 'A park', 'primaryImageSmall': 'https://images.metmuseum.org/a.jpg',
        }), 200);
      }
      return http.Response(jsonEncode({'data': [{
        'id': 4, 'share_license_status': 'CC0', 'type': 'Painting',
        'title': 'Park', 'images': {'web': {'url':
          'https://openaccess-cdn.clevelandart.org/x.jpg'}},
      }]}), 200);
    });
    final service = MuseumSearchService(client: mock);
    addTearDown(service.close);
    expect(calls, 0);
    final result = await service.search('parco', ArtworkSearchScope.subject);
    expect(result.map((a) => a.museumSource).toSet(), {'met', 'cleveland'});
    expect(calls, 3);
  });

  test('bad provider URL is not a displayable artwork', () {
    expect(Artwork.officialImageUrl('https://images.metmuseum.org.evil.test/a.jpg', 'met'), isFalse);
    expect(Artwork.officialImageUrl('http://images.metmuseum.org/a.jpg', 'met'), isFalse);
  });
}
