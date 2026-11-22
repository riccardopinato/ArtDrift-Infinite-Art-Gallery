import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/artwork.dart';
import '../services/art_offline_thumbnail_index.dart';
import 'art_remote_image.dart';

/// Compact, source-bound thumbnail used by search, favorites and details.
/// On Android it never requests a remote painting if its real WebP is bundled.
class ArtworkPreviewImage extends StatelessWidget {
  const ArtworkPreviewImage({
    super.key,
    required this.artwork,
    this.fit = BoxFit.cover,
    this.cacheWidth = 120,
  });

  final Artwork artwork;
  final BoxFit fit;
  final int cacheWidth;

  static String? bundledAssetFor(Artwork artwork) =>
      artwork.hasBundledPreview ? artwork.bootstrapAsset :
      ArtOfflineThumbnailIndex.instance.assetFor(artwork);

  @override
  Widget build(BuildContext context) {
    Widget unavailable() => const ColoredBox(
      color: Color(0xFF292832),
      child: Center(child: Icon(Icons.image_not_supported_outlined,
        color: Colors.white54, size: 20)),
    );
    final packagedAsset = bundledAssetFor(artwork);
    if (packagedAsset != null) {
      return Image.asset(
        packagedAsset,
        fit: fit,
        cacheWidth: cacheWidth,
        gaplessPlayback: true,
        filterQuality: FilterQuality.low,
        errorBuilder: (_, _, _) => unavailable(),
      );
    }
    final webThumb = ArtOfflineThumbnailIndex.instance.urlFor(artwork);
    final url = webThumb ?? artwork.imageUrl(width: 200);
    if (url.isEmpty) return unavailable();
    return Image.network(
      url,
      fit: fit,
      cacheWidth: kIsWeb ? null : cacheWidth,
      gaplessPlayback: true,
      filterQuality: FilterQuality.low,
      webHtmlElementStrategy: ArtRemoteImage.strategyFor(isWeb: kIsWeb &&
          webThumb == null),
      errorBuilder: (_, _, _) => unavailable(),
    );
  }
}
