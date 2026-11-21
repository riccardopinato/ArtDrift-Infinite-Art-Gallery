import 'package:flutter/material.dart';
import 'package:drift_core/drift_core.dart';
import '../models/artwork.dart';

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
    return const ColoredBox(
      color: Color(0xFF24232A),
      child: Center(child: Icon(Icons.image_not_supported_outlined,
          color: Colors.white30, size: 22)),
    );
  }

  Widget _tileImage(Artwork art, double zoom) {
    // Real bundled WebP previews show on the very first frame even offline.
    // Zooming in opts into a higher-detail remote IIIF rendition only then.
    if (art.hasBundledPreview && zoom <= 1.65) return _preview(art);
    return Image.network(
      art.imageUrl(width: 400),
      fit: BoxFit.cover,
      filterQuality: FilterQuality.low,
      cacheWidth: 400,
      gaplessPlayback: true,
      loadingBuilder: (context, child, progress) =>
          progress == null ? child : _preview(art),
      errorBuilder: (_, error, stack) => _preview(art),
    );
  }


  @override
  Widget build(BuildContext context) => DriftCanvas<Artwork>(
    items: artworks, onOpen: onOpen,
    tileBuilder: (context, art, zoom) => _tileImage(art, zoom),
    cameraKey: 'artdrift.camera',
    compactBrand: 'A∞',
    fullBrand: 'artdrift  ∞',
    hintText: 'Trascina per esplorare  ·  Tocca un’opera',
    recenterTooltip: 'Torna al centro',
  );
}
