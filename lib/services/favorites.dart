import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/artwork.dart';

/// Provider-qualified favorite IDs and locally cached artwork metadata.
/// Legacy AIC numeric IDs are migrated without resetting prior preferences.
class Favorites {
  static const legacyKey = 'artdrift.favorites.v1';
  static const keysKey = 'artdrift.favorites.keys.v2';
  static const snapshotsKey = 'artdrift.favorites.snapshots.v2';

  String? _accountId;

  /// null is the original guest store, preserving all v1/v2 installations.
  String? get accountId => _accountId;

  String get _keysStorageKey => _accountId == null
      ? keysKey : 'artdrift.favorites.account.$_accountId.keys.v1';
  String get _snapshotsStorageKey => _accountId == null
      ? snapshotsKey : 'artdrift.favorites.account.$_accountId.snapshots.v1';

  final Set<String> keys = <String>{};
  final Map<String, Artwork> _snapshots = <String, Artwork>{};

  Future<void> useAccount(String? accountId) async {
    // Only the verified auth user ID may be passed by the coordinator.
    _accountId = accountId;
    await load();
  }

  Artwork? snapshotFor(String key) => _snapshots[key];

  Future<void> load() async {
    keys.clear();
    _snapshots.clear();
    final prefs = await SharedPreferences.getInstance();
    final v2 = prefs.getStringList(_keysStorageKey);
    if (v2 == null && _accountId == null) {
      keys.addAll((prefs.getStringList(legacyKey) ?? const <String>[])
          .map(int.tryParse).whereType<int>().map((id) => 'aic:$id'));
    } else {
      keys.addAll(v2 ?? const <String>[]);
    }
    final raw = prefs.getString(_snapshotsStorageKey);
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
    await _persist();
  }

  /// Replace only the active account view after a successful server read.
  /// Never touches the guest store, and never writes another account's keys.
  Future<void> replaceState(
      Set<String> activeKeys, Map<String, Artwork> snapshots) async {
    keys
      ..clear()
      ..addAll(activeKeys);
    _snapshots
      ..clear()
      ..addEntries(snapshots.entries.where(
        (e) => keys.contains(e.key) && e.value.catalogKey == e.key));
    await _persist();
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    final written = await prefs.setStringList(
      _keysStorageKey, keys.toList()..sort());
    final saved = await prefs.setString(_snapshotsStorageKey, jsonEncode({
      for (final entry in _snapshots.entries)
        if (keys.contains(entry.key)) entry.key: entry.value.toJson(),
    }));
    if (!written || !saved) {
      throw StateError('artdrift_favorites_local_write_failed');
    }
  }
}
