import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Strict editorial test catalog. This is not cleared for a public app release.
class DailyDoppelgangerMedia {
  const DailyDoppelgangerMedia({
    required this.name, required this.fileName, required this.filePage,
    required this.credit, required this.license, required this.licenseUrl,
  });

  final String name;
  final String fileName;
  final String filePage;
  final String credit;
  final String license;
  final String licenseUrl;

  String get previewUrl =>
      'https://commons.wikimedia.org/wiki/Special:FilePath/' +
      Uri.encodeComponent(fileName) + '?width=640';

  factory DailyDoppelgangerMedia.fromJson(Map<String, dynamic> json) {
    String get(String key) => (json[key] is String ? json[key] as String : '').trim();
    final fileName = get('fileName');
    final page = get('filePage');
    final uri = Uri.tryParse(page);
    final lic = Uri.tryParse(get('licenseUrl'));
    if (get('name').isEmpty || fileName.isEmpty || fileName.length > 180 ||
        !fileName.toLowerCase().endsWith('.jpg') ||
        fileName.contains('/') || fileName.contains(String.fromCharCode(92)) ||
        uri == null || uri.scheme != 'https' ||
        uri.host != 'commons.wikimedia.org' || uri.userInfo.isNotEmpty ||
        uri.hasPort || uri.query.isNotEmpty ||
        uri.pathSegments.length != 2 || uri.pathSegments.first != 'wiki' ||
        !uri.pathSegments.last.startsWith('File:') ||
        lic == null || lic.scheme != 'https' ||
        lic.host != 'creativecommons.org' ||
        get('credit').isEmpty || get('license').isEmpty) {
      throw const FormatException('Daily media source/license invalid');
    }
    final pageFile = uri.pathSegments.last.substring(5).replaceAll('_', ' ');
    if (pageFile != fileName) {
      throw const FormatException('Daily media filename/source mismatch');
    }
    return DailyDoppelgangerMedia(
      name: get('name'), fileName: fileName, filePage: page,
      credit: get('credit'), license: get('license'),
      licenseUrl: get('licenseUrl'),
    );
  }
}

class DailyDoppelgangerPair {
  const DailyDoppelgangerPair({
    required this.id, required this.portrait, required this.celebrity,
    required this.artist, required this.year, required this.editorialEvidence,
  });
  final String id;
  final DailyDoppelgangerMedia portrait;
  final DailyDoppelgangerMedia celebrity;
  final String artist;
  final String year;
  final String editorialEvidence;

  factory DailyDoppelgangerPair.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    if (id is! String || !RegExp(r'^[a-z][a-z0-9-]{2,80}$').hasMatch(id) ||
        json['status'] != 'INTERNAL_QA_REVIEWED' ||
        json['rightsReviewedForInternalPreview'] != true ||
        json['commercialPublicityCleared'] != false ||
        json['portrait'] is! Map || json['celebrity'] is! Map) {
      throw const FormatException('Pair not admitted for internal QA');
    }
    final rawPortrait = Map<String, dynamic>.from(json['portrait'] as Map);
    final portrait = DailyDoppelgangerMedia.fromJson(rawPortrait);
    final celebrity = DailyDoppelgangerMedia.fromJson(
        Map<String, dynamic>.from(json['celebrity'] as Map));
    final artist = (rawPortrait['artist'] as String?)?.trim() ?? '';
    final year = (rawPortrait['year'] as String?)?.trim() ?? '';
    final editorial = json['editorialEvidence'];
    final editorialUri = editorial is String ? Uri.tryParse(editorial) : null;
    if (!celebrity.license.startsWith('CC BY ') ||
        !(portrait.license == 'CC0 1.0' ||
          portrait.license == 'Public domain') ||
        artist.isEmpty || year.isEmpty || portrait.name == celebrity.name ||
        editorialUri == null || editorialUri.scheme != 'https' ||
        editorialUri.userInfo.isNotEmpty || editorialUri.host.isEmpty) {
      throw const FormatException('Pair attribution/evidence incomplete');
    }
    return DailyDoppelgangerPair(
      id: id, portrait: portrait, celebrity: celebrity,
      artist: artist, year: year, editorialEvidence: editorial,
    );
  }
}

class DailyDoppelgangerCatalog {
  static const assetPath = 'assets/daily_doppelgangers.json';

  static List<DailyDoppelgangerPair> parse(String source) {
    final document = jsonDecode(source);
    if (document is! Map ||
        document['formatVersion'] != 1 ||
        document['publicationStatus'] != 'INTERNAL_QA_ONLY' ||
        document['pairs'] is! List) {
      throw const FormatException('Unsupported daily catalog');
    }
    final list = (document['pairs'] as List).map((row) {
      if (row is! Map) throw const FormatException('Bad daily pair');
      return DailyDoppelgangerPair.fromJson(Map<String, dynamic>.from(row));
    }).toList();
    if (list.length < 2 || list.map((p) => p.id).toSet().length != list.length) {
      throw const FormatException('At least two distinct pairs required');
    }
    list.sort((a, b) => a.id.compareTo(b.id));
    return List.unmodifiable(list);
  }

  static Future<List<DailyDoppelgangerPair>> load() async =>
      parse(await rootBundle.loadString(assetPath));
}

/// Per-device local-calendar daily lock, persisted atomically as a single JSON.
/// A previously seen pair can be revisited, but the other cards are not exposed.
/// Clock changes/uninstall/multiple devices require server authority to prevent.
class DailyDoppelgangerRotation {
  static const storageKey = 'artdrift.daily_doppelganger.v1';

  static String dayKey(DateTime date) =>
      date.year.toString().padLeft(4, '0') + '-' +
      date.month.toString().padLeft(2, '0') + '-' +
      date.day.toString().padLeft(2, '0');

  static DailyDoppelgangerPair? select({
    required List<DailyDoppelgangerPair> pairs,
    required DateTime date,
    String? previousDay,
    String? previousId,
  }) {
    if (pairs.length < 2 || pairs.map((p) => p.id).toSet().length != pairs.length) {
      return null;
    }
    final sorted = [...pairs]..sort((a, b) => a.id.compareTo(b.id));
    final today = dayKey(date);
    // Already revealed today (or device's clock was moved backwards).
    if (previousDay != null && today.compareTo(previousDay) <= 0) {
      for (final pair in sorted) {
        if (pair.id == previousId) return pair;
      }
      return null; // An unlisted image cannot be silently replaced today.
    }
    final dayNumber = DateTime.utc(date.year, date.month, date.day)
        .difference(DateTime.utc(1970, 1, 1)).inDays;
    var index = dayNumber % sorted.length;
    if (sorted[index].id == previousId) index = (index + 1) % sorted.length;
    return sorted[index];
  }

  static Future<DailyDoppelgangerPair?> open({
    required List<DailyDoppelgangerPair> pairs,
    required DateTime now,
  }) async {
    final preferences = await SharedPreferences.getInstance();
    final raw = preferences.getString(storageKey);
    String? previousDay;
    String? previousId;
    if (raw != null) {
      try {
        final saved = jsonDecode(raw);
        if (saved is Map && saved['day'] is String &&
            saved['id'] is String &&
            RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(saved['day'] as String)) {
          previousDay = saved['day'] as String;
          previousId = saved['id'] as String;
        }
      } on FormatException {
        // Ignore damaged optional daily state, not user content.
      }
    }
    final item = select(pairs: pairs, date: now,
        previousDay: previousDay, previousId: previousId);
    if (item == null) return null;
    final today = dayKey(now);
    if (previousDay == null || today.compareTo(previousDay) > 0) {
      await preferences.setString(storageKey,
          jsonEncode({'day': today, 'id': item.id}));
    }
    return item;
  }
}
