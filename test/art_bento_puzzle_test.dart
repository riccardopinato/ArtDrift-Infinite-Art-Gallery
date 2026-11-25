import 'dart:ui';
import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:flutter_test/flutter_test.dart';

Artwork image(int i) => Artwork(
  id:i+1, title:i%13==0?'Flower landscape':'Painting',
  artist:'Artist', date:'1890',
  imageId:'01234567-0123-0123-0123-0123456789ab',
  publicDomain:true, artworkType:'Painting',
  imageWidth:i.isEven?800:600, imageHeight:i.isEven?600:800,
  bootstrapAsset:'assets/gallery/thumbs/'+(i+1).toString()+'.webp',
);

void main(){
  final art=List.generate(3200,image);
  final scores=<String,int>{
    for(var i=0;i<art.length;i++) art[i].catalogKey:i%256,
  };
  final world=ArtBentoWorld(art,scores);

  test('world has zero holes or overlaps, while whole painting fits',(){
    const view=Rect.fromLTWH(-1384.5,-2200.4,2771.3,4512.7);
    final tiles=world.visible(view,art.length,limit:2000);
    expect(tiles.length,greaterThan(50));
    var area=0.0;
    for(final t in tiles){
      final inside=t.rect.intersect(view);
      area+=inside.width*inside.height;
      expect((t.rect.width/t.rect.height -
          art[t.artworkIndex].naturalAspectRatio).abs(),
          lessThan(0.00000001));
    }
    expect((area-view.width*view.height).abs(),lessThan(0.01));
    for(var i=0;i<tiles.length;i++){
      for(var j=i+1;j<tiles.length;j++){
        expect(tiles[i].rect.overlaps(tiles[j].rect),false);
      }
    }
  });

  test('wide desktop region has unique work IDs and stable revisits',(){
    const view=Rect.fromLTWH(-2700,-2700,5400,5400);
    final a=world.visible(view,art.length,limit:1000);
    expect(a.length,greaterThan(250));
    expect(a.map((t)=>t.artworkIndex).toSet().length,a.length);
    final b=world.visible(view,art.length,limit:1000);
    String sig(dynamic t)=>t.key.toString()+'/'+
      t.artworkIndex.toString()+'/'+t.rect.toString();
    expect(a.map(sig).toList(),b.map(sig).toList());
  });

  test('four neighboring color bands span all 3200 items before cycling',(){
    final found=<int>{};
    for(final top in [0.0,260.0,610.0,825.0]){
      final row=world.visible(Rect.fromLTWH(0,top,1000000,1),
          art.length,limit:800);
      expect(row.length,800);
      expect(row.map((t)=>t.artworkIndex).toSet().length,800);
      found.addAll(row.map((t)=>t.artworkIndex));
    }
    expect(found.length,3200);
  });

  test('far negative and positive regions remain locally unique',(){
    const windows=[
      Rect.fromLTWH(-2000000,1000000,1800,1800),
      Rect.fromLTWH(1500000,-1200000,1800,1800),
      Rect.fromLTWH(-2700,-2700,1800,1800),
    ];
    for(final area in windows){
      final tiles=world.visible(area,art.length,limit:200);
      expect(tiles,isNotEmpty);
      expect(tiles.map((t)=>t.artworkIndex).toSet().length,tiles.length);
    }
  });

  test('zoom/prefetch priority keeps on-screen artworks under cap',(){
    const screen=Rect.fromLTWH(0,0,650,1000);
    const overdraw=Rect.fromLTWH(-1500,-1200,3500,3700);
    final essential=world.visible(screen,art.length,limit:180)
        .map((t)=>t.key).toSet();
    final capped=world.visible(overdraw,art.length,
        limit:180,priorityViewport:screen);
    expect(capped.length,lessThanOrEqualTo(180));
    expect(essential.difference(capped.map((t)=>t.key).toSet()),isEmpty);
  });
}
