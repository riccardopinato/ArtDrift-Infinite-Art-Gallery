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
    this.museumSource = 'aic',
    this.remotePreviewUrl = '',
    this.remoteMuseumUrl = '',
    this.subjectTerms = const [],
    this.museumName = '',
    this.museumNativeId = '',
    this.rightsLicense = '',
    this.rightsEvidenceUrl = '',
    this.dimensions = '',
    this.technique = '',
    this.remoteFullUrl = '',
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
  /// Compact verified painting preview shipped with the app.
  final String bootstrapAsset;
  /// Officially sourced international results must retain source identity.
  final String museumSource;
  final String remotePreviewUrl;
  final String remoteMuseumUrl;
  final List<String> subjectTerms;
  final String museumName;
  final String museumNativeId;
  final String rightsLicense;
  final String rightsEvidenceUrl;
  final String dimensions;
  final String technique;
  final String remoteFullUrl;
  String get displayedMuseum => museumName.isNotEmpty ? museumName :
      museumSource == 'met' ? 'The Metropolitan Museum of Art' :
      museumSource == 'cleveland' ? 'Cleveland Museum of Art' :
      museumSource == 'rijks' ? 'Rijksmuseum' :
      museumSource == 'nga' ? 'National Gallery of Art, Washington' :
      museumSource == 'getty' ? 'J. Paul Getty Museum' :
      museumSource == 'smithsonian' ? 'Smithsonian American Art Museum' :
      museumSource == 'smk' ? 'SMK – National Gallery of Denmark' :
      museumSource == 'mia' ? 'Minneapolis Institute of Art' :
      museumSource == 'walters' ? 'The Walters Art Museum' :
      'Art Institute of Chicago';
  String get displayedLicense => rightsLicense.isNotEmpty ? rightsLicense :
      museumSource == 'aic' ? 'Public Domain' : 'CC0';
  String get catalogKey => '$museumSource:$id';

  static bool officialImageUrl(String url, String museum) {
    final uri = Uri.tryParse(url);
    if (uri == null || uri.scheme != 'https' || uri.userInfo.isNotEmpty ||
        (uri.hasPort && uri.port != 443)) return false;
    const hosts = <String, Set<String>>{
      'met': {'images.metmuseum.org'},
      'cleveland': {'openaccess-cdn.clevelandart.org',
        'clevelandart.org', 'www.clevelandart.org'},
      'rijks': {'iiif.micr.io'},
      'nga': {'api.nga.gov', 'media.nga.gov'},
      'getty': {'media.getty.edu'},
      'smithsonian': {'ids.si.edu', 'www.si.edu', 'si.edu'},
      'smk': {'iip.smk.dk', 'iip-thumb.smk.dk'},
      'mia': {'api.artsmia.org'},
      'walters': {'images.thewalters.org', 'art.thewalters.org'},
    };
    return hosts[museum]?.contains(uri.host.toLowerCase()) ?? false;
  }
  bool get hasBundledPreview => museumSource == 'aic'
      ? bootstrapAsset == 'assets/gallery/thumbs/$id.webp'
      : bootstrapAsset == 'assets/museums/thumbs/' + museumSource + '_$id.webp';

  static final RegExp _imageIdPattern = RegExp(r'^[0-9a-fA-F-]{16,64}$');
  bool get displayable {
    if (id <= 0 || !publicDomain) return false;
    if (museumSource == 'aic') {
      return _imageIdPattern.hasMatch(imageId) &&
          (artworkType.isEmpty || artworkType.toLowerCase() == 'painting');
    }
    if (!const <String>{'met','cleveland','rijks','nga','getty','smithsonian','smk','mia','walters'}
        .contains(museumSource)) return false;
    return artworkType.toLowerCase() == 'painting' &&
        officialImageUrl(remotePreviewUrl, museumSource) &&
        (remoteFullUrl.isEmpty ||
         officialImageUrl(remoteFullUrl, museumSource));
  }

  double get naturalAspectRatio {
    if (imageWidth == null || imageHeight == null || imageHeight == 0) {
      return 1;
    }
    return (imageWidth! / imageHeight!).clamp(0.35, 3.0).toDouble();
  }

  String imageUrl({int width = 400}) {
    if (museumSource != 'aic') {
      if (width >= 600 && remoteFullUrl.isNotEmpty &&
         (museumSource == 'rijks' || museumSource == 'nga' ||
          museumSource == 'getty' || museumSource == 'smk' ||
          museumSource == 'smithsonian')) return remoteFullUrl;
      return remotePreviewUrl;
    }
    if (!hasBundledPreview && width <= 400 && remotePreviewUrl.isNotEmpty) {
      return remotePreviewUrl;
    }
    final safeWidth = <int>{112, 200, 400, 600, 800, 843, 1200, 1686}
        .contains(width) ? width : 843;
    return 'https://www.artic.edu/iiif/2/$imageId/full/$safeWidth,/0/default.jpg';
  }

  String get museumUrl {
    if (museumSource == 'aic') return 'https://www.artic.edu/artworks/$id';
    final uri = Uri.tryParse(remoteMuseumUrl);
    const hosts = <String, Set<String>>{
      'met': {'www.metmuseum.org','metmuseum.org'},
      'cleveland': {'www.clevelandart.org','clevelandart.org'},
      'rijks': {'www.rijksmuseum.nl','rijksmuseum.nl','data.rijksmuseum.nl'},
      'nga': {'www.nga.gov','nga.gov'},
      'getty': {'www.getty.edu','getty.edu','data.getty.edu'},
      'smithsonian': {'americanart.si.edu','www.si.edu','si.edu',
        'npg.si.edu','asia.si.edu'},
      'smk': {'open.smk.dk', 'www.open.smk.dk', 'www.smk.dk', 'smk.dk'},
      'mia': {'collections.artsmia.org'},
      'walters': {'art.thewalters.org', 'www.thewalters.org'},
    };
    if (uri != null && uri.scheme == 'https' && uri.userInfo.isEmpty &&
        (hosts[museumSource]?.contains(uri.host) ?? false)) {
      return remoteMuseumUrl;
    }
    const home = <String,String>{
      'met':'https://www.metmuseum.org/',
      'cleveland':'https://www.clevelandart.org/',
      'rijks':'https://www.rijksmuseum.nl/en',
      'nga':'https://www.nga.gov/',
      'getty':'https://www.getty.edu/art/collection/',
      'smithsonian':'https://www.si.edu/',
      'smk':'https://open.smk.dk/',
      'mia':'https://collections.artsmia.org/',
      'walters':'https://art.thewalters.org/',
    };
    return home[museumSource] ?? 'https://www.artic.edu/';
  }

  /// Original factual caption built solely from metadata, not museum prose.
  /// Concise original prose assembled only from museum factual fields.
  String get shortDescription {
    final creator = artist.isEmpty ? 'un artista non identificato' : artist;
    final when = date.isEmpty ? '' : ', datata $date';
    final method = technique.isNotEmpty ? technique : medium;
    final how = method.isEmpty ? '' : ' Tecnica e materiali: $method.';
    final scale = dimensions.isEmpty ? '' : ' Dimensioni: $dimensions.';
    final where = origin.isEmpty ? '' : ' Origine: $origin.';
    final museum = museumSource == 'aic' ? '' :
        ' Conservata presso $displayedMuseum.';
    return '«$title» è un’opera attribuita a $creator$when.$how$scale$where$museum';
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
      museumSource: _str(json['museum_source']).isEmpty ? 'aic' : _str(json['museum_source']),
      remotePreviewUrl: _str(json['remote_preview_url']),
      remoteFullUrl: _str(json['remote_full_url']),
      museumName: _str(json['museum_name']),
      museumNativeId: _str(json['museum_native_id']),
      rightsLicense: _str(json['rights_license']),
      rightsEvidenceUrl: _str(json['rights_evidence_url']),
      dimensions: _str(json['dimensions_display']),
      technique: _str(json['technique_display']),
      remoteMuseumUrl: _str(json['remote_museum_url']),
      subjectTerms: (json['subject_terms'] is List)
          ? (json['subject_terms'] as List).whereType<String>().take(32).toList(growable: false)
          : const [],
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
        if (museumSource != 'aic') 'museum_source': museumSource,
        if (remotePreviewUrl.isNotEmpty) 'remote_preview_url': remotePreviewUrl,
        if (remoteMuseumUrl.isNotEmpty) 'remote_museum_url': remoteMuseumUrl,
        if (subjectTerms.isNotEmpty) 'subject_terms': subjectTerms,
        if (remoteFullUrl.isNotEmpty) 'remote_full_url': remoteFullUrl,
        if (museumName.isNotEmpty) 'museum_name': museumName,
        if (museumNativeId.isNotEmpty) 'museum_native_id': museumNativeId,
        if (rightsLicense.isNotEmpty) 'rights_license': rightsLicense,
        if (rightsEvidenceUrl.isNotEmpty) 'rights_evidence_url': rightsEvidenceUrl,
        if (dimensions.isNotEmpty) 'dimensions_display': dimensions,
        if (technique.isNotEmpty) 'technique_display': technique,
      };
}
