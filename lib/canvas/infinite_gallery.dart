import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:drift_core/drift_core.dart';
import '../models/artwork.dart';
import '../ui/art_remote_image.dart';

/// Art-specific adapter. Visual appearance, preview and camera keys preserved.
class InfiniteGallery extends StatelessWidget {
  const InfiniteGallery({super.key, required this.artworks, required this.onOpen});
  final List<Artwork> artworks;
  final ValueChanged<Artwork> onOpen;

  Widget _preview(Artwork art) {
    if (art.hasBundledPreview) {
      return Image.asset(
        art.bootstrapAsset,
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
    if (art.hasBundledPreview && zoom <= 1.65) return _preview(art);
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
    prefetchItem: (context, art, zoom) async {
      if (!context.mounted) return;
      if (art.hasBundledPreview && zoom <= 1.65) {
        await precacheImage(AssetImage(art.bootstrapAsset), context,
            onError: (error, stack) {});
        return;
      }
      // Mirror ArtRemoteImage's browser strategy and image dimensions.
      final provider = NetworkImage(art.imageUrl(width: 400),
        webHtmlElementStrategy: ArtRemoteImage.strategyFor(isWeb: kIsWeb));
      await precacheImage(
        ResizeImage.resizeIfNeeded(kIsWeb ? null : 400, null, provider),
        context, onError: (error, stack) {});
    },
    cameraKey: 'artdrift.camera',
    compactBrand: 'A∞',
    fullBrand: 'artdrift  ∞',
    hintText: 'Trascina per esplorare  ·  Tocca un’opera',
    recenterTooltip: 'Torna al centro',
  );
}
