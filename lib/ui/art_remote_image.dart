import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/artwork.dart';
import '../services/art_offline_thumbnail_index.dart';

/// Displays the museum's own image. Web images use HTML platform views to
/// avoid CORS failures; no third-party proxy or substituted artwork is used.
///
/// A bounded *visible-only* retry recovers short network interruptions.
/// Non-transient 403/404/hotlink denials remain the museum's responsibility.
class ArtRemoteImage extends StatefulWidget {
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

  static WebHtmlElementStrategy strategyFor({required bool isWeb}) =>
      isWeb ? WebHtmlElementStrategy.prefer : WebHtmlElementStrategy.never;

  @visibleForTesting
  static List<String> candidateUrls(Artwork artwork, {required int width}) {
    final urls = <String>[
      artwork.imageUrl(width: width),
      if (width > 400) artwork.imageUrl(width: 400),
    ];
    return List.unmodifiable(urls.where((url) => url.isNotEmpty).toSet());
  }

  @override
  State<ArtRemoteImage> createState() => _ArtRemoteImageState();
}

class _ArtRemoteImageState extends State<ArtRemoteImage> {
  static const maxRetryCount = 1;
  static const retryDelay = Duration(milliseconds: 1600);
  int _retryCount = 0;
  Timer? _retryTimer;

  @override
  void didUpdateWidget(covariant ArtRemoteImage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.artwork.catalogKey != widget.artwork.catalogKey ||
        oldWidget.width != widget.width) {
      _retryTimer?.cancel();
      _retryTimer = null;
      _retryCount = 0;
    }
  }

  void _retryWhenVisible() {
    if (_retryCount >= maxRetryCount || _retryTimer != null) return;
    // Never call setState synchronously inside Image.errorBuilder.
    _retryTimer = Timer(retryDelay, () {
      _retryTimer = null;
      if (mounted) setState(() => _retryCount++);
    });
  }

  @override
  void dispose() {
    _retryTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final urls = ArtRemoteImage.candidateUrls(
        widget.artwork, width: widget.width);
    if (urls.isEmpty) return widget.fallback;

    final localUrl = ArtOfflineThumbnailIndex.instance.urlFor(widget.artwork);
    final nativeAsset = ArtOfflineThumbnailIndex.instance.assetFor(widget.artwork);
    Widget nativePreview({required Widget Function() onError}) => Image.asset(
          nativeAsset!,
          fit: widget.fit,
          cacheWidth: 240,
          filterQuality: FilterQuality.low,
          gaplessPlayback: true,
          errorBuilder: (context, error, stack) => onError(),
        );
    // Local files are tiny same-origin WebP; unlike museum HTML platform views,
    // Flutter can decode them efficiently into a regular image layer.
    Widget packaged({required Widget Function() onError}) => Image.network(
          localUrl!,
          fit: widget.fit,
          cacheWidth: kIsWeb ? null : widget.width,
          gaplessPlayback: true,
          webHtmlElementStrategy: WebHtmlElementStrategy.never,
          errorBuilder: (context, error, stack) => onError(),
        );
    Widget initialPreview() => nativeAsset != null
        ? nativePreview(onError: () => widget.loading)
        : localUrl != null
            ? packaged(onError: () => widget.loading)
            : widget.loading;
    Widget finalFallback() => nativeAsset != null
        ? nativePreview(onError: () => widget.fallback)
        : localUrl != null
            ? packaged(onError: () => widget.fallback)
            : widget.fallback;

    Widget imageAt(int index) {
      final url = urls[index];
      return Image.network(
        url,
        key: ValueKey('${widget.artwork.catalogKey}:$index:$_retryCount'),
        fit: widget.fit,
        cacheWidth: kIsWeb ? null : widget.width,
        filterQuality: FilterQuality.low,
        gaplessPlayback: true,
        webHtmlElementStrategy: ArtRemoteImage.strategyFor(isWeb: kIsWeb),
        // frameBuilder avoids rebuilding on every byte of network progress.
        // Keep the lower-quality artwork visible until a full frame arrives.
        frameBuilder: (context, child, frame, wasSynchronouslyLoaded) =>
            wasSynchronouslyLoaded || frame != null ? child : initialPreview(),
        errorBuilder: (_, error, stack) {
          if (index + 1 < urls.length) return imageAt(index + 1);
          _retryWhenVisible();
          return finalFallback();
        },
      );
    }

    if (nativeAsset != null && widget.width <= 400) {
      return nativePreview(onError: () => imageAt(0));
    }
    if (localUrl != null && widget.width <= 400) {
      return packaged(onError: () => imageAt(0));
    }
    return imageAt(0);
  }
}
