import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/artwork.dart';

/// Art-only network image: on browsers, retry with an HTML image element if
/// fetching bytes is blocked by a museum's cross-origin policy.
/// This does not bypass HTTP 403/404, hotlink protection or image rights.
/// Android retains its existing byte-decoding behavior.
class ArtRemoteImage extends StatelessWidget {
  const ArtRemoteImage({
    super.key,
    required this.artwork,
    required this.width,
    required this.fit,
    required this.fallback,
    required this.loading,
  });

  final Artwork artwork;
  final int width;
  final BoxFit fit;
  final Widget fallback;
  final Widget loading;

  @visibleForTesting
  static WebHtmlElementStrategy strategyFor({required bool isWeb}) =>
      isWeb
          ? WebHtmlElementStrategy.prefer
          : WebHtmlElementStrategy.never;

  @visibleForTesting
  static List<String> candidateUrls(Artwork artwork, {required int width}) {
    final urls = <String>[
      artwork.imageUrl(width: width),
      if (width > 400) artwork.imageUrl(width: 400),
    ];
    return List.unmodifiable(urls.where((url) => url.isNotEmpty).toSet());
  }

  @override
  Widget build(BuildContext context) {
    final urls = candidateUrls(artwork, width: width);
    if (urls.isEmpty) return fallback;

    Widget imageAt(int index) => Image.network(
          urls[index],
          fit: fit,
          filterQuality: FilterQuality.low,
          cacheWidth: width,
          gaplessPlayback: true,
          webHtmlElementStrategy: strategyFor(isWeb: kIsWeb),
          loadingBuilder: (context, child, progress) =>
              progress == null ? child : loading,
          errorBuilder: (context, error, stack) =>
              index + 1 < urls.length ? imageAt(index + 1) : fallback,
        );

    return imageAt(0);
  }
}
