import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/museums/museum_catalog.dart';
void main(){
  TestWidgetsFlutterBinding.ensureInitialized();
  const review = bool.fromEnvironment('ARTDRIFT_INTERNAL_ART_REVIEW',
      defaultValue: false);
  test('Research metadata never counts as independently cleared rights',(){
    final w=Artwork.fromJson({
      'id':123,'title':'Painting', 'artist_title':'Alfred Sisley',
      'museum_source':'commons','museum_native_id':'123',
      'source_identity':'commons:123', 'is_public_domain':true,
      'artwork_type_title':'Painting',
      'remote_preview_url':'https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/500px-Example.jpg',
      'remote_museum_url':'https://commons.wikimedia.org/wiki/File:Example.jpg',
      'rights_evidence_url':'https://commons.wikimedia.org/wiki/File:Example.jpg',
      'rights_license':'Public Domain',
      'credit_line':'Credit','image_attribution':'Wikimedia Commons',
      'artdrift_research_only':true,
      'commercially_approved':false,'source_provenance_verified':false,
      'worldwide_distribution_reviewed':false,
    });
    expect(w.researchOnly,isTrue);
    expect(w.internalResearchVisible,review);
    expect(w.curatedCommonsRightsEvidenceComplete,isFalse);
    expect(w.curatedCommonsReleaseReady,isFalse);
    expect(w.wallpaperAllowed,isFalse);
    expect(Artwork.fromJson(w.toJson()).researchOnly,isTrue);
  });
  test('Default build ships zero internal research cards',() async {
    if(review)return;
    final data=jsonDecode(await rootBundle.loadString(
      'assets/museums/catalog_curated_commons_review.json')) as List<dynamic>;
    expect(data,isEmpty);
  });
  test('283 unapproved candidates render ONLY in test build',
      skip:!review,() async {
    final raw=jsonDecode(await rootBundle.loadString(
      'assets/museums/catalog_curated_commons_review.json')) as List<dynamic>;
    expect(raw.length,283);
    final works=raw.map((o)=>Artwork.fromJson(
      Map<String,dynamic>.from(o as Map))).toList();
    expect(works.map((x)=>x.sourceIdentity).toSet().length,283);
    for(final a in works){
      expect(a.researchOnly,isTrue);
      expect(a.commerciallyApproved,isFalse);
      expect(a.provenanceVerified,isFalse);
      expect(a.curatedCommonsRightsEvidenceComplete,isFalse);
      expect(a.curatedCommonsReleaseReady,isFalse);
      expect(a.internalResearchVisible,isTrue);
      expect(a.displayable,isTrue);
    }
    final museum=await const MuseumCatalog().bundled();
    expect(museum.length,4428+1+283);
    expect(museum.where((x)=>x.researchOnly).length,283);
    expect(museum.where((x)=>x.catalogKey=='commons:57672559').length,1);
  });
}
