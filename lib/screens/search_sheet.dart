import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/artwork.dart';
import '../collections/art_collections.dart';
import '../ui/artwork_preview_image.dart';
import '../search/gallery_search.dart';
import '../search/museum_search.dart';
import '../services/museum_cloud_catalog.dart';
import 'museum_cloud_catalog_page.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

Future<Artwork?> showArtSearchSheet(BuildContext context,
    List<Artwork> catalog, {
      void Function(ArtCollection)? onOpenCollection,
      VoidCallback? onOpenDoppleganger,
      List<Artwork>? collectionCatalog,
    }) =>
    showModalBottomSheet<Artwork>(
      context: context, isScrollControlled: true, useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _SearchSheet(
        artworks: catalog,
        collectionCatalog: collectionCatalog ?? catalog,
        onOpenCollection: onOpenCollection,
        onOpenDoppleganger: onOpenDoppleganger,
      ),
    );

class _SearchSheet extends StatefulWidget {
  const _SearchSheet({
    required this.artworks,
    required this.collectionCatalog,
    this.onOpenCollection,
    this.onOpenDoppleganger,
  });
  final List<Artwork> artworks;
  final List<Artwork> collectionCatalog;
  final void Function(ArtCollection)? onOpenCollection;
  final VoidCallback? onOpenDoppleganger;
  @override
  State<_SearchSheet> createState() => _SearchSheetState();
}

class _SearchSheetState extends State<_SearchSheet> {
  final TextEditingController _text = TextEditingController();
  final MuseumSearchService _museums = MuseumSearchService();
  final MuseumCloudCatalog _cloud = MuseumCloudCatalog();
  static const bool _d1OptIn = bool.fromEnvironment('ARTDRIFT_ENABLE_D1_DISCOVERY',defaultValue:false);
  late final GallerySearch _search;
  ArtworkSearchScope _scope = ArtworkSearchScope.all;
  List<Artwork> _local = const [];
  List<Artwork> _international = const [];
  List<String> _suggestions = const [];
  List<ArtCollection> _collections = const [];
  bool _searching = false;
  bool _remoteAttempted = false;
  int _generation = 0;

  static String t(String key) => ArtDriftLocale.text(key);

  @override
  void initState() {
    super.initState();
    _search = GallerySearch(widget.artworks);
    _collections = ArtCollections.available(widget.collectionCatalog);
    _text.addListener(_updateLocal);
  }

  void _updateLocal() {
    final query = _text.text.trim();
    _generation++;
    setState(() {
      _international = const [];
      _remoteAttempted = false;
      _searching = false;
      _suggestions = _search.suggest(query, scope: _scope);
      _local = query.length > 1 ? _search.find(query, scope: _scope) : const [];
    });
  }

  void _changeScope(ArtworkSearchScope scope) {
    _scope = scope;
    _updateLocal();
  }

  Future<void> _searchInternational() async {
    final query = _text.text.trim();
    if (query.length < 2 || _searching) return;
    final generation = ++_generation;
    FocusScope.of(context).unfocus();
    setState(() {
      _searching = true;
      _remoteAttempted = false;
      _international = const [];
    });
    try {
      final results = await _museums.search(query, _scope);
      if (!mounted || generation != _generation) return;
      setState(() {
        _international = results;
        _remoteAttempted = true;
        _searching = false;
      });
    } catch (_) {
      if (!mounted || generation != _generation) return;
      setState(() {
        _remoteAttempted = true;
        _searching = false;
      });
    }
  }

  @override
  void dispose() {
    _generation++;
    _text.removeListener(_updateLocal);
    _text.dispose();
    _museums.close();
    _cloud.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.of(context);
    final availableHeight = mq.size.height - mq.viewInsets.bottom - 30;
    final height = math.max(270.0, math.min(mq.size.height * .84, availableHeight));
    return AnimatedPadding(
      duration: const Duration(milliseconds: 140),
      curve: Curves.easeOut,
      padding: EdgeInsets.only(bottom: mq.viewInsets.bottom),
      child: SizedBox(height: height, child: ParchmentPanel(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const BrushMark(size: 28),
            const SizedBox(width: 11),
            Expanded(child: Text(t('searchTitle'),
              style: const TextStyle(fontFamily: 'serif', fontSize: 26,
                fontWeight: FontWeight.w600, color: ArtPaper.ink))),
            IconButton(onPressed: () => Navigator.pop(context),
              tooltip: t('close'),
              icon: const Icon(Icons.close, color: ArtPaper.ink)),
          ]),
          const Divider(color: ArtPaper.gold, thickness: .75),
          const SizedBox(height: 7),
          OrnateFrame(shadow: false, padding: const EdgeInsets.fromLTRB(10, 1, 8, 1),
            child: Row(children: [
              const BrushMark(size: 20), const SizedBox(width: 9),
              Expanded(child: TextField(
                controller: _text, autofocus: true, maxLength: 90,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _searchInternational(),
                style: const TextStyle(color: ArtPaper.ink, fontSize: 16,
                  fontFamily: 'serif'),
                decoration: InputDecoration(
                  counterText: '', hintText: t('searchHint'),
                  hintStyle: const TextStyle(color: Color(0xFF8E7759)),
                  isDense: true, border: InputBorder.none),
              )),
              if (_text.text.isNotEmpty) IconButton(
                icon: const Icon(Icons.close, color: ArtPaper.gold, size: 18),
                onPressed: _text.clear),
            ]),
          ),
          const SizedBox(height: 12),
          SingleChildScrollView(scrollDirection: Axis.horizontal,
            child: Row(children: [
              _scopeChip(ArtworkSearchScope.all,'filterAll'),
              _scopeChip(ArtworkSearchScope.artist,'filterArtist'),
              _scopeChip(ArtworkSearchScope.title,'filterTitle'),
              _scopeChip(ArtworkSearchScope.subject,'filterSubject'),
            ]),
          ),
          const SizedBox(height: 8),
          Expanded(child: ListView(children: [
            if (_text.text.trim().isEmpty) ...[
              if (widget.onOpenDoppleganger != null)
                _dopplegangerRow(),
              if (_collections.isNotEmpty) ...[
                _section(_collectionHeader()),
                for (final collection in _collections)
                  _collectionRow(collection),
              ] else
                Padding(padding: const EdgeInsets.symmetric(vertical: 24),
                  child: Center(child: Text(t('emptyQuery'),
                    style: const TextStyle(
                      color: ArtPaper.ink, fontFamily: 'serif')))),
            ],
            if (_suggestions.isNotEmpty) ...[
              _section(t('suggestions')),
              for (final name in _suggestions)
                InkWell(
                  onTap: () { _text.value = TextEditingValue(
                    text: name, selection: TextSelection.collapsed(offset: name.length)); },
                  child: Padding(padding: const EdgeInsets.symmetric(
                    horizontal: 9, vertical: 7),
                    child: Row(children: [
                      const Icon(Icons.auto_awesome_outlined,
                        color: ArtPaper.gold, size: 14),
                      const SizedBox(width: 10),
                      Expanded(child: Text(name, maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: ArtPaper.ink,fontSize:13))),
                    ])),
                ),
              const Divider(color: ArtPaper.gold),
            ],
            if (_text.text.trim().length > 1) ...[
              _section(t('results') + ' · ' + _local.length.toString()),
              if (_local.isEmpty) Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: Text(t('noResults'), style: const TextStyle(
                    color: ArtPaper.ink, fontSize: 12))),
              for (final a in _local) _artworkRow(a),
              const SizedBox(height: 12),
              const Divider(color: ArtPaper.gold),
              OutlinedButton.icon(
                onPressed: _searching ? null : _searchInternational,
                style: OutlinedButton.styleFrom(
                  foregroundColor: ArtPaper.ink,
                  side: const BorderSide(color: ArtPaper.gold)),
                icon: const Icon(Icons.museum_outlined),
                label: Text(_searching ? t('museumSearching') : t('museumSearch')),
              ),
              if (_d1OptIn && _cloud.enabled)
                Padding(padding: const EdgeInsets.only(top: 8),
                  child: OutlinedButton.icon(
                    key: const Key('artdrift-open-d1-museum-archive'),
                    onPressed: () => Navigator.of(context).push<void>(
                      MaterialPageRoute<void>(builder: (_) =>
                        MuseumCloudCatalogPageScreen(
                          initialQuery: _text.text.trim()))),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: ArtPaper.ink,
                      side: const BorderSide(color: ArtPaper.gold)),
                    icon: const Icon(Icons.account_balance_outlined),
                    label: Text(t('cloudMuseumArchive')),
                  )),
              Padding(padding: const EdgeInsets.symmetric(vertical: 6),
                child: Text(t('queryDisclosure'),
                  style: const TextStyle(color: Color(0xFF765D42),
                    fontSize: 11, height: 1.35))),
              if (_searching) const Center(child: Padding(
                padding: EdgeInsets.symmetric(vertical: 10),
                child: CircularProgressIndicator(color: ArtPaper.gold))),
              if (_remoteAttempted) ...[
                _section(t('museumResults') + ' · ' + _international.length.toString()),
                if (_international.isEmpty) Text(t('museumUnavailable'),
                  style: const TextStyle(color: ArtPaper.ink,fontSize:12)),
                for (final art in _international) _artworkRow(art),
              ],
              if (_scope == ArtworkSearchScope.subject)
                Padding(padding: const EdgeInsets.symmetric(vertical: 13),
                  child: Text(t('subjectNotice'), style: const TextStyle(
                    color: Color(0xFF765D42), fontSize: 11, height: 1.4))),
            ],
            const SizedBox(height: 12),
          ])),
          Center(child: Text(t('offline'),
            style: const TextStyle(color: Color(0xFF80684B),fontSize:10))),
        ])),
      ),
    );
  }

  Widget _dopplegangerRow() {
    const subtitles = <String, String>{
      'it': 'Un ritratto, un volto celebre. Indovina il sosia.',
      'en': 'One portrait, one familiar face. Guess the match.',
      'fr': 'Un portrait, un visage connu. Devinez la ressemblance.',
      'es': 'Un retrato, un rostro famoso. Adivina el parecido.',
      'de': 'Ein Porträt, ein bekanntes Gesicht. Rate mit.',
      'pt': 'Um retrato, um rosto famoso. Adivinha a semelhança.',
    };
    final subtitle = subtitles[ArtDriftLocale.current.value] ??
        subtitles['en']!;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: OrnateFrame(shadow: false, padding: EdgeInsets.zero,
        child: ListTile(
          key: const Key('artdrift-doppleganger-entry'),
          leading: const Icon(Icons.theater_comedy_outlined,
            color: ArtPaper.gold),
          title: const Text('Doppleganger', style: TextStyle(
            color: ArtPaper.ink, fontFamily: 'serif',
            fontSize: 17, fontWeight: FontWeight.w600)),
          subtitle: Text(subtitle, style: const TextStyle(
            color: Color(0xFF785C3C), fontSize: 11)),
          trailing: const Icon(Icons.open_in_new_rounded,
            color: ArtPaper.gold, size: 18),
          onTap: () {
            Navigator.of(context).pop();
            widget.onOpenDoppleganger?.call();
          },
        ),
      ),
    );
  }

  String _collectionHeader() {
    const titles = {'it':'Esplora le collezioni',
      'en':'Explore collections','fr':'Explorer les collections',
      'es':'Explorar colecciones','de':'Sammlungen entdecken',
      'pt':'Explorar coleções'};
    return titles[ArtDriftLocale.current.value] ?? titles['en']!;
  }

  Widget _collectionRow(ArtCollection collection) {
    final language = ArtDriftLocale.current.value;
    final count = widget.collectionCatalog.where(collection.contains).length;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: OrnateFrame(shadow: false, padding: EdgeInsets.zero,
        child: ListTile(
          key: ValueKey('collection-${collection.id}'),
          leading: const Icon(Icons.collections_bookmark_outlined,
              color: ArtPaper.gold),
          title: Text(collection.title(language),
              style: const TextStyle(color: ArtPaper.ink,
                  fontFamily: 'serif', fontSize: 15)),
          subtitle: Text(collection.subtitle(language),
              style: const TextStyle(color: Color(0xFF785C3C), fontSize: 11)),
          trailing: Text('$count',
              style: const TextStyle(color: ArtPaper.gold, fontSize: 12)),
          onTap: () {
            Navigator.of(context).pop();
            widget.onOpenCollection?.call(collection);
          },
        ),
      ),
    );
  }

  Widget _scopeChip(ArtworkSearchScope scope, String key) => Padding(
    padding: const EdgeInsets.only(right: 7),
    child: ChoiceChip(
      selected: _scope == scope,
      label: Text(t(key)),
      side: const BorderSide(color: ArtPaper.gold),
      backgroundColor: ArtPaper.pale,
      selectedColor: const Color(0xFFC9AB7C),
      labelStyle: const TextStyle(color: ArtPaper.ink, fontSize: 12),
      onSelected: (_) => _changeScope(scope),
    ),
  );

  Widget _section(String name) => Padding(
    padding: const EdgeInsets.fromLTRB(4, 12, 4, 7),
    child: Text(name.toUpperCase(),style: const TextStyle(
      color: Color(0xFF896536), letterSpacing: 1.2,
      fontSize: 10, fontWeight: FontWeight.bold)),
  );

  Widget _artworkRow(Artwork art) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: OrnateFrame(shadow: false, padding: EdgeInsets.zero,
      child: InkWell(
        onTap: () => Navigator.of(context).pop(art),
        child: Padding(padding: const EdgeInsets.all(8),
          child: Row(children: [
            ClipRRect(borderRadius: BorderRadius.circular(3),
              child: SizedBox(width: 49, height: 67,
                child: ArtworkPreviewImage(
                  artwork: art,
                  fit: BoxFit.cover,
                  cacheWidth: 100,
                ),
              )),
            const SizedBox(width: 13),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(art.title, maxLines: 2, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontFamily: 'serif', color: ArtPaper.ink,
                    fontSize: 15, fontWeight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text(art.artist.isEmpty ? '—' : art.artist,
                  maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Color(0xFF78634C),fontSize: 11)),
                const SizedBox(height: 4),
                Text(art.displayedMuseum + ' · ' + art.displayedLicense,
                  maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Color(0xFF896A45),fontSize: 9)),
              ])),
            const Icon(Icons.chevron_right, color: ArtPaper.gold),
          ])),
      )),
  );
}
