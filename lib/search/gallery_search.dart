import '../models/artwork.dart';
import 'reference/hybrid_search.dart';

enum ArtworkSearchScope { all, artist, title, subject }

/// Thin, source-pinned adapter for App Factory's certified ephemeral retrieval.
/// A feature hash is NOT image recognition and does not hallucinate subject tags.
class GallerySearch {
  GallerySearch(this.artworks);
  final List<Artwork> artworks;

  // Search documents are immutable for this catalog snapshot; reusing them
  // avoids 4,500 allocations on every keystroke / scope switch.
  final _documentsByScope = <ArtworkSearchScope, List<SearchReferenceDocument>>{};
  final _artById = <String, Artwork>{};

  int get cachedScopeCount => _documentsByScope.length;

  List<SearchReferenceDocument> _documents(ArtworkSearchScope scope) =>
      _documentsByScope.putIfAbsent(scope, () {
        final docs = <SearchReferenceDocument>[];
        for (final art in artworks) {
          if (!art.displayable) continue;
          _artById[art.catalogKey] = art;
          docs.add(SearchReferenceDocument(
            id: art.catalogKey,
            text: _textFor(art, scope),
            tags: art.subjectTerms,
          ));
        }
        return List.unmodifiable(docs);
      });

  static String _normal(String text) => text.toLowerCase().replaceAll(
    RegExp(r'[àáâäãå]'), 'a').replaceAll(RegExp(r'[èéêë]'), 'e')
    .replaceAll(RegExp(r'[ìíîï]'), 'i').replaceAll(RegExp(r'[òóôöõ]'), 'o')
    .replaceAll(RegExp(r'[ùúûü]'), 'u').replaceAll('ç', 'c')
    .replaceAll('ñ', 'n').trim();

  static const Map<String, String> _concepts = {
    'parco':'park garden landscape parc jardin giardino',
    'parchi':'parks gardens landscapes parc jardins giardini',
    'park':'parco garden giardino landscape',
    'giardino':'garden gardens park jardin giardini',
    'giardini':'gardens garden parks jardin',
    'mare':'sea ocean seascape coast beach mer',
    'spiaggia':'beach coast sea playa plage',
    'fiore':'flower flowers blossom fleur flor',
    'fiori':'flowers flower floral fleurs flores',
    'bosco':'forest woods trees foresta forêt',
    'albero':'tree trees arbre árbol',
    'montagna':'mountain mountains montagne',
    'citta':'city town urban ville ciudad',
    'notte':'night nocturne nighttime nuit noche',
    'neve':'snow snowy winter neige nieve',
    'ritratto':'portrait portraits portraiture retrato',
    'natura':'nature natural landscape paysage',
    'lago':'lake lakes lac lago',
    'fiume':'river rivers rivière rio',
  };

  static String expandSubject(String query) {
    final words = _normal(query).split(RegExp(r'\s+'));
    final extra = <String>[];
    for (final word in words) {
      final alias = _concepts[word];
      if (alias != null) extra.add(alias);
    }
    return [query, ...extra].join(' ');
  }

  String _textFor(Artwork a, ArtworkSearchScope scope) {
    switch (scope) {
      case ArtworkSearchScope.artist: return a.artist;
      case ArtworkSearchScope.title: return a.title;
      case ArtworkSearchScope.subject:
        return [a.title, a.subjectTerms.join(' '), a.origin, a.artworkType].join(' ');
      case ArtworkSearchScope.all:
        return [a.artist, a.title, a.date, a.medium,
            a.subjectTerms.join(' '), a.origin].join(' ');
    }
  }

  List<Artwork> find(String query, {ArtworkSearchScope scope = ArtworkSearchScope.all,
      int limit = 35}) {
    final q = query.trim();
    if (q.isEmpty) return const [];
    final docs = _documents(scope);
    final expanded = scope == ArtworkSearchScope.subject ||
        scope == ArtworkSearchScope.all ? expandSubject(q) : q;
    final result = HybridReferenceSearch.search(
      query: expanded.length <= 1000 ? expanded : q,
      documents: docs,
      // Exact source-metadata retrieval is faster than recomputing feature
      // hashes for every painting on each keystroke. No invented image tags.
      semanticAvailable: false, limit: limit.clamp(1, 100).toInt());
    return result.hits.where((h) => h.reasons.contains('lexical'))
        .map((h) => _artById[h.document.id]).whereType<Artwork>()
        .toList(growable: false);
  }

  List<String> suggest(String query, {ArtworkSearchScope scope = ArtworkSearchScope.all}) {
    final q = _normal(query);
    if (q.isEmpty) return const [];
    final results = <String>{};
    for (final art in artworks) {
      if ((scope == ArtworkSearchScope.all || scope == ArtworkSearchScope.artist) &&
          _normal(art.artist).split(' ').any((part) => part.startsWith(q))) {
        results.add(art.artist);
      }
      if ((scope == ArtworkSearchScope.all || scope == ArtworkSearchScope.title ||
              scope == ArtworkSearchScope.subject) &&
          _normal(art.title).split(' ').any((part) => part.startsWith(q))) {
        results.add(art.title);
      }
      if (results.length >= 30) break;
    }
    final sorted = results.where((s) => s.trim().isNotEmpty).toList()
      ..sort((a,b) => _normal(a).compareTo(_normal(b)));
    return sorted.take(7).toList(growable: false);
  }
}
