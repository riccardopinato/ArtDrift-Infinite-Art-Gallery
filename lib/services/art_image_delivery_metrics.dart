import 'package:flutter/painting.dart';

import '../models/artwork.dart';

/// Bounded, local-only counts of failed museum-image loads. No raw URL,
/// user identifiers, search queries, artwork IDs or network transmissions.
class ArtImageDeliveryMetrics {
  ArtImageDeliveryMetrics._();

  static final instance = ArtImageDeliveryMetrics._();
  static const int maxSources = 16;
  static const int maxCount = 1000000;

  final _errorsBySource = <String, Map<String, int>>{};

  int get trackedSourceCount => _errorsBySource.length;

  void clear() => _errorsBySource.clear();

  void recordFailure(Artwork art, Object error) {
    final source = art.museumSource;
    if (!RegExp(r'^[a-z]{2,16}$').hasMatch(source)) return;
    final status = error is NetworkImageLoadException ? error.statusCode : null;
    final category = status == 403 ? 'http_403' :
        status == 404 ? 'http_404' :
        status != null ? 'http_other' : 'network_or_decode';
    if (!_errorsBySource.containsKey(source) &&
        _errorsBySource.length >= maxSources) return;
    final counts = _errorsBySource.putIfAbsent(source, () => <String, int>{});
    final old = counts[category] ?? 0;
    counts[category] = old >= maxCount ? old : old + 1;
  }

  String get report {
    if (_errorsBySource.isEmpty) {
      return 'Museum image failures: none recorded in this session.';
    }
    final lines = ['Museum image failures (local, cumulative this session):'];
    final sources = _errorsBySource.keys.toList()..sort();
    for (final source in sources) {
      final counts = _errorsBySource[source]!;
      final labels = counts.keys.toList()..sort();
      lines.add('$source: ' +
          labels.map((label) => '$label=${counts[label]}').join(', '));
    }
    lines.add('Counts are request failures, not missing-image ratios or');
    lines.add('verified museum outages. No image URLs are retained.');
    return lines.join('\n');
  }
}
