/// Public-domain artwork metadata from the Art Institute of Chicago API.
/// The institute's narrative description is NOT copied or redistributed.
class Artwork {
  const Artwork({
    required this.id,
    required this.title,
    required this.artist,
    required this.date,
    required this.imageId,
    required this.publicDomain,
    this.medium = '',
    this.origin = '',
    this.creditLine = '',
    this.artworkType = '',
    this.imageWidth,
    this.imageHeight,
    this.bootstrapAsset = '',
  });

  final int id;
  final String title;
  final String artist;
  final String date;
  final String imageId;
  final bool publicDomain;
  final String medium;
  final String origin;
  final String creditLine;
  final String artworkType;
  final int? imageWidth;
  final int? imageHeight;
  /// Source-pinned tiny WebP artwork preview; no full-size bitmap in the APK.
  final String bootstrapAsset;
  bool get hasBundledPreview => RegExp(r'^assets/gallery/thumbs/[0-9]+\.webp
  static final RegExp _imageIdPattern = RegExp(r'^[0-9a-fA-F-]{16,64}$');
  bool get displayable =>
      id > 0 && publicDomain && _imageIdPattern.hasMatch(imageId) &&
      (artworkType.isEmpty || artworkType.toLowerCase() == 'painting');

  double get naturalAspectRatio {
    if (imageWidth == null || imageHeight == null || imageHeight == 0) {
      return 1;
    }
    return (imageWidth! / imageHeight!).clamp(0.35, 3.0).toDouble();
  }

  String imageUrl({int width = 400}) {
    final safeWidth = <int>{112, 200, 400, 600, 800, 843, 1200, 1686}
        .contains(width) ? width : 843;
    return 'https://www.artic.edu/iiif/2/$imageId/full/$safeWidth,/0/default.jpg';
  }

  String get museumUrl => 'https://www.artic.edu/artworks/$id';

  /// Original factual caption built solely from metadata, not museum prose.
  String get shortDescription {
    final creator = artist.isEmpty ? 'un artista non identificato' : artist;
    final when = date.isEmpty ? '' : ', datata $date';
    final how = medium.isEmpty ? '' : ' La tecnica registrata è: $medium.';
    final where = origin.isEmpty ? '' : ' Provenienza: $origin.';
    return '«$title» è un’opera attribuita a $creator$when.$how$where';
  }

  static String _str(Object? value) => value is String ? value.trim() : '';
  static int? _int(Object? value) => value is num ? value.toInt() : null;

  factory Artwork.fromJson(Map<String, dynamic> json) {
    final thumb = json['thumbnail'];
    final image = thumb is Map ? thumb : const {};
    return Artwork(
      id: _int(json['id']) ?? 0,
      title: _str(json['title']).isEmpty ? 'Senza titolo' : _str(json['title']),
      artist: _str(json['artist_title']).isNotEmpty
          ? _str(json['artist_title']) : _str(json['artist_display']),
      date: _str(json['date_display']),
      imageId: _str(json['image_id']),
      publicDomain: json['is_public_domain'] == true,
      medium: _str(json['medium_display']),
      origin: _str(json['place_of_origin']),
      creditLine: _str(json['credit_line']),
      artworkType: _str(json['artwork_type_title']),
      imageWidth: _int(image['width']),
      imageHeight: _int(image['height']),
      bootstrapAsset: _str(json['bootstrap_asset']),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'artist_title': artist,
        'date_display': date,
        'image_id': imageId,
        'is_public_domain': publicDomain,
        'medium_display': medium,
        'place_of_origin': origin,
        'credit_line': creditLine,
        'artwork_type_title': artworkType,
        'thumbnail': {'width': imageWidth, 'height': imageHeight},
        if (hasBundledPreview) 'bootstrap_asset': bootstrapAsset,
      };
}
).hasMatch(bootstrapAsset);

  static final RegExp _imageIdPattern = RegExp(r'^[0-9a-fA-F-]{16,64}$');
  bool get displayable =>
      id > 0 && publicDomain && _imageIdPattern.hasMatch(imageId) &&
      (artworkType.isEmpty || artworkType.toLowerCase() == 'painting');

  double get naturalAspectRatio {
    if (imageWidth == null || imageHeight == null || imageHeight == 0) {
      return 1;
    }
    return (imageWidth! / imageHeight!).clamp(0.35, 3.0).toDouble();
  }

  String imageUrl({int width = 400}) {
    final safeWidth = <int>{112, 200, 400, 600, 800, 843, 1200, 1686}
        .contains(width) ? width : 843;
    return 'https://www.artic.edu/iiif/2/$imageId/full/$safeWidth,/0/default.jpg';
  }

  String get museumUrl => 'https://www.artic.edu/artworks/$id';

  /// Original factual caption built solely from metadata, not museum prose.
  String get shortDescription {
    final creator = artist.isEmpty ? 'un artista non identificato' : artist;
    final when = date.isEmpty ? '' : ', datata $date';
    final how = medium.isEmpty ? '' : ' La tecnica registrata è: $medium.';
    final where = origin.isEmpty ? '' : ' Provenienza: $origin.';
    return '«$title» è un’opera attribuita a $creator$when.$how$where';
  }

  static String _str(Object? value) => value is String ? value.trim() : '';
  static int? _int(Object? value) => value is num ? value.toInt() : null;

  factory Artwork.fromJson(Map<String, dynamic> json) {
    final thumb = json['thumbnail'];
    final image = thumb is Map ? thumb : const {};
    return Artwork(
      id: _int(json['id']) ?? 0,
      title: _str(json['title']).isEmpty ? 'Senza titolo' : _str(json['title']),
      artist: _str(json['artist_title']).isNotEmpty
          ? _str(json['artist_title']) : _str(json['artist_display']),
      date: _str(json['date_display']),
      imageId: _str(json['image_id']),
      publicDomain: json['is_public_domain'] == true,
      medium: _str(json['medium_display']),
      origin: _str(json['place_of_origin']),
      creditLine: _str(json['credit_line']),
      artworkType: _str(json['artwork_type_title']),
      imageWidth: _int(image['width']),
      imageHeight: _int(image['height']),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'artist_title': artist,
        'date_display': date,
        'image_id': imageId,
        'is_public_domain': publicDomain,
        'medium_display': medium,
        'place_of_origin': origin,
        'credit_line': creditLine,
        'artwork_type_title': artworkType,
        'thumbnail': {'width': imageWidth, 'height': imageHeight},
      };
}
