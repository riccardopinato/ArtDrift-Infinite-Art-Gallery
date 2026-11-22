import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:artdrift/services/moma_cloud_catalog.dart';

void main() {
  test('missing API URL prevents additional cloud requests',(){
    final service=MomaCloudCatalog(baseUrl:'');
    expect(service.enabled,false);
    service.close();
  });
  test('untrusted record URL and unlicensed image are blocked',(){
    expect(MomaCatalogWork.parse({
      'id':14,'source_url':'https://www.moma.org.evil.test/collection/works/14',
      'title':'bad'}),null);
    expect(MomaCatalogWork.parse({
      'id':14,'source_url':'https://www.moma.org/collection/works/14',
      'title':'ok','thumbnail_url':'https://img.example/art.webp',
      'image_rights':'NOT_INCLUDED_NOT_LICENSED'})?.thumbnailUrl,null);
  });
  test('API pagination and MoMA source guard',() async {
    final service=MomaCloudCatalog(baseUrl:'https://catalog.example',
      client:MockClient((request) async{
        expect(request.url.path,'/api/v1/search');
        expect(request.url.queryParameters['q'],'Van Gogh');
        expect(request.url.queryParameters['scope'],'artist');
        return http.Response(jsonEncode({
          'source':'MoMA','next_cursor':'24',
          'works':[
            {'id':111,'title':'Art','artist':'Van Gogh','date':'1889',
              'medium':'Oil','dimensions':'20 cm','department':'Painting',
              'source_url':'https://www.moma.org/collection/works/111',
              'thumbnail_url':null},
          ],
        }),200);
      }));
    final page=await service.search('Van Gogh',scope:'artist');
    expect(page.works.length,1);
    expect(page.nextCursor,'24');
    expect(page.works.first.thumbnailUrl,null);
    service.close();
  });
}
