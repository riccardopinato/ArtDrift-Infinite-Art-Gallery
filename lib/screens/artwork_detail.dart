import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/artwork.dart';
import '../services/wallpaper.dart';

/// Full-screen viewer inspired by the reference interaction, with our own UI,
/// factual caption and independent open-access catalogue.
class ArtworkDetail extends StatefulWidget {
  const ArtworkDetail({super.key, required this.artworks,
    required this.initialIndex, required this.isFavorite,
    required this.onToggleFavorite});
  final List<Artwork> artworks;
  final int initialIndex;
  final bool Function(int) isFavorite;
  final Future<void> Function(int) onToggleFavorite;

  @override
  State<ArtworkDetail> createState() => _ArtworkDetailState();
}

class _ArtworkDetailState extends State<ArtworkDetail> {
  late int _index;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex;
  }

  Artwork get art => widget.artworks[_index];
  void _next(int direction) => setState(() =>
      _index = (_index + direction + widget.artworks.length) % widget.artworks.length);

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
    await widget.onToggleFavorite(art.id);
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
          onMuseum: _openMuseum,
          onWallpaper: _busy ? null : _setWallpaper,
        );
        final painting = InteractiveViewer(
          key: ValueKey('detail-${current.id}'),
          minScale: 0.9, maxScale: 5,
          child: Center(child: Image.network(
            current.imageUrl(width: 843),
            fit: BoxFit.contain,
            errorBuilder: (_, error, stack) => current.hasBundledPreview
                ? Image.asset(current.bootstrapAsset, fit: BoxFit.contain)
                : const Center(child: Text('Immagine non raggiungibile',
                    style: TextStyle(color: Colors.white70))),
            loadingBuilder: (context, child, progress) => progress == null
                ? child
                : current.hasBundledPreview
                    ? Image.asset(current.bootstrapAsset, fit: BoxFit.contain)
                    : const Center(child: CircularProgressIndicator(
                        color: Colors.white54)),
          )),
        );
        return Stack(children: [
          Padding(
            padding: const EdgeInsets.only(top: 56),
            child: wide
                ? Row(children: [
                    SizedBox(width: 290, child: caption),
                    Expanded(child: Padding(
                      padding: const EdgeInsets.all(14), child: painting)),
                  ])
                : Column(children: [
                    Expanded(child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      child: painting)),
                    SizedBox(height: constraints.maxHeight * 0.31, child: caption),
                  ]),
          ),
          Positioned(left: 8, top: 3, child: IconButton(
            tooltip: 'Torna alla galleria',
            color: Colors.white,
            icon: const Icon(Icons.close_rounded),
            onPressed: () => Navigator.of(context).pop())),
          Positioned(right: 8, top: 3, child: Row(children: [
            IconButton(tooltip: 'Precedente', icon: const Icon(Icons.arrow_back),
              color: Colors.white70, onPressed: () => _next(-1)),
            IconButton(tooltip: 'Successivo', icon: const Icon(Icons.arrow_forward),
              color: Colors.white70, onPressed: () => _next(1)),
            IconButton(
              tooltip: widget.isFavorite(current.id)
                  ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti',
              icon: Icon(widget.isFavorite(current.id)
                  ? Icons.favorite : Icons.favorite_border),
              color: widget.isFavorite(current.id)
                  ? const Color(0xFFF5B1A8) : Colors.white70,
              onPressed: _favorite),
          ])),
          if (_busy) const Positioned.fill(child: ColoredBox(
            color: Color(0x70000000),
            child: Center(child: CircularProgressIndicator()))),
        ]);
      })),
    );
  }
}

class _Caption extends StatelessWidget {
  const _Caption({required this.artwork, required this.onMuseum,
    required this.onWallpaper});
  final Artwork artwork;
  final VoidCallback onMuseum;
  final VoidCallback? onWallpaper;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(19, 12, 19, 16),
      child: SingleChildScrollView(child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('ARTDRIFT · L’OPERA',
            style: TextStyle(color: Colors.white54,
              fontSize: 10, letterSpacing: 2)),
          const SizedBox(height: 15),
          Text(artwork.title, style: const TextStyle(
            color: Colors.white, fontFamily: 'serif',
            fontSize: 22, fontWeight: FontWeight.w500)),
          const SizedBox(height: 5),
          Text('${artwork.artist.isEmpty ? 'Autore sconosciuto' : artwork.artist}'
               '${artwork.date.isEmpty ? '' : ' · ${artwork.date}'}',
            style: const TextStyle(color: Color(0xFFCBC9CC), fontSize: 12)),
          const SizedBox(height: 18),
          Text(artwork.shortDescription, style: const TextStyle(
            color: Color(0xFFDFDCE1), fontSize: 13, height: 1.48)),
          if (artwork.creditLine.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(artwork.creditLine, style: const TextStyle(
              color: Colors.white54, fontSize: 11, height: 1.4)),
          ],
          const SizedBox(height: 18),
          TextButton.icon(onPressed: onWallpaper,
            icon: const Icon(Icons.wallpaper_outlined, size: 17),
            label: const Text('Imposta come sfondo'),
            style: TextButton.styleFrom(foregroundColor: Colors.white)),
          TextButton.icon(onPressed: onMuseum,
            icon: const Icon(Icons.open_in_new, size: 17),
            label: const Text('Scheda originale del museo'),
            style: TextButton.styleFrom(foregroundColor: Colors.white70)),
          const SizedBox(height: 10),
          const Text('Fonte: Art Institute of Chicago · Public Domain',
            style: TextStyle(color: Colors.white38, fontSize: 10)),
        ],
      )),
    );
  }
}
