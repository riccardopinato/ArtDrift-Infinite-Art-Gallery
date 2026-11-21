import 'package:flutter_test/flutter_test.dart';
import 'package:artdrift/models/artwork.dart';

void main() {
  test('only independently verified public-domain artwork enters gallery', () {
    final base = <String, dynamic>{
      'id': 27992,
      'title': 'A Sunday on La Grande Jatte — 1884',
      'artist_title': 'Georges Seurat',
      'date_display': '1884–86',
      'image_id': '2d484387-2509-5e8e-2c43-22f9981972eb',
      'is_public_domain': true,
      'artwork_type_title': 'Painting',
      'thumbnail': {'width': 1000, 'height': 700},
    };
    final artwork = Artwork.fromJson(base);
    expect(artwork.displayable, isTrue);
    expect(artwork.naturalAspectRatio, greaterThan(1));
    expect(artwork.imageUrl(width: 400), contains('/full/400,/0/default.jpg'));
    expect(artwork.shortDescription, contains('Georges Seurat'));
    expect(Artwork.fromJson({...base, 'is_public_domain': false}).displayable, isFalse);
    expect(Artwork.fromJson({...base, 'image_id': 'javascript:fake'}).displayable, isFalse);
    expect(Artwork.fromJson({...base, 'artwork_type_title': 'Photograph'}).displayable, isFalse);
  });
}
