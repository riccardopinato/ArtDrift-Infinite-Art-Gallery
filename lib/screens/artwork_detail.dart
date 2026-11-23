import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/artwork.dart';
import '../ui/art_remote_image.dart';
import '../ui/artwork_preview_image.dart';
import '../services/wallpaper.dart';
import '../ui/museum_wood_frame.dart';

/// Full-screen viewer inspired by the reference interaction, with our own UI,
/// factual caption and independent open-access catalogue.
class ArtworkDetail extends StatefulWidget {
  const ArtworkDetail({super.key, required this.artworks,
    required this.initialIndex, required this.isFavorite,
    required this.onToggleFavorite});
  final List<Artwork> artworks;
  final int initialIndex;
  final bool Function(Artwork) isFavorite;
  final Future<void> Function(Artwork) onToggleFavorite;

  @override
  State<ArtworkDetail> createState() => _ArtworkDetailState();
}

class _ArtworkDetailState extends State<ArtworkDetail> {
  late int _index;
  bool _busy = false;
  bool _contemplation = false;
  bool _captionExpanded = false;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex;
  }

  Artwork get art => widget.artworks[_index];
  void _next(int direction) => setState(() {
    _index = (_index + direction + widget.artworks.length) % widget.artworks.length;
    _captionExpanded = false;
  });

  Future<void> _setWallpaper() async {
    final selection = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: const Color(0xFF20212A),
      builder: (context) => SafeArea(child: Column(mainAxisSize: MainAxisSize.min,
        children: [
          const ListTile(title: Text('Imposta come sfondo',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
            subtitle: Text('L’immagine verrà adattata al telefono.',
              style: TextStyle(color: Colors.white70))),
          for (final target in const [('home', 'Schermata Home'),
              ('lock', 'Schermata di blocco'), ('both', 'Entrambe')])
            ListTile(title: Text(target.$2, style: const TextStyle(color: Colors.white)),
              onTap: () => Navigator.of(context).pop(target.$1)),
        ],
      )),
    );
    if (selection == null || !mounted) return;
    setState(() => _busy = true);
    try {
      final bytes = await AndroidWallpaper.compose(art);
      await AndroidWallpaper.apply(bytes, selection);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sfondo impostato da Android')));
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Impossibile impostare lo sfondo: $error')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _favorite() async {
    await widget.onToggleFavorite(art);
    if (mounted) setState(() {});
  }

  Future<void> _openMuseum() async {
    final uri = Uri.parse(art.museumUrl);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication) && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Impossibile aprire il museo')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final current = art;
    return Scaffold(
      backgroundColor: const Color(0xFF0E1019),
      body: SafeArea(child: LayoutBuilder(builder: (context, constraints) {
        final wide = constraints.maxWidth >= 740;
        final caption = _Caption(
          artwork: current,
          expanded: _captionExpanded,
          onExpand: () => setState(
            () => _captionExpanded = !_captionExpanded),
          onMuseum: _openMuseum,
          onWallpaper: _busy || kIsWeb ? null : _setWallpaper,
        );
        final painting = GestureDetector(
          behavior: HitTestBehavior.translucent,
          onTap: () => setState(() => _contemplation = !_contemplation),
          child: InteractiveViewer(
            key: ValueKey('detail-${current.catalogKey}'),
            minScale: .9, maxScale: 5,
            child: Center(child: ArtRemoteImage(
              artwork: current, width: 843, fit: BoxFit.contain,
              fallback: ArtworkPreviewImage(
                artwork: current, fit: BoxFit.contain, cacheWidth: 240),
              loading: ArtworkPreviewImage(
                artwork: current, fit: BoxFit.contain, cacheWidth: 240),
            )),
          ),
        );
        final imageWithFrame = MuseumWoodFrame(
          child: AnimatedSwitcher(
            key: const Key('artdrift-detail-switcher'),
            duration: MediaQuery.disableAnimationsOf(context)
                ? Duration.zero : const Duration(milliseconds: 180),
            switchInCurve: Curves.easeIn,
            switchOutCurve: Curves.easeOut,
            transitionBuilder: (child, animation) =>
                FadeTransition(opacity: animation, child: child),
            child: SizedBox.expand(
              key: ValueKey(current.catalogKey),
              child: painting,
            ),
          ),
        );
        final tour = Row(children: [
          SizedBox(width: 43, child: IconButton(
            key: const Key('artdrift-detail-prev'),
            tooltip: 'Precedente',
            icon: const Icon(Icons.chevron_left_rounded),
            iconSize: 34,
            color: const Color(0xFFE8D6B9),
            onPressed: widget.artworks.length > 1 ? () => _next(-1) : null)),
          Expanded(child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: imageWithFrame)),
          SizedBox(width: 43, child: IconButton(
            key: const Key('artdrift-detail-next'),
            tooltip: 'Successivo',
            icon: const Icon(Icons.chevron_right_rounded),
            iconSize: 34,
            color: const Color(0xFFE8D6B9),
            onPressed: widget.artworks.length > 1 ? () => _next(1) : null)),
        ]);
        final tourCounter = Padding(
          padding: const EdgeInsets.fromLTRB(46, 2, 46, 7),
          child: Row(children: [
            const Expanded(child: Text('ARTDRIFT · LA COLLEZIONE',
              style: TextStyle(color: Color(0xFFC0A681),
                fontSize: 9, letterSpacing: 1.2))),
            Text('${_index + 1} / ${widget.artworks.length}',
              key: const Key('artdrift-detail-counter'),
              style: const TextStyle(color: Color(0xFFE5C595),
                fontSize: 11)),
          ]),
        );
        return Stack(children: [
          Column(children: [
            if (!_contemplation) const SizedBox(height: 52),
            Expanded(child: _contemplation
              ? Center(child: painting)
              : wide
                ? Row(children: [
                    Expanded(child: tour),
                    SizedBox(width: 295, child: caption),
                  ])
                : Column(children: [
                    Expanded(child: tour),
                    tourCounter,
                    SizedBox(
                      height: (constraints.maxHeight * .35).clamp(175.0, 310.0),
                      child: caption,
                    ),
                  ])),
            if (wide && !_contemplation) tourCounter,
          ]),
          if (!_contemplation) Positioned(left: 8, top: 3,
            child: IconButton(
              key: const Key('artdrift-detail-close'),
              tooltip: 'Torna alla galleria',
              color: const Color(0xFFF1E1C9),
              icon: const Icon(Icons.close_rounded),
              onPressed: () => Navigator.of(context).pop())),
          if (!_contemplation) Positioned(right: 9, top: 3,
            child: IconButton(
              key: const Key('artdrift-detail-favorite'),
              tooltip: widget.isFavorite(current)
                  ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti',
              icon: Icon(widget.isFavorite(current)
                  ? Icons.favorite : Icons.favorite_border),
              color: widget.isFavorite(current)
                  ? const Color(0xFFCB986F) : const Color(0xFFE8D4B5),
              onPressed: _favorite)),
          if (_busy) const Positioned.fill(child: ColoredBox(
            color: Color(0x70000000),
            child: Center(child: CircularProgressIndicator()))),
        ]);
      })),
    );
  }
}

class _Caption extends StatelessWidget {
  const _Caption({required this.artwork, required this.expanded,
    required this.onExpand, required this.onMuseum, required this.onWallpaper});
  final Artwork artwork;
  final bool expanded;
  final VoidCallback onExpand, onMuseum;
  final VoidCallback? onWallpaper;

  @override
  Widget build(BuildContext context) {
    // All fields come from the current artwork. The prose is constructed from
    // factual catalog metadata, not copied museum narratives or invented history.
    final creator = artwork.artist.isEmpty ? 'Autore sconosciuto'
        : artwork.artist;
    final hasMore = artwork.medium.isNotEmpty || artwork.technique.isNotEmpty ||
        artwork.creditLine.isNotEmpty || artwork.origin.isNotEmpty ||
        artwork.dimensions.isNotEmpty || artwork.date.isNotEmpty;
    return Container(
      key: const Key('artdrift-room-label'),
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [
          Color(0xFFF6ECD9), Color(0xFFEBDEC8)]),
        border: Border.all(color: const Color(0xFFC2A77D)),
      ),
      child: SingleChildScrollView(
        key: const Key('artdrift-room-label-scroll'),
        padding: const EdgeInsets.fromLTRB(17, 13, 17, 13),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Expanded(child: Text('ARTDRIFT · L’OPERA',
                style: TextStyle(color: Color(0xFF987147),
                  fontSize: 10, letterSpacing: 1.5))),
              const Text('✦', style: TextStyle(
                color: Color(0xFFAD8B5A), fontSize: 16)),
            ]),
            const Divider(color: Color(0xFFC5AC88)),
            Text(artwork.title, key: const Key('artdrift-room-title'),
              style: const TextStyle(color: Color(0xFF362B21),
                fontFamily: 'serif', fontSize: 21)),
            const SizedBox(height: 5),
            Text(creator +
              (artwork.date.isEmpty ? '' : ' · ${artwork.date}'),
              style: const TextStyle(color: Color(0xFF765E44),
                fontSize: 12, height: 1.4)),
            const SizedBox(height: 10),
            if (hasMore) ...[
              TextButton(
                key: const Key('artdrift-room-expand'),
                onPressed: onExpand,
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  foregroundColor: const Color(0xFF7A5834)),
                child: Row(children: [
                  Expanded(child: Text(expanded
                    ? 'Riduci la scheda' : 'Leggi la scheda',
                    style: const TextStyle(fontFamily: 'serif'))),
                  Icon(expanded
                    ? Icons.keyboard_arrow_up_rounded
                    : Icons.keyboard_arrow_down_rounded),
                ]),
              ),
              if (expanded) ...[
                Text(artwork.shortDescription,
                  style: const TextStyle(color: Color(0xFF59442F),
                    fontSize: 12, height: 1.55)),
                if (artwork.creditLine.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(artwork.creditLine, style: const TextStyle(
                    color: Color(0xFF6A533C), fontSize: 11)),
                ],
              ],
            ],
            const SizedBox(height: 8),
            Wrap(spacing: 7, runSpacing: 0, children: [
              if (!kIsWeb)
                TextButton.icon(
                  onPressed: onWallpaper,
                  style: TextButton.styleFrom(
                    foregroundColor: const Color(0xFF59432F)),
                  icon: const Icon(Icons.wallpaper_outlined, size: 16),
                  label: const Text('Imposta come sfondo',
                    style: TextStyle(fontSize: 11))),
              TextButton.icon(
                onPressed: onMuseum,
                style: TextButton.styleFrom(
                  foregroundColor: const Color(0xFF59432F)),
                icon: const Icon(Icons.open_in_new, size: 16),
                label: const Text('Scheda originale del museo',
                  style: TextStyle(fontSize: 11))),
            ]),
            const SizedBox(height: 7),
            Text(artwork.displayedMuseum + ' · ' + artwork.displayedLicense,
              style: const TextStyle(color: Color(0xFF867258),
                fontSize: 10)),
          ],
        ),
      ),
    );
  }
}
