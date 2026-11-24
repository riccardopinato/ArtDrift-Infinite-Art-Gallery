import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:artdrift/services/museum_cloud_catalog.dart';

void main(){
  test('unconfigured D1 remains offline with no additional requests',(){
    final source=MuseumCloudCatalog(baseUrl:'');
    expect(source.enabled,isFalse);
    source.close();
  });

  test('new approved-modern D1 browsing is disabled by default',() async {
    final client=MockClient((_req) async {
      fail('must not send a request while release gate is disabled');
    });
    final catalog=MuseumCloudCatalog(baseUrl:'https://d1.example',client:client);
    expect(catalog.approvedModernEnabled,isFalse);
    await expectLater(catalog.approvedModern(),throwsStateError);
    catalog.close();
  });

  test('museum metadata preserves attribution and rejects unsafe media',(){
    final row={
      'source_key':'commons:10000012',
      'museum_source':'commons','museum_name':'Wikimedia Commons',
      'title':'Modern Art','artist':'Artist','date':'2020',
      'medium':'Painting','rights_license':'CC BY-SA 4.0',
      'rights_evidence_url':'https://commons.wikimedia.org/wiki/File:Art.jpg',
      'credit_line':'Artist · CC BY-SA 4.0',
      'source_url':'https://commons.wikimedia.org/wiki/File:Art.jpg',
      'thumbnail_url':'https://upload.wikimedia.org/example.jpg',
    };
    final work=MuseumCloudWork.parse(row)!;
    expect(work.title,'Modern Art');
    expect(work.imageUrl,isNull); // Unreviewed metadata search MUST NOT display images
    expect(work.sourceUrl,startsWith('https://commons.wikimedia.org/'));
    expect(MuseumCloudWork.parse({...row,'rights_license':'CC BY-NC 4.0'}),isNull);
    expect(MuseumCloudWork.parse({...row,'rights_license':'CC0 1.0'})?.title,'Modern Art');
    expect(MuseumCloudWork.parse({...row,'source_key':'evil.test:12'}),isNull);
    expect(MuseumCloudWork.parse({...row,'thumbnail_url':'https://upload.wikimedia.org.evil.test/a.jpg'},allowImage:true)?.imageUrl,isNull);
  });

  test('read-only museum D1 search is paginated and source-validated',() async {
    final client=MockClient((req)async {
      expect(req.url.path,'/api/v1/museum-search');
      expect(req.url.queryParameters['scope'],'artist');
      expect(req.url.queryParameters['q'],'artist');
      return http.Response(jsonEncode({
        'source':'ArtDrift-Museums','next_cursor':'24',
        'works':[{
          'source_key':'met:991','museum_source':'met',
          'title':'Painting','museum_name':'The Metropolitan Museum of Art',
          'artist':'Artist','date':'1890','medium':'Painting',
          'rights_license':'CC0',
          'rights_evidence_url':'https://www.metmuseum.org/about-the-met/policies-and-documents/open-access',
          'source_url':'https://www.metmuseum.org/art/collection/search/991',
          'thumbnail_url':'https://images.metmuseum.org/a.jpg'
        }],
      }),200);
    });
    final catalog=MuseumCloudCatalog(baseUrl:'https://d1.example',client:client);
    final result=await catalog.search('artist',scope:'artist');
    expect(result.works.length,1);
    expect(result.works.single.museum,'The Metropolitan Museum of Art');
    expect(result.nextCursor,'24');
    expect(result.works.single.imageUrl,isNull);
    catalog.close();
  });
}
