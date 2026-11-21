import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/artwork.dart';

/// Provider-qualified favorite IDs and locally cached artwork metadata.
/// Legacy AIC numeric IDs are migrated without resetting prior preferences.
class Favorites {
  static const legacyKey = 'artdrift.favorites.v1';
  static const keysKey = 'artdrift.favorites.keys.v2';
  static const snapshotsKey = 'artdrift.favorites.snapshots.v2';

  final Set<String> keys = <String>{};
  final Map<String, Artwork> _snapshots = <String, Artwork>{};

  Future<void> load() async {
    keys.clear();
    _snapshots.clear();
    final prefs = await SharedPreferences.getInstance();
    final v2 = prefs.getStringList(keysKey);
    if (v2 == null) {
      keys.addAll((prefs.getStringList(legacyKey) ?? const <String>[])
          .map(int.tryParse).whereType<int>().map((id) => 'aic:$id'));
    } else {
      keys.addAll(v2);
    }
    final raw = prefs.getString(snapshotsKey);
    if (raw == null) return;
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return;
      for (final entry in decoded.entries) {
        if (entry.key is! String || entry.value is! Map) continue;
        final art = Artwork.fromJson(Map<String, dynamic>.from(entry.value as Map));
        if (art.catalogKey == entry.key && keys.contains(entry.key)) {
          _snapshots[entry.key as String] = art;
        }
      }
    } on FormatException {
      // Invalid optional snapshots do not discard saved keys.
    } on TypeError {
      // Ignore invalid metadata; retain recoverable local catalog favorites.
    }
  }

  bool contains(Artwork artwork) => keys.contains(artwork.catalogKey);

  List<Artwork> savedFrom(List<Artwork> catalog) {
    final byKey = <String, Artwork>{
      ..._snapshots,
      for (final artwork in catalog) artwork.catalogKey: artwork,
    };
    return <Artwork>[
      for (final key in keys)
        if (byKey.containsKey(key)) byKey[key]!,
    ];
  }

  Future<void> toggle(Artwork artwork) async {
    final key = artwork.catalogKey;
    if (keys.remove(key)) {
      _snapshots.remove(key);
    } else {
      keys.add(key);
      _snapshots[key] = artwork;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(keysKey, keys.toList()..sort());
    await prefs.setString(snapshotsKey, jsonEncode({
      for (final entry in _snapshots.entries)
        if (keys.contains(entry.key)) entry.key: entry.value.toJson(),
    }));
  }
}
