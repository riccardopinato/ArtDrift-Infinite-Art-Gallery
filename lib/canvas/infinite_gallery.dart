import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:drift_core/drift_core.dart';

import '../models/artwork.dart';
import '../services/art_thumbnail_prefetch.dart';
import '../services/art_offline_thumbnail_index.dart';
import '../ui/art_remote_image.dart';
import '../ui/localization.dart';
import '../ui/parchment.dart';

/// Art-only museum interaction adapter.
/// Artwork/source identity and camera remain owned by canonical Drift Core.
class InfiniteGallery extends StatefulWidget {
  const InfiniteGallery({
    super.key,
    required this.artworks,
    required this.onOpen,
    this.cameraKey = 'artdrift.camera',
  });

  final List<Artwork> artworks;
  final ValueChanged<Artwork> onOpen;
  final String cameraKey;

  @override
  State<InfiniteGallery> createState() => _InfiniteGalleryState();
}

class _InfiniteGalleryState extends State<InfiniteGallery> {
  Artwork? _inspectedArtwork;
  Rect? _inspectedTile;

  static const _copy = <String, List<String>>{
    'it': ['L’OPERA', 'Apri la scheda', 'Chiudi'],
    'en': ['THE ARTWORK', 'Open artwork', 'Close'],
    'fr': ['L’ŒUVRE', 'Ouvrir la fiche', 'Fermer'],
    'es': ['LA OBRA', 'Abrir la ficha', 'Cerrar'],
    'de': ['DAS WERK', 'Werk öffnen', 'Schließen'],
    'pt': ['A OBRA', 'Abrir a ficha', 'Fechar'],
  };

  void _hidePlaque() {
    if (_inspectedArtwork != null && mounted) {
      setState(() {
        _inspectedArtwork = null;
        _inspectedTile = null;
      });
    }
  }

  void _inspect(Artwork item, Rect rect) {
    if (!mounted) return;
    setState(() {
      _inspectedArtwork = item;
      _inspectedTile = rect;
    });
  }

  Widget _preview(Artwork art) {
    final localAsset = art.hasBundledPreview
        ? art.bootstrapAsset
        : ArtOfflineThumbnailIndex.instance.assetFor(art);
    if (localAsset != null) {
      return Image.asset(
        localAsset,
        fit: BoxFit.cover,
        filterQuality: FilterQuality.low,
        cacheWidth: 240,
        gaplessPlayback: true,
        errorBuilder: (_, error, stack) => const ColoredBox(
          color: Color(0xFF24232A),
          child: Center(child: Icon(Icons.image_not_supported_outlined,
              color: Colors.white30, size: 22)),
        ),
      );
    }
    // Do not substitute another painting when a museum refuses an image.
    return ColoredBox(
      color: const Color(0xFF24232A),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Center(child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.account_balance_outlined,
                color: Colors.white24, size: 20),
            const SizedBox(height: 9),
            Text(art.title, maxLines: 3, overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white60, fontSize: 11)),
            const SizedBox(height: 5),
            Text(art.displayedMuseum, maxLines: 2,
                overflow: TextOverflow.ellipsis, textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white30, fontSize: 9)),
          ],
        )),
      ),
    );
  }

  Widget _tileImage(Artwork art, double zoom) {
    // Real bundled WebP previews show on the very first frame even offline.
    // Zooming in opts into a higher-detail remote IIIF rendition only then.
    if (zoom <= 1.65 && (art.hasBundledPreview ||
        ArtOfflineThumbnailIndex.instance.assetFor(art) != null)) {
      return _preview(art);
    }
    return ArtRemoteImage(
      artwork: art,
      width: 400,
      fit: BoxFit.cover,
      fallback: _preview(art),
      loading: _preview(art),
    );
  }



  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final item = _inspectedArtwork;
      final tile = _inspectedTile;
      final maxW = constraints.maxWidth;
      final maxH = constraints.maxHeight;
      final plaqueWidth = math.max(140.0, math.min(286.0, maxW - 24.0));
      final x = tile == null ? 12.0 : (tile.center.dx - plaqueWidth / 2)
          .clamp(12.0, math.max(12.0, maxW - plaqueWidth - 12.0))
          .toDouble();
      final below = tile == null ? 12.0 : tile.bottom + 12.0;
      final above = tile == null ? 12.0 : tile.top - 210.0;
      final y = (below + 205 < maxH ? below : math.max(12.0, above))
          .clamp(12.0, math.max(12.0, maxH - 186.0))
          .toDouble();
      final strings = _copy[ArtDriftLocale.current.value] ?? _copy['en']!;

      return Stack(fit: StackFit.expand, children: [
        DriftCanvas<Artwork>(
          items: widget.artworks,
          onOpen: widget.onOpen,
          onOpenAtRect: (art, _) {
            _hidePlaque();
            widget.onOpen(art);
          },
          onTileLongPress: _inspect,
          onCanvasGestureStart: _hidePlaque,
          onImmersiveChanged: (_) => _hidePlaque(),
          museumControls: true,
          tileBuilder: (context, art, zoom) => _tileImage(art, zoom),
          prefetchItem: ArtThumbnailPrefetch.instance.warm,
          cameraKey: widget.cameraKey,
          compactBrand: 'A∞',
          fullBrand: 'artdrift  ∞',
          hintText: 'Trascina per esplorare  ·  Tocca un’opera',
          recenterTooltip: 'Torna al centro',
        ),
        if (item != null && tile != null)
          Positioned(
            left: x, top: y, width: plaqueWidth,
            child: Material(
              color: Colors.transparent,
              elevation: 8,
              borderRadius: BorderRadius.circular(9),
              child: OrnateFrame(
                padding: const EdgeInsets.fromLTRB(17, 15, 17, 12),
                child: ConstrainedBox(
                  constraints: BoxConstraints(maxHeight: math.max(120.0, maxH - 24.0)),
                  child: SingleChildScrollView(child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(strings[0], style: const TextStyle(
                        color: ArtPaper.gold, fontSize: 10,
                        letterSpacing: 1.8, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 7),
                      Text(item.title, maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: ArtPaper.ink, fontFamily: 'serif',
                          fontSize: 18, height: 1.15)),
                      const SizedBox(height: 4),
                      Text([
                        item.artist,
                        if (item.date.trim().isNotEmpty) item.date.trim(),
                      ].where((s) => s.trim().isNotEmpty).join(' · '),
                        maxLines: 2, overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: ArtPaper.faded, fontSize: 11)),
                      const SizedBox(height: 12),
                      Row(children: [
                        Expanded(child: OutlinedButton(
                          key: const Key('artdrift-museum-plaque-open'),
                          onPressed: () {
                            _hidePlaque();
                            widget.onOpen(item);
                          },
                          style: OutlinedButton.styleFrom(
                            foregroundColor: ArtPaper.ink,
                            side: const BorderSide(color: ArtPaper.gold),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 9)),
                          child: Text(strings[1], maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 12)),
                        )),
                        IconButton(
                          tooltip: strings[2],
                          onPressed: _hidePlaque,
                          color: ArtPaper.ink,
                          icon: const Icon(Icons.close, size: 19)),
                      ]),
                    ],
                  )),
                ),
              ),
            ),
          ),
      ]);
    },
  );
}
