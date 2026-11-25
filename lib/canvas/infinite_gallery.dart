import 'package:flutter/material.dart';
import 'package:drift_core/drift_core.dart';
import '../models/artwork.dart';
import '../ui/art_remote_image.dart';
import '../services/art_thumbnail_prefetch.dart';
import '../services/art_offline_thumbnail_index.dart';

/// Art-specific adapter. Visual appearance, preview and camera keys preserved.
class InfiniteGallery extends StatelessWidget {
  const InfiniteGallery({super.key, required this.artworks, required this.onOpen,
    this.cameraKey = 'artdrift.camera', this.initialWorldCenter});
  final List<Artwork> artworks;
  final ValueChanged<Artwork> onOpen;
  final String cameraKey;
  final Offset? initialWorldCenter;

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
  Widget build(BuildContext context) => DriftCanvas<Artwork>(
    items: artworks, onOpen: onOpen,
    tileBuilder: (context, art, zoom) => _tileImage(art, zoom),
    prefetchItem: ArtThumbnailPrefetch.instance.warm,
    cameraKey: cameraKey,
    initialWorldCenter: initialWorldCenter,
    compactBrand: 'A∞',
    fullBrand: 'artdrift  ∞',
    hintText: 'Trascina per esplorare  ·  Tocca un’opera',
    recenterTooltip: 'Torna al centro',
  );
}
