import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/museums/museum_catalog.dart';
void main(){
 TestWidgetsFlutterBinding.ensureInitialized();
 const nga=bool.fromEnvironment('ARTDRIFT_ENABLE_INSTITUTIONAL_NGA',defaultValue:false);
 const commons=bool.fromEnvironment('ARTDRIFT_ENABLE_CURATED_COMMONS',defaultValue:false);
 test('NGA official 29 image-level CC0 rights and stable identity',() async {
  final list=jsonDecode(await rootBundle.loadString(
    'assets/museums/catalog_nga_openaccess_20261127.json')) as List<dynamic>;
  expect(list.length,29);
  expect(list.map((x)=>(x as Map)['source_identity']).toSet().length,29);
  for(final item in list){
   final a=Artwork.fromJson(Map<String,dynamic>.from(item as Map));
   expect(a.isCuratedOfficialNga,isTrue);
   expect(a.rightsLicense,'CC0 1.0');
   expect(a.curatedNgaRightsEvidenceComplete,isTrue);
   expect(a.curatedNgaReleaseReady,nga);
   expect(a.displayable,nga);
   expect(a.wallpaperAllowed,isFalse);
   expect(a.museumUrl,startsWith('https://www.nga.gov/'));
   expect(a.imageUrl(width:400),startsWith('https://api.nga.gov/iiif/'));
   expect(a.imageUrl(width:843),startsWith('https://api.nga.gov/iiif/'));
   expect(a.imageAttribution,contains('National Gallery of Art'));
   expect(a.rightsReviewReference,isNotEmpty);
   expect(Artwork.fromJson(a.toJson()).sourceIdentity,a.sourceIdentity);
  }
 });
 test('No NGA records visible without independent explicit build flag',() async {
  final catalog=await const MuseumCatalog().bundled();
  expect(catalog.length,4428+(commons?5:0)+(nga?29:0));
  expect(catalog.where((x)=>x.isCuratedOfficialNga).length,nga?29:0);
  expect(catalog.map((x)=>x.catalogKey).toSet().length,catalog.length);
 });
 test('New NGA items fail closed when licensing or ID changes',(){
  final input={
   'id':4000045872,'museum_source':'nga','museum_native_id':'45872',
   'source_identity':'nga:45872','title':'Morning Haze','artist_title':'Claude Monet',
   'is_public_domain':true,'artwork_type_title':'Painting',
   'museum_name':'National Gallery of Art, Washington',
   'remote_preview_url':'https://api.nga.gov/iiif/36bd94fc-291f-43cb-9fd4-7b391fe3f0e5/full/!600,600/0/default.jpg',
   'remote_full_url':'https://api.nga.gov/iiif/36bd94fc-291f-43cb-9fd4-7b391fe3f0e5/full/!1600,1600/0/default.jpg',
   'remote_museum_url':'https://www.nga.gov/collection/art-object-page.45872.html',
   'rights_evidence_url':'https://www.nga.gov/artworks/free-images-and-open-access',
   'rights_license':'CC0 1.0','image_license_url':'https://creativecommons.org/publicdomain/zero/1.0/',
   'image_creator':'National Gallery of Art','image_attribution':'Claude Monet, Morning Haze, NGA',
   'credit_line':'Chester Dale Collection','commercially_approved':true,
   'source_provenance_verified':true,'worldwide_distribution_reviewed':true,
   'rights_review_reference':'docs/ARTDRIFT_NGA_29_OPEN_ACCESS_SOURCE_VERIFIED_20261127.md'
  };
  final good=Artwork.fromJson(input);
  expect(good.curatedNgaRightsEvidenceComplete,isTrue);
  for(final corrupt in [
    {'commercially_approved':false},{'rights_license':'CC BY-NC 4.0'},
    {'source_provenance_verified':false},{'museum_native_id':'45873'},
    {'remote_preview_url':'https://api.nga.gov.attacker.test/iiif/invalid'},
    {'rights_evidence_url':'https://fake.nga.gov/policy'},
    {'image_attribution':''},{'image_license_url':''},
  ]){
   final work=Artwork.fromJson({...input,...corrupt});
   expect(work.displayable,isFalse,reason:corrupt.toString());
  }
 });
}
