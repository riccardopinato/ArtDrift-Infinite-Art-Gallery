import 'dart:async';
import 'dart:collection';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/artwork.dart';
import '../ui/art_remote_image.dart';

/// Limits speculative museum requests. On-screen loads always retain priority
/// in Flutter; speculation never delays detail-view image requests.
class ArtThumbnailPrefetch {
  ArtThumbnailPrefetch._();
  static final instance = ArtThumbnailPrefetch._();

  static const maxConcurrent = 4;
  static const maxQueued = 24;
  static const maxRecentKeys = 256;

  final _waiting = Queue<_WarmArt>();
  final _known = <String>{};
  final _recent = Queue<String>();
  int _active = 0;

  Future<void> warm(BuildContext context, Artwork art, double zoom) {
    if (!context.mounted) return Future.value();
    final assetPreview = art.hasBundledPreview && zoom <= 1.65;
    final key = '${art.catalogKey}:${assetPreview ? 'local' : 'remote'}';
    if (_known.contains(key) || _waiting.length >= maxQueued) {
      return Future.value();
    }
    _known.add(key);
    _recent.add(key);
    while (_recent.length > maxRecentKeys) {
      _known.remove(_recent.removeFirst());
    }

    final request = _WarmArt(context, art, assetPreview);
    _waiting.addLast(request);
    _pump();
    return request.completer.future;
  }

  void _pump() {
    while (_active < maxConcurrent && _waiting.isNotEmpty) {
      _active++;
      unawaited(_resolve(_waiting.removeFirst()));
    }
  }

  Future<void> _resolve(_WarmArt request) async {
    try {
      if (!request.context.mounted) return;
      final art = request.art;
      final ImageProvider provider = request.assetPreview
          ? AssetImage(art.bootstrapAsset)
          : ResizeImage.resizeIfNeeded(
              kIsWeb ? null : 400,
              null,
              NetworkImage(art.imageUrl(width: 400),
                webHtmlElementStrategy: ArtRemoteImage.strategyFor(isWeb: kIsWeb)));
      await precacheImage(provider, request.context,
        onError: (error, stack) {}).timeout(const Duration(seconds: 8));
    } catch (_) {
      // Prefetch failure never blocks on-screen fallback or manual navigation.
    } finally {
      if (!request.completer.isCompleted) request.completer.complete();
      _active--;
      _pump();
    }
  }
}

class _WarmArt {
  _WarmArt(this.context, this.art, this.assetPreview);
  final BuildContext context;
  final Artwork art;
  final bool assetPreview;
  final Completer<void> completer = Completer<void>();
}
