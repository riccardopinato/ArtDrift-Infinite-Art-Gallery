import 'dart:ui';
import 'package:artdrift/canvas/art_bento_world.dart';
import 'package:artdrift/models/artwork.dart';
import 'package:flutter_test/flutter_test.dart';

Artwork sample(int i) => Artwork(
  id: i + 1, title: i % 7 == 0 ? 'Flower landscape' : 'Painting',
  artist: 'Artist', date: '1890',
  imageId: '01234567-0123-0123-0123-0123456789ab',
  publicDomain: true, artworkType: 'Painting',
  imageWidth: i.isEven ? 800 : 600,
  imageHeight: i.isEven ? 600 : 800,
  bootstrapAsset: 'assets/gallery/thumbs/' + (i + 1).toString() + '.webp',
);

void main() {
  final items = List.generate(240, sample);
  final pixels = <String,int>{
    for (var i = 0; i < items.length; i++) items[i].catalogKey: i,
  };
  final mosaic = ArtBentoWorld(items, pixels);

  test('natural shape and visible size variation', () {
    final tiles = mosaic.visible(const Rect.fromLTWH(0,0,3150,3150),
        items.length,limit:1000);
    expect(tiles.length,greaterThan(90));
    expect(tiles.map((t)=>t.rect.height).toSet().length,greaterThan(5));
    expect(tiles.map((t)=>t.rect.width).toSet().length,greaterThan(6));
    expect(tiles.any((t)=>t.rect.width>t.rect.height),true);
    expect(tiles.any((t)=>t.rect.height>t.rect.width),true);
    for(final t in tiles) {
      expect((t.rect.width/t.rect.height -
          items[t.artworkIndex].naturalAspectRatio).abs(),
          lessThan(0.00000001));
    }
  });

  test('same coordinates yield same painting, no tile collisions', () {
    const region=Rect.fromLTWH(-1000,-800,2200,1800);
    final a=mosaic.visible(region,items.length,limit:800);
    final b=mosaic.visible(region,items.length,limit:800);
    String signature(dynamic t) =>
      t.key.toString()+'/'+t.artworkIndex.toString()+'/'+t.rect.toString();
    expect(a.map(signature).toList(),b.map(signature).toList());
    expect(a.map((t)=>t.key).toSet().length,a.length);
    for(var i=0;i<a.length;i++){
      for(var j=i+1;j<a.length;j++){
        expect(a[i].rect.overlaps(a[j].rect),false);
      }
    }
  });

  test('most vivid score class gets biggest rows', () {
    final tiles=mosaic.visible(const Rect.fromLTWH(-1200,-1100,3200,3000),
        items.length,limit:900);
    final hero=tiles.where((t)=>t.rect.height>=385);
    final small=tiles.where((t)=>t.rect.height<=230);
    expect(hero,isNotEmpty);
    expect(small,isNotEmpty);
    final low=hero.map((t)=>pixels[items[t.artworkIndex].catalogKey]!)
        .reduce((a,b)=>a<b?a:b);
    final high=small.map((t)=>pixels[items[t.artworkIndex].catalogKey]!)
        .reduce((a,b)=>a>b?a:b);
    expect(low,greaterThan(high));
  });

  test('bounded distant coordinates and viewport priority', () {
    expect(mosaic.visible(const Rect.fromLTWH(-2000000,1000000,900,1600),
        items.length,limit:100),isNotEmpty);
    expect(mosaic.visible(const Rect.fromLTWH(1500000,-1200000,900,1600),
        items.length,limit:100),isNotEmpty);
    const view=Rect.fromLTWH(0,0,660,1000);
    final all=mosaic.visible(view,items.length,limit:180)
        .map((t)=>t.key).toSet();
    final capped=mosaic.visible(
        const Rect.fromLTWH(-1500,-1200,3500,3700),items.length,
        limit:180,priorityViewport:view);
    expect(capped.length,lessThanOrEqualTo(180));
    expect(all.difference(capped.map((t)=>t.key).toSet()),isEmpty);
  });
}
