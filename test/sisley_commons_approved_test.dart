import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/museums/museum_catalog.dart';
void main(){
 TestWidgetsFlutterBinding.ensureInitialized();
 const enabled=bool.fromEnvironment('ARTDRIFT_ENABLE_CURATED_COMMONS',defaultValue:false);
 const ids={
 'commons:57672559','commons:52129968','commons:52132342','commons:80548151',
 'commons:80538945'
 };
 test('six curated Commons photographs have independent provenance',() async {
  final list=jsonDecode(await rootBundle.loadString(
    'assets/museums/catalog_curated_commons.json')) as List<dynamic>;
  expect(list.length,5);
  expect(list.map((x)=>(x as Map)['source_identity']).toSet(),ids);
  for(final entry in list){
   final a=Artwork.fromJson(Map<String,dynamic>.from(entry as Map));
   expect(a.curatedCommonsRightsEvidenceComplete,isTrue);
   expect(a.curatedCommonsReleaseReady,enabled);
   expect(a.displayable,enabled);
   expect(a.imageAttribution,isNotEmpty);
   expect(a.rightsReviewReference,isNotEmpty);
   expect(a.wallpaperAllowed,isFalse);
  }
  for(final id in ['commons:80538945']){
   final a=Artwork.fromJson(Map<String,dynamic>.from(
    list.firstWhere((x)=>(x as Map)['source_identity']==id) as Map));
   expect(a.rightsLicense,'CC0 1.0');
   expect(a.imageLicenseUrl,'https://creativecommons.org/publicdomain/zero/1.0/');
   expect(a.imageUrl(width:900),startsWith('https://upload.wikimedia.org/'));
  }
 });
 test('bundled museum catalog stays stable unless explicit release build flag',() async {
  final paintings=await const MuseumCatalog().bundled();
  expect(paintings.length,4428+(enabled?5:0));
  expect(paintings.where((x)=>x.museumSource=='commons').length,enabled?5:0);
  expect(paintings.map((x)=>x.catalogKey).toSet().length,paintings.length);
 });
}
