import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import '../models/artwork.dart';

/// Web-only source-gated offline image manifest. No Android assets added.
class ArtOfflineThumbnailIndex {
  ArtOfflineThumbnailIndex._();
  static final instance = ArtOfflineThumbnailIndex._();
  Set<String> _keys = const {};
  Future<void>? _loading;

  @visibleForTesting
  int get availableCount => _keys.length;

  @visibleForTesting
  void loadFromManifest(String raw) {
    final json = jsonDecode(raw);
    if (json is! Map || json['schema_version'] != 1 ||
        json['keys'] is! List) {
      throw const FormatException('Invalid Web thumbnail manifest');
    }
    final result = <String>{};
    for (final v in json['keys'] as List) {
      if (v is! String || !RegExp(r'^[a-z]+:[0-9]+$').hasMatch(v)) {
        throw const FormatException('Invalid thumbnail identity');
      }
      result.add(v);
    }
    _keys = Set.unmodifiable(result);
  }

  Future<void> initialize() => _loading ??= _load();

  Future<void> _load() async {
    if (!kIsWeb) {
      // AssetBundle-backed on Android: 1,142 verified small WebPs are usable
      // immediately without any mobile network request or mutable disk cache.
      try {
        loadFromManifest(await rootBundle.loadString(
            'web/museum_thumbs/manifest.json'));
      } catch (error) {
        // The original bundled museum previews remain usable independently.
        // Keep a debug-only diagnostic so pack/asset mistakes are observable.
        if (kDebugMode) debugPrint('Mobile thumbnail manifest: $error');
      }
      return;
    }
    try {
      final response = await http.get(Uri.base.resolve(
          'museum_thumbs/manifest.json')).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) loadFromManifest(response.body);
    } catch (_) {
      // Never claim a thumbnail exists without a valid manifest.
    }
  }

  bool has(Artwork artwork) => artwork.displayable &&
      !artwork.hasBundledPreview && _keys.contains(artwork.catalogKey);

  /// Flutter asset namespace used on Android. These are the exact artwork
  /// thumbnails declared in the validated, packaged manifest.
  String? assetFor(Artwork artwork) {
    if (kIsWeb || !has(artwork)) return null;
    return 'web/museum_thumbs/${artwork.museumSource}_${artwork.id}.webp';
  }

  String? urlFor(Artwork artwork) {
    if (!kIsWeb || !has(artwork)) return null;
    return Uri.base.resolve('museum_thumbs/' +
        artwork.museumSource + '_' + artwork.id.toString() + '.webp')
        .toString();
  }
}
