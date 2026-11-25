import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import '../models/artwork.dart';
import 'art_offline_thumbnail_index.dart';

/// Deterministic offline image-backed color playlist; keeps original catalog.
class ArtVisualColorSelection {
  ArtVisualColorSelection._();
  static const assetPath='assets/museums/canvas_visual_color_v1.json';

  @visibleForTesting
  static List<Artwork> selectFromManifest(
      List<Artwork> catalog,String raw,{
      bool Function(Artwork)? imageBacked,
    }) {
    final parsed=jsonDecode(raw);
    if(parsed is! Map || parsed['schema_version']!=1 ||
       parsed['selection'] is! List ||
       parsed['actual_image_pixels_analyzed']!=true ||
       parsed['source_rights_policy_checked']!=true){
      throw const FormatException('Invalid color-first manifest');
    }
    final keys=parsed['selection'] as List;
    if(keys.length<300 || keys.length>4000 ||
       parsed['selected_count']!=keys.length){
      throw const FormatException('Color-first manifest count mismatch');
    }
    final byKey=<String,Artwork>{
      for(final art in catalog)
        if(art.displayable)art.catalogKey:art
    };
    final selected=<Artwork>[];
    final seen=<String>{};
    for(final key in keys){
      if(key is! String ||
         !RegExp(r'^[a-z]+:[0-9]+$').hasMatch(key) ||
         !seen.add(key)){
        throw const FormatException('Invalid or duplicate artwork key');
      }
      final art=byKey[key];
      if(art==null)continue;
      final available=imageBacked?.call(art) ??
          (art.hasBundledPreview || ArtOfflineThumbnailIndex.instance.has(art));
      if(available)selected.add(art);
    }
    if(selected.length<300)return const [];
    return List.unmodifiable(selected);
  }

  static Future<List<Artwork>> select(List<Artwork> catalog,
      {AssetBundle? bundle}) async{
    try{
      final raw=await (bundle??rootBundle).loadString(assetPath);
      return selectFromManifest(catalog,raw);
    }catch(error){
      if(kDebugMode)debugPrint('Color gallery unavailable: $error');
      return const [];
    }
  }
}
