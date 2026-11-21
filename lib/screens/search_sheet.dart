import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../models/artwork.dart';
import '../search/gallery_search.dart';
import '../search/museum_search.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

Future<Artwork?> showArtSearchSheet(BuildContext context, List<Artwork> catalog) =>
    showModalBottomSheet<Artwork>(
      context: context, isScrollControlled: true, useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _SearchSheet(artworks: catalog),
    );

class _SearchSheet extends StatefulWidget {
  const _SearchSheet({required this.artworks});
  final List<Artwork> artworks;
  @override
  State<_SearchSheet> createState() => _SearchSheetState();
}

class _SearchSheetState extends State<_SearchSheet> {
  final TextEditingController _text = TextEditingController();
  final MuseumSearchService _museums = MuseumSearchService();
  late final GallerySearch _search;
  ArtworkSearchScope _scope = ArtworkSearchScope.all;
  List<Artwork> _local = const [];
  List<Artwork> _international = const [];
  List<String> _suggestions = const [];
  bool _searching = false;
  bool _remoteAttempted = false;
  int _generation = 0;

  static String t(String key) => ArtDriftLocale.text(key);

  @override
  void initState() {
    super.initState();
    _search = GallerySearch(widget.artworks);
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
            if (_text.text.trim().isEmpty)
              Padding(padding: const EdgeInsets.symmetric(vertical: 24),
                child: Center(child: Text(t('emptyQuery'),
                  style: const TextStyle(color: ArtPaper.ink, fontFamily:'serif')))),
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
      )),
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
                child: art.hasBundledPreview
                  ? Image.asset(art.bootstrapAsset, fit: BoxFit.cover,
                      cacheWidth: 100)
                  : Image.network(art.imageUrl(width: 200),
                      fit: BoxFit.cover, cacheWidth: 100,
                      errorBuilder: (_, __, ___) =>
                        const ColoredBox(color: ArtPaper.faded,
                          child: Icon(Icons.image_outlined,
                            color: ArtPaper.gold))),
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
                Text(art.museumSource == 'met' ? 'The Met · CC0' :
                  art.museumSource == 'cleveland' ? 'Cleveland · CC0' :
                  'Art Institute of Chicago · Public Domain',
                  maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Color(0xFF896A45),fontSize: 9)),
              ])),
            const Icon(Icons.chevron_right, color: ArtPaper.gold),
          ])),
      )),
  );
}
