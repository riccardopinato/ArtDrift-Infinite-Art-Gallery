import 'dart:math' as math;
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
    required this.onToggleFavorite, this.onArtworkChanged});
  final List<Artwork> artworks;
  final int initialIndex;
  final bool Function(Artwork) isFavorite;
  final Future<void> Function(Artwork) onToggleFavorite;
  final ValueChanged<Artwork>? onArtworkChanged;

  @override
  State<ArtworkDetail> createState() => _ArtworkDetailState();
}

class _ArtworkDetailState extends State<ArtworkDetail> {
  late int _index;
  bool _busy = false;
  bool _contemplation = false;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex;
  }

  // Keep the frame geometry stable when changing paintings; the content
  // itself is always contained and never cropped.
  double get _museumFrameAspect {
    final initial = widget.artworks[widget.initialIndex];
    final w = initial.imageWidth;
    final h = initial.imageHeight;
    if (w == null || h == null || w <= 0 || h <= 0) return 1.0;
    return (w / h).clamp(0.45, 1.8).toDouble();
  }

  Artwork get art => widget.artworks[_index];
  void _next(int direction) {
    setState(() {
      _index = (_index + direction + widget.artworks.length) %
          widget.artworks.length;
    });
    widget.onArtworkChanged?.call(art);
  }

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

  Future<void> _openRights(String source) async {
    final uri = Uri.tryParse(source);
    if (uri == null || uri.scheme != 'https' || uri.userInfo.isNotEmpty ||
        (uri.hasPort && uri.port != 443)) return;
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication) &&
        mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Impossibile aprire il riferimento ai diritti')));
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
          onMuseum: _openMuseum,
          onRights: current.rightsEvidenceUrl.isEmpty
              ? null : () => _openRights(current.rightsEvidenceUrl),
          onLicense: current.imageLicenseRequiresAttribution &&
              current.validImageLicenseLink
              ? () => _openRights(current.imageLicenseUrl)
              : null,
          onWallpaper: _busy || kIsWeb || !current.wallpaperAllowed
              ? null : _setWallpaper,
        );
        final painting = GestureDetector(
          behavior: HitTestBehavior.translucent,
          onTap: () => setState(() => _contemplation = !_contemplation),
          child: InteractiveViewer(
          key: ValueKey('detail-${current.id}'),
          minScale: 0.9, maxScale: 5,
          child: Center(child: ArtRemoteImage(
            artwork: current,
            width: 843,
            fit: BoxFit.contain,
            fallback: ArtworkPreviewImage(
              artwork: current,
              fit: BoxFit.contain,
              cacheWidth: 240,
            ),
            // Same-art packaged WebP appears immediately during HD loading.
            loading: ArtworkPreviewImage(
              artwork: current,
              fit: BoxFit.contain,
              cacheWidth: 240,
            ),
          )),
        ));

        // The decorative walnut surrounds the artwork, not the entire
        // screen. Caption and rights remain the established original UI.
        final museumPainting = LayoutBuilder(builder: (context, bounds) {
          final maxW = math.max(1.0, bounds.maxWidth - 18);
          final maxH = math.max(1.0, bounds.maxHeight - 18);
          final ratio = _museumFrameAspect;
          final width = math.min(maxW, maxH * ratio);
          return Center(child: SizedBox(
            width: width,
            height: width / ratio,
            child: MuseumWoodFrame(child: AnimatedSwitcher(
              key: const Key('artdrift-detail-museum-switcher'),
              duration: MediaQuery.disableAnimationsOf(context)
                ? Duration.zero : const Duration(milliseconds: 180),
              transitionBuilder: (child, animation) =>
                FadeTransition(opacity: animation, child: child),
              child: SizedBox.expand(
                key: ValueKey(current.catalogKey),
                child: painting,
              ),
            )),
          ));
        });
        return Stack(children: [
          Padding(
            padding: EdgeInsets.only(top: _contemplation ? 0 : 56),
            child: _contemplation ? Center(child: painting) : wide
                ? Row(children: [
                    SizedBox(width: 290, child: caption),
                    Expanded(child: Padding(
                      padding: const EdgeInsets.all(14), child: museumPainting)),
                  ])
                : Column(children: [
                    Expanded(child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      child: museumPainting)),
                    SizedBox(height: constraints.maxHeight * 0.31, child: caption),
                  ]),
          ),
          if (!_contemplation) Positioned(left: 8, top: 3, child: IconButton(
            tooltip: 'Torna alla galleria',
            color: Colors.white,
            icon: const Icon(Icons.close_rounded),
            onPressed: () => Navigator.of(context).pop())),
          if (!_contemplation) Positioned(right: 8, top: 3, child: Row(children: [
            IconButton(tooltip: 'Precedente', icon: const Icon(Icons.arrow_back),
              color: Colors.white70, onPressed: () => _next(-1)),
            IconButton(tooltip: 'Successivo', icon: const Icon(Icons.arrow_forward),
              color: Colors.white70, onPressed: () => _next(1)),
            IconButton(
              tooltip: widget.isFavorite(current)
                  ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti',
              icon: Icon(widget.isFavorite(current)
                  ? Icons.favorite : Icons.favorite_border),
              color: widget.isFavorite(current)
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
    required this.onRights, required this.onLicense,
    required this.onWallpaper});
  final Artwork artwork;
  final VoidCallback onMuseum;
  final VoidCallback? onRights;
  final VoidCallback? onLicense;
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
          if (!kIsWeb && artwork.wallpaperAllowed)
            TextButton.icon(onPressed: onWallpaper,
              icon: const Icon(Icons.wallpaper_outlined, size: 17),
              label: const Text('Imposta come sfondo'),
              style: TextButton.styleFrom(foregroundColor: Colors.white)),
          TextButton.icon(onPressed: onMuseum,
            icon: const Icon(Icons.open_in_new, size: 17),
            label: Text(artwork.isCuratedCommons
                ? 'Scheda originale su Wikimedia Commons'
                : 'Scheda originale del museo'),
            style: TextButton.styleFrom(foregroundColor: Colors.white70)),
          if (onRights != null)
            TextButton.icon(
              key: const Key('artdrift-image-rights-evidence'),
              onPressed: onRights,
              icon: const Icon(Icons.gavel_outlined, size: 17),
              label: const Text('Fonte e diritti dell’immagine'),
              style: TextButton.styleFrom(foregroundColor: Colors.white70)),
          if (onLicense != null)
            TextButton.icon(
              key: const Key('artdrift-image-license-terms'),
              onPressed: onLicense,
              icon: const Icon(Icons.open_in_new, size: 17),
              label: const Text('Condizioni della licenza'),
              style: TextButton.styleFrom(foregroundColor: Colors.white70)),
          const SizedBox(height: 10),
          Text((artwork.isCuratedCommons ? 'Archivio digitale: ' : 'Museo: ') +
              artwork.displayedMuseum,
            style: const TextStyle(color: Colors.white70, fontSize: 11)),
          if (artwork.medium.isNotEmpty || artwork.technique.isNotEmpty)
            Text('Tecnica: ' +
                (artwork.technique.isNotEmpty ? artwork.technique : artwork.medium),
              style: const TextStyle(color: Colors.white54, fontSize: 11)),
          if (artwork.dimensions.isNotEmpty)
            Text('Dimensioni: ' + artwork.dimensions,
              style: const TextStyle(color: Colors.white54, fontSize: 11)),
          const SizedBox(height: 8),
          Text('Licenza immagine: ${artwork.displayedLicense}',
            key: const Key('artdrift-image-license-label'),
            style: const TextStyle(color: Colors.white70, fontSize: 11)),
          if (artwork.imageCreator.isNotEmpty)
            Text('Riproduzione digitale: ${artwork.imageCreator}',
              style: const TextStyle(color: Colors.white54, fontSize: 11)),
          if (artwork.imageAttribution.isNotEmpty)
            Text(artwork.imageAttribution,
              key: const Key('artdrift-image-attribution'),
              style: const TextStyle(color: Colors.white54, fontSize: 11)),
          if (artwork.imageModifications.isNotEmpty)
            Text('Modifiche all’immagine: ${artwork.imageModifications}',
              style: const TextStyle(color: Colors.white54, fontSize: 11)),
          const SizedBox(height: 6),
          Text('Fonte: ${artwork.displayedMuseum}',
            style: const TextStyle(color: Colors.white38, fontSize: 10)),
        ],
      )),
    );
  }
}
