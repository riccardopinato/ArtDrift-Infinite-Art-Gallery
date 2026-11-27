import 'package:flutter/material.dart';

import '../canvas/infinite_gallery.dart';
import '../collections/art_collections.dart';
import '../models/artwork.dart';
import '../ui/localization.dart';

/// Reuses the approved immersive mosaic, with an independent camera per
/// collection. No local image uploads and no remote search on entry.
class ArtCollectionCanvasScreen extends StatelessWidget {
  const ArtCollectionCanvasScreen({
    super.key,
    required this.collection,
    required this.artworks,
    required this.onOpen,
  });

  final ArtCollection collection;
  final List<Artwork> artworks;
  final void Function(Artwork, List<Artwork>) onOpen;

  @override
  Widget build(BuildContext context) {
    final language = ArtDriftLocale.current.value;
    return Scaffold(
      body: Stack(fit: StackFit.expand, children: [
        InfiniteGallery(
          artworks: artworks,
          onOpen: (art) => onOpen(art, artworks),
          cameraKey: 'artdrift.collection.${collection.id}.camera',
        ),
        // Reserve the top-left area for the shared canvas brand, Auto
        // and speed controls; collection navigation stays on the right.
        Positioned(
          top: 0, right: 12,
          child: SafeArea(
            bottom: false,
            child: SizedBox(
              width: MediaQuery.sizeOf(context).width * 0.46,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Material(
                    color: const Color(0xE51B1B22),
                    borderRadius: BorderRadius.circular(12),
                    child: IconButton(
                      key: const ValueKey('collection-back'),
                      tooltip: 'Back',
                      onPressed: () => Navigator.of(context).pop(),
                      color: Colors.white,
                      icon: const Icon(Icons.arrow_back_rounded),
                    ),
                  ),
                  const SizedBox(height: 6),
                  DecoratedBox(
                    decoration: BoxDecoration(
                      color: const Color(0xE51B1B22),
                      borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 8),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(collection.title(language),
                            maxLines: 1, overflow: TextOverflow.ellipsis,
                            style: const TextStyle(color: Colors.white,
                              fontSize: 15, fontWeight: FontWeight.w600)),
                          Text('${artworks.length} · ${collection.subtitle(language)}',
                            maxLines: 1, overflow: TextOverflow.ellipsis,
                            style: const TextStyle(color: Colors.white70,
                              fontSize: 10)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ]),
    );
  }
}
