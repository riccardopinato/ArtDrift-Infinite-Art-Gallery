import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:flutter/services.dart';

import '../models/artwork.dart';
import '../museums/museum_catalog.dart';

/// Museum Open Access client. Does not scrape or consume anotherboring.day.
/// A saved catalogue snapshot keeps artwork placement stable across launches.
class CatalogService {
  CatalogService({http.Client? client}) : _client = client ?? http.Client();
  final http.Client _client;
  static const _fields =
      'id,title,artist_title,artist_display,date_display,image_id,'
      'is_public_domain,artwork_type_title,medium_display,'
      'credit_line,place_of_origin,thumbnail';

  Future<File> _cacheFile() async {
    final directory = await getApplicationSupportDirectory();
    return File('${directory.path}/artdrift-catalog-v1.json');
  }

  Future<List<Artwork>> cached() async {
    try {
      final file = await _cacheFile();
      if (!await file.exists()) return const [];
      final data = jsonDecode(await file.readAsString());
      if (data is! List) return const [];
      return data.whereType<Map<String, dynamic>>()
          .map(Artwork.fromJson).where((a) => a.displayable).toList();
    } catch (_) {
      return const [];
    }
  }

  /// Tiny images + metadata are bundled at build time, so the very first
  /// screen is real paintings rather than a remote-API loading spinner.
  Future<List<Artwork>> bundled() async {
    try {
      final source = await rootBundle.loadString('assets/gallery/catalog.json');
      final data = jsonDecode(source);
      if (data is! List) return const [];
      return data.whereType<Map<String, dynamic>>()
          .map(Artwork.fromJson)
          .where((a) => a.displayable && a.hasBundledPreview)
          .toList(growable: false);
    } catch (_) {
      return const [];
    }
  }

  Future<List<Artwork>> load({bool refresh = false}) async {
    final original = await bundled();
    final extended = await const MuseumCatalog().bundled();
    final builtIn = MuseumCatalog.combine(original, extended);
    // A known-good build-time snapshot is authoritative for initial display.
    // This also preserves which artwork occupies which stable world tile.
    if (builtIn.isNotEmpty && !refresh) return builtIn;
    final existing = await cached();
    if (existing.isNotEmpty && !refresh) return existing;
    final collected = <int, Artwork>{};
    Object? lastError;
    // A few targeted queries produce a varied, art-first selection without
    // requesting an entire institution's database or using an unofficial feed.
    const subjects = [
      'landscape', 'impressionism', 'flowers', 'portrait',
      'still life', 'seascape', 'painting',
    ];
    for (final subject in subjects) {
      try {
        final uri = Uri.https('api.artic.edu', '/api/v1/artworks/search', {
          'q': subject,
          'query[term][is_public_domain]': 'true',
          'fields': _fields,
          'limit': '100',
        });
        final response = await _client.get(uri, headers: {
          'Accept': 'application/json',
          'AIC-User-Agent': 'ArtDrift/0.1 (independent Android art viewer)',
        }).timeout(const Duration(seconds: 18));
        if (response.statusCode != 200) {
          throw HttpException('Art Institute API HTTP ${response.statusCode}');
        }
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        if (decoded is! Map<String, dynamic> || decoded['data'] is! List) {
          throw const FormatException('Invalid museum response');
        }
        for (final row in decoded['data'] as List) {
          if (row is! Map<String, dynamic>) continue;
          final art = Artwork.fromJson(row);
          if (art.displayable) collected[art.id] = art;
        }
        if (collected.length >= 160) break;
        // Provider-friendly, bounded requests; never parallel scrape images.
        await Future<void>.delayed(const Duration(milliseconds: 950));
      } catch (error) {
        lastError = error;
        // One failed query must not invalidate other successful results.
      }
    }
    if (collected.isEmpty) {
      if (builtIn.isNotEmpty) return builtIn;
      if (existing.isNotEmpty) return existing;
      throw StateError('Catalogo non disponibile: ${lastError ?? 'rete assente'}');
    }
    final works = collected.values.toList()
      ..sort((a, b) => a.id.compareTo(b.id));
    try {
      final file = await _cacheFile();
      final pending = File('${file.path}.pending');
      await pending.writeAsString(jsonEncode(works.map((a) => a.toJson()).toList()),
        flush: true);
      await pending.rename(file.path);
    } catch (_) {
      // Viewing online still works when persistence is unavailable.
    }
    return MuseumCatalog.combine(works, extended);
  }

  void close() => _client.close();
}
