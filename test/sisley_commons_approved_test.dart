import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/museums/museum_catalog.dart';
void main() {
 TestWidgetsFlutterBinding.ensureInitialized();
 const enabled=bool.fromEnvironment('ARTDRIFT_ENABLE_CURATED_COMMONS',defaultValue:false);
 const ids={'commons:57672559','commons:52129968','commons:52132342','commons:80548151'};
 test('all four file-specific rights records are traceable',() async {
  final list=jsonDecode(await rootBundle.loadString(
    'assets/museums/catalog_curated_commons.json')) as List<dynamic>;
  expect(list.length,4);
  expect(list.map((x)=>(x as Map)['source_identity']).toSet(),ids);
  for(final raw in list){
   final m=Map<String,dynamic>.from(raw as Map);
   expect(m['commercially_approved'],isTrue);
   expect(m['source_provenance_verified'],isTrue);
   expect(m['worldwide_distribution_reviewed'],isTrue);
   expect(m['rights_review_reference'],isNotEmpty);
   final a=Artwork.fromJson(m);
   expect(a.curatedCommonsRightsEvidenceComplete,isTrue);
   expect(a.curatedCommonsReleaseReady,enabled);
   expect(a.displayable,enabled);
   expect(a.imageUrl(width:400),startsWith('https://'));
   expect(a.imageAttribution,isNotEmpty);
   expect(a.wallpaperAllowed,isFalse);
  }
 });
 test('bundled museum catalog stays stable when disabled',() async {
  final paintings=await const MuseumCatalog().bundled();
  expect(paintings.length,4428+(enabled?4:0));
  expect(paintings.where((x)=>x.museumSource=='commons').length,enabled?4:0);
  expect(paintings.map((x)=>x.catalogKey).toSet().length,paintings.length);
 });
}
