import 'dart:convert';
import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/art_visual_color_selection.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:artdrift/services/art_offline_thumbnail_index.dart';
import 'package:artdrift/services/catalog_service.dart';

void main(){
  List<Artwork> catalog(int n)=>List.generate(n,(i)=>Artwork(
    id:i+1,title:'Painting '+i.toString(),artist:'Painter',date:'1900',
    imageId:'abcdefab-cdef-abcd-1234-abcd1234abcd',
    publicDomain:true,artworkType:'Painting',
    bootstrapAsset:'assets/gallery/thumbs/'+(i+1).toString()+'.webp'));
  String manifest(List<String> keys)=>jsonEncode({
    'schema_version':1,'selection':keys,'selected_count':keys.length,
    'actual_image_pixels_analyzed':true,'source_rights_policy_checked':true,
    'commercial_rights_certified':false,
  });
  test('valid selection preserves source IDs and visual ordering',(){
    final works=catalog(330);
    final keys=[for(var i=330;i>0;i--) 'aic:'+i.toString()];
    final selected=ArtVisualColorSelection.selectFromManifest(
      works,manifest(keys),imageBacked:(_)=>true);
    expect(selected.length,330);
    expect(selected.first.id,330);
    expect(selected.last.id,1);
  });
  test('missing thumbnails do not become empty canvas tiles',(){
    final works=catalog(400);
    final keys=[for(var i=1;i<=400;i++) 'aic:'+i.toString()];
    expect(ArtVisualColorSelection.selectFromManifest(
      works,manifest(keys),imageBacked:(_)=>false),isEmpty);
  });
  test('portrait share reduced at least 70 percent in compiled asset',() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final raw=await rootBundle.loadString(
      ArtVisualColorSelection.assetPath);
    final manifest=jsonDecode(raw) as Map<String,dynamic>;
    final policy=manifest['portrait_policy'] as Map<String,dynamic>;
    final before=policy['portrait_before'] as int;
    final after=policy['portrait_after'] as int;
    expect(before,greaterThan(0));
    expect(after * 10,lessThanOrEqualTo(before * 3));
    expect(policy['portraits_replaced'],before-after);
    expect(policy['new_image_files_added'],0);
    expect(policy['portraits_in_first_120'],lessThanOrEqualTo(9));
    expect(manifest['selected_count'],2400);
  });

  test('actual pinned museum pack yields 1200 fully image-backed works',() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    await ArtOfflineThumbnailIndex.instance.initialize();
    final catalog=CatalogService();
    addTearDown(catalog.close);
    final all=await catalog.load();
    // The original 2,400-tile visual selection must remain pinned, even as
    // the optional modern metadata catalog grows.
    expect(all.length,greaterThanOrEqualTo(4499));
    final chosen=await ArtVisualColorSelection.select(all);
    expect(chosen.length,2400);
    expect(chosen.every((a)=>a.hasBundledPreview ||
      ArtOfflineThumbnailIndex.instance.has(a)),isTrue);
    expect(chosen.map((a)=>a.catalogKey).toSet().length,2400);
    expect(chosen.any((a)=>a.artist.toLowerCase().contains('van gogh')),isTrue);
    expect(chosen.any((a)=>a.artist.toLowerCase().contains('matisse')),isTrue);
  });

  test('malformed and duplicate keys are rejected',(){
    final works=catalog(400);
    final keys=[for(var i=1;i<=400;i++) 'aic:'+i.toString()];
    keys[5]=keys[4];
    expect(()=>ArtVisualColorSelection.selectFromManifest(
      works,manifest(keys),imageBacked:(_)=>true),throwsFormatException);
    expect(()=>ArtVisualColorSelection.selectFromManifest(
      works,jsonEncode({'schema_version':0,'selection':keys}),
      imageBacked:(_)=>true),throwsFormatException);
  });
}
