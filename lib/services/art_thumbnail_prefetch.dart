import 'dart:async';
import 'dart:collection';

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';

import '../models/artwork.dart';
import 'art_offline_thumbnail_index.dart';
import 'art_image_warm_native.dart'
    if (dart.library.html) 'art_image_warm_web.dart' as image_warm;

/// Maximum simultaneous speculative downloads, with visible images handled
/// directly by the widgets. Warmups are never allowed to occupy all available
/// network slots or cache every artwork at startup.
typedef ArtWarmLoader = Future<bool> Function(
    BuildContext context, Artwork artwork, bool bundledPreview,
    bool highDetail);

class ArtThumbnailPrefetch {
  ArtThumbnailPrefetch._() : _warmer = _defaultWarm;
  @visibleForTesting
  ArtThumbnailPrefetch.testing({required ArtWarmLoader warmer})
      : _warmer = warmer;

  static final instance = ArtThumbnailPrefetch._();

  static const maxConcurrent = 3;
  static const maxQueued = 18;
  static const maxRecentKeys = 256;

  final ArtWarmLoader _warmer;
  final _waiting = Queue<_WarmArt>();
  final _inFlight = <String>{};
  final _cooldownUntil = LinkedHashMap<String, DateTime>();
  int _active = 0;

  @visibleForTesting
  int get activeCount => _active;
  @visibleForTesting
  int get queuedCount => _waiting.length;

  /// A single artwork can be loaded again after expiry or a transient error.
  /// A queue rejection is never stored in the cooldown map.
  Future<void> warm(BuildContext context, Artwork art, double zoom) {
    if (!context.mounted) return Future.value();
    final localAsset = art.hasBundledPreview
        ? art.bootstrapAsset
        : ArtOfflineThumbnailIndex.instance.assetFor(art);
    // ArtRemoteImage renders same-origin Web thumbnails at width 400 even
    // above zoom 1.65; only native tiles request remote detail at that zoom.
    // Never prefetch a remote image that the visible Web tile won't display.
    final webThumbnail = ArtOfflineThumbnailIndex.instance.urlFor(art);
    final highDetail = zoom > 1.65 && !(kIsWeb && webThumbnail != null);
    final bundledPreview = localAsset != null && !highDetail;
    // Align the cache identity with the actual image source being warmed.
    // On Web a small zoom can use the offline thumbnail URL; high zoom
    // must warm the remote detail that the visible tile will request.
    final localUrl = highDetail ? null : webThumbnail;
    final key = bundledPreview
        ? 'asset:$localAsset'
        : 'url:${localUrl ?? art.imageUrl(width: 400)}';
    final now = DateTime.now();
    final until = _cooldownUntil[key];
    if (_inFlight.contains(key) ||
        (until != null && now.isBefore(until)) ||
        _waiting.length >= maxQueued) return Future.value();

    final request = _WarmArt(key, context, art, bundledPreview,
        highDetail);
    _inFlight.add(key);
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
    var success = false;
    try {
      if (request.context.mounted) {
        success = await _warmer(
          request.context, request.art, request.bundledPreview,
          request.highDetail,
        ).timeout(const Duration(seconds: 8), onTimeout: () => false);
      }
    } catch (_) {
      success = false;
    } finally {
      _cooldownUntil.remove(request.key);
      _cooldownUntil[request.key] = DateTime.now().add(success
          ? const Duration(minutes: 4)
          : const Duration(seconds: 20));
      while (_cooldownUntil.length > maxRecentKeys) {
        _cooldownUntil.remove(_cooldownUntil.keys.first);
      }
      _inFlight.remove(request.key);
      if (!request.completer.isCompleted) request.completer.complete();
      _active--;
      _pump();
    }
  }

  static Future<bool> _defaultWarm(
      BuildContext context, Artwork art, bool bundledPreview,
      bool highDetail) async {
    if (!context.mounted) return false;
    if (!bundledPreview) {
      final localUrl = highDetail ? null :
          ArtOfflineThumbnailIndex.instance.urlFor(art);
      if (localUrl != null) {
        var failed = false;
        try {
          await precacheImage(NetworkImage(localUrl), context,
              onError: (error, stack) { failed = true; })
              .timeout(const Duration(seconds: 5));
          return !failed;
        } catch (_) {
          return false;
        }
      }
      return image_warm.warmMuseumImage(context, art.imageUrl(width: 400));
    }
    var failed = false;
    try {
      // Match Image.asset(cacheWidth: 240) used by the displayed tile.
      final localAsset = art.hasBundledPreview ? art.bootstrapAsset :
          ArtOfflineThumbnailIndex.instance.assetFor(art);
      if (localAsset == null) return false;
      final image = ResizeImage.resizeIfNeeded(
          240, null, AssetImage(localAsset));
      await precacheImage(image, context, onError: (error, stack) {
        failed = true;
      }).timeout(const Duration(seconds: 7));
      return !failed;
    } catch (_) {
      return false;
    }
  }
}

class _WarmArt {
  _WarmArt(this.key, this.context, this.art, this.bundledPreview,
      this.highDetail);

  final String key;
  final BuildContext context;
  final Artwork art;
  final bool bundledPreview;
  final bool highDetail;
  final Completer<void> completer = Completer<void>();
}
