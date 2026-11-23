import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:drift_core/drift_core.dart';
import '../models/artwork.dart';
import '../ui/art_remote_image.dart';
import '../services/art_thumbnail_prefetch.dart';
import '../services/art_offline_thumbnail_index.dart';

/// Art-specific adapter. Visual appearance, preview and camera keys preserved.
class InfiniteGallery extends StatefulWidget {
  const InfiniteGallery({super.key, required this.artworks, required this.onOpen,
    this.onOpenAtRect, this.onToggleFavorite, this.isFavorite,
    this.onImmersiveChanged, this.cameraKey = 'artdrift.camera'});
  final List<Artwork> artworks;
  final ValueChanged<Artwork> onOpen;
  final void Function(Artwork art, Rect tileRect)? onOpenAtRect;
  final Future<void> Function(Artwork art)? onToggleFavorite;
  final bool Function(Artwork art)? isFavorite;
  final ValueChanged<bool>? onImmersiveChanged;
  final String cameraKey;

  @override
  State<InfiniteGallery> createState() => _InfiniteGalleryState();
}

class _InfiniteGalleryState extends State<InfiniteGallery> {
  Artwork? _inspected;
  Rect? _inspectedRect;

  void _inspect(Artwork artwork, Rect rect) {
    setState(() {
      _inspected = artwork;
      _inspectedRect = rect;
    });
  }

  void _dismiss() {
    if (_inspected != null) setState(() {
      _inspected = null;
      _inspectedRect = null;
    });
  }

  void _open(Artwork artwork, Rect rect) {
    _dismiss();
    final precise = widget.onOpenAtRect;
    if (precise == null) widget.onOpen(artwork);
    else precise(artwork, rect);
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
      final artwork = _inspected;
      final rect = _inspectedRect;
      final cardWidth = math.min(290.0, math.max(1.0, constraints.maxWidth - 24));
      final left = rect == null ? 12.0 : rect.left
          .clamp(12.0, math.max(12.0, constraints.maxWidth - cardWidth - 12));
      final top = rect == null ? 120.0 : (
        rect.bottom + 10 + 225 <= constraints.maxHeight
            ? rect.bottom + 10
            : math.max(16.0, rect.top - 235)
      ).clamp(16.0, math.max(16.0, constraints.maxHeight - 225));
      return Stack(fit: StackFit.expand, children: [
        DriftCanvas<Artwork>(
          items: widget.artworks, onOpen: widget.onOpen,
          onOpenAtRect: _open,
          onTileLongPress: _inspect,
          onCanvasGestureStart: _dismiss,
          onImmersiveChanged: widget.onImmersiveChanged,
          museumControls: true,
          tileBuilder: (context, art, zoom) => _tileImage(art, zoom),
          prefetchItem: ArtThumbnailPrefetch.instance.warm,
          cameraKey: widget.cameraKey,
          compactBrand: 'A∞',
          fullBrand: 'artdrift  ∞',
          hintText: 'Trascina per esplorare  ·  Tocca un’opera',
          recenterTooltip: 'Torna al centro',
        ),
        if (artwork != null && rect != null) Positioned(
          left: left, top: top, width: cardWidth,
          child: Material(
            key: const Key('artdrift-museum-tile-plaque'),
            elevation: 8,
            color: const Color(0xFFF1E5CF),
            shape: RoundedRectangleBorder(
              side: const BorderSide(color: Color(0xFFAA8A60)),
              borderRadius: BorderRadius.circular(7)),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(13, 9, 8, 11),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(children: [
                    const Expanded(child: Text('ARTDRIFT · TARGHETTA',
                      style: TextStyle(color: Color(0xFF8A6B46),
                        fontSize: 9, letterSpacing: 1))),
                    IconButton(
                      key: const Key('artdrift-museum-plaque-close'),
                      constraints: const BoxConstraints(minWidth: 38,
                        minHeight: 38),
                      padding: EdgeInsets.zero,
                      tooltip: 'Chiudi targhetta',
                      onPressed: _dismiss,
                      icon: const Icon(Icons.close, color: Color(0xFF6C5036))),
                  ]),
                  const Divider(color: Color(0xFFC1AA88), height: 6),
                  Text(artwork.title,
                    maxLines: 2, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Color(0xFF34281D),
                      fontFamily: 'serif', fontSize: 17)),
                  const SizedBox(height: 5),
                  Text(artwork.artist.isEmpty ? 'Autore sconosciuto'
                    : artwork.artist,
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Color(0xFF765B40),
                      fontSize: 11)),
                  if (artwork.date.isNotEmpty) Text(artwork.date,
                    style: const TextStyle(color: Color(0xFF765B40),
                      fontSize: 11)),
                  const SizedBox(height: 5),
                  Text(artwork.displayedMuseum,
                    maxLines: 2, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Color(0xFF8A6C49),
                      fontSize: 10)),
                  const SizedBox(height: 9),
                  Row(children: [
                    Expanded(child: OutlinedButton(
                      key: const Key('artdrift-museum-plaque-open'),
                      onPressed: () => _open(artwork, rect),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF5A422A),
                        side: const BorderSide(color: Color(0xFFBBA07A))),
                      child: const Text('Dettagli'))),
                    if (widget.onToggleFavorite != null) IconButton(
                      key: const Key('artdrift-museum-plaque-favorite'),
                      tooltip: widget.isFavorite?.call(artwork) == true
                        ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti',
                      onPressed: () async {
                        await widget.onToggleFavorite!(artwork);
                        if (mounted) setState(() {});
                      },
                      icon: Icon(widget.isFavorite?.call(artwork) == true
                        ? Icons.favorite : Icons.favorite_border,
                        color: const Color(0xFF946B48))),
                  ]),
                ],
              ),
            ),
          ),
        ),
      ]);
    },
  );
}
