import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/artwork.dart';
import 'gallery_search.dart';

/// Search is user-invoked, ephemeral and strictly filtered to public-domain
/// painting results from official museum APIs. Not a background harvest.
class MuseumSearchService {
  MuseumSearchService({http.Client? client}) : _client = client ?? http.Client();
  final http.Client _client;
  static String _str(Object? value) => value is String ? value.trim() : '';
  static int? _id(Object? value) => value is num ? value.toInt() : null;
  static Map<String, dynamic>? _map(Object? value) =>
      value is Map<String, dynamic> ? value : null;

  static String translatedQuery(String query, ArtworkSearchScope scope) {
    if (scope != ArtworkSearchScope.subject && scope != ArtworkSearchScope.all) {
      return query.trim();
    }
    const terms = <String, String>{
      'parco':'park', 'parchi':'park', 'giardino':'garden', 'giardini':'garden',
      'mare':'sea', 'spiaggia':'beach', 'bosco':'forest', 'albero':'tree',
      'fiori':'flowers', 'fiore':'flower', 'montagna':'mountain',
      'città':'city', 'citta':'city', 'natura':'nature',
      'lago':'lake', 'fiume':'river', 'ritratto':'portrait',
      'notte':'night', 'neve':'snow',
    };
    return terms[query.toLowerCase().trim()] ?? query.trim();
  }

  Future<Map<String, dynamic>> _get(Uri uri) async {
    final response = await _client.get(uri, headers: {
      'Accept': 'application/json',
      'User-Agent': 'ArtDrift/0.3 independent Open Access gallery',
    }).timeout(const Duration(seconds: 12));
    if (response.statusCode != 200 || response.bodyBytes.length > 2500000) {
      throw StateError('Invalid museum response');
    }
    final data = jsonDecode(utf8.decode(response.bodyBytes));
    if (data is! Map<String, dynamic>) throw const FormatException('Museum response');
    return data;
  }

  Future<List<Artwork>> fromMet(String query, ArtworkSearchScope scope) async {
    final args = <String, String>{
      'q': translatedQuery(query, scope), 'hasImages': 'true',
      'offset': '0', 'limit': '32',
    };
    if (scope == ArtworkSearchScope.title) args['title'] = 'true';
    if (scope == ArtworkSearchScope.artist) args['artistOrCulture'] = 'true';
    if (scope == ArtworkSearchScope.subject) args['tags'] = 'true';
    final result = await _get(Uri.https('collectionapi.metmuseum.org',
        '/public/collection/v1.1/search', args));
    final ids = result['objectIDs'];
    if (ids is! List) return const [];
    final found = <Artwork>[];
    for (var i = 0; i < ids.length && i < 24 && found.length < 8; i += 4) {
      final batch = ids.skip(i).take(4).whereType<int>().toList();
      final works = await Future.wait(batch.map((id) async {
        try {
          return parseMet(await _get(Uri.https('collectionapi.metmuseum.org',
              '/public/collection/v1/objects/$id')));
        } catch (_) { return null; }
      }));
      found.addAll(works.whereType<Artwork>());
    }
    return found.take(8).toList(growable: false);
  }

  static Artwork? parseMet(Map<String, dynamic> row) {
    final id = _id(row['objectID']);
    final url = _str(row['primaryImageSmall']);
    final type = (_str(row['classification']) + ' ' + _str(row['objectName']) +
        ' ' + _str(row['department'])).toLowerCase();
    if (id == null || id <= 0 || row['isPublicDomain'] != true ||
        !type.contains('paint') || !Artwork.officialImageUrl(url, 'met')) return null;
    final terms = <String>[];
    if (row['tags'] is List) {
      for (final tag in row['tags'] as List) {
        final term = _str(_map(tag)?['term']);
        if (term.isNotEmpty) terms.add(term);
      }
    }
    final work = Artwork(
      id: 10000000 + id, imageId: '', publicDomain: true,
      title: _str(row['title']).isNotEmpty ? _str(row['title']) : 'Untitled',
      artist: _str(row['artistDisplayName']), date: _str(row['objectDate']),
      artworkType: 'Painting', medium: _str(row['medium']),
      origin: _str(row['culture']), creditLine: _str(row['creditLine']),
      museumSource: 'met', remotePreviewUrl: url,
      remoteMuseumUrl: _str(row['objectURL']),
      subjectTerms: terms.take(32).toList(growable: false),
    );
    return work.displayable ? work : null;
  }

  Future<List<Artwork>> fromCleveland(String query, ArtworkSearchScope scope) async {
    final response = await _get(Uri.https('openaccess-api.clevelandart.org',
        '/api/artworks/', {
          'q': translatedQuery(query, scope), 'cc0': '1',
          'has_image': '1', 'limit': '30', 'skip': '0',
        }));
    final rows = response['data'];
    if (rows is! List) return const [];
    return rows.whereType<Map<String, dynamic>>().map(parseCleveland)
        .whereType<Artwork>().take(10).toList(growable: false);
  }

  static Artwork? parseCleveland(Map<String, dynamic> row) {
    final id = _id(row['id']);
    final license = _str(row['share_license_status']).toUpperCase();
    final type = _str(row['type']).toLowerCase();
    final preview = _str(_map(_map(row['images'])?['web'])?['url']);
    if (id == null || id <= 0 || !license.startsWith('CC0') ||
        !type.contains('paint') ||
        !Artwork.officialImageUrl(preview, 'cleveland')) return null;
    final creators = <String>[];
    if (row['creators'] is List) {
      for (final item in row['creators'] as List) {
        final name = _str(_map(item)?['description']);
        if (name.isNotEmpty) creators.add(name);
      }
    }
    final tags = <String>[];
    if (row['keywords'] is List) {
      for (final item in row['keywords'] as List) {
        final tag = item is String ? item : _str(_map(item)?['name']);
        if (tag.isNotEmpty) tags.add(tag);
      }
    }
    final work = Artwork(
      id: 20000000 + id, imageId: '', publicDomain: true,
      title: _str(row['title']).isNotEmpty ? _str(row['title']) : 'Untitled',
      artist: creators.isNotEmpty ? creators.first : _str(row['culture']),
      date: _str(row['creation_date']), artworkType: 'Painting',
      medium: _str(row['technique']), origin: _str(row['culture']),
      creditLine: _str(row['creditline']),
      museumSource: 'cleveland', remotePreviewUrl: preview,
      remoteMuseumUrl: _str(row['url']),
      subjectTerms: tags.take(32).toList(growable: false),
    );
    return work.displayable ? work : null;
  }

  /// No authentication, storage or network calls unless user taps search.
  Future<List<Artwork>> search(String query, ArtworkSearchScope scope) async {
    final q = query.trim();
    if (q.length < 2 || q.length > 90) return const [];
    final sources = await Future.wait([
      fromMet(q, scope).catchError((Object _) => <Artwork>[]),
      fromCleveland(q, scope).catchError((Object _) => <Artwork>[]),
    ]);
    final bySourceId = <String, Artwork>{};
    for (final list in sources) {
      for (final art in list) {
        if (art.displayable) bySourceId[art.catalogKey] = art;
      }
    }
    return bySourceId.values.toList(growable: false);
  }

  void close() => _client.close();
}
