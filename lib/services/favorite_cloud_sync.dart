import 'dart:async';
import 'dart:convert';

import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../models/artwork.dart';
import 'artdrift_account.dart';
import 'favorites.dart';

/// Soft-delete tombstones prevent remote removals from being resurrected by
/// stale local snapshots on the next device. Every row is owned by auth.uid().
class FavoriteCloudRecord {
  const FavoriteCloudRecord(this.key, this.selected, this.snapshot);
  final String key;
  final bool selected;
  final Map<String, dynamic>? snapshot;

  static final _validKey = RegExp(r'^[a-z][a-z0-9_]{1,24}:[0-9]{1,12}$');
  bool get valid => key.length <= 96 && _validKey.hasMatch(key);

  factory FavoriteCloudRecord.decode(Map<String, dynamic> value) {
    final snap = value['artwork_snapshot'];
    return FavoriteCloudRecord(
      (value['artwork_key'] ?? '').toString(),
      value['is_favorite'] == true,
      snap is Map ? Map<String, dynamic>.from(snap) : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'artwork_key': key,
    'is_favorite': selected,
    'artwork_snapshot': selected ? snapshot : null,
  };

  Map<String, dynamic> toRow(String uid) => {
    'user_id': uid,
    ...toJson(),
  };

  Artwork? get artwork {
    if (!selected || snapshot == null) return null;
    try {
      final result = Artwork.fromJson(snapshot!);
      return result.catalogKey == key ? result : null;
    } catch (_) {
      return null;
    }
  }
}

abstract interface class FavoriteCloudGateway {
  Future<List<FavoriteCloudRecord>> fetch(String uid);
  Future<void> upload(String uid, List<FavoriteCloudRecord> changes);
}

class SupabaseFavoriteCloudGateway implements FavoriteCloudGateway {
  const SupabaseFavoriteCloudGateway(this.client);
  final SupabaseClient client;

  void _assertIdentity(String uid) {
    if (client.auth.currentUser?.id != uid) {
      throw StateError('artdrift_cloud_account_changed');
    }
  }

  @override
  Future<List<FavoriteCloudRecord>> fetch(String uid) async {
    _assertIdentity(uid);
    final rows = await client.from('artdrift_favorites')
        .select('artwork_key,is_favorite,artwork_snapshot')
        .eq('user_id', uid);
    _assertIdentity(uid);
    return [
      for (final row in rows)
        if (FavoriteCloudRecord.decode(row).valid)
          FavoriteCloudRecord.decode(row),
    ];
  }

  @override
  Future<void> upload(String uid, List<FavoriteCloudRecord> changes) async {
    if (changes.isEmpty) return;
    _assertIdentity(uid);
    for (var i = 0; i < changes.length; i += 80) {
      final batch = changes.skip(i).take(80).toList();
      await client.from('artdrift_favorites').upsert(
        [for (final change in batch) change.toRow(uid)],
        onConflict: 'user_id,artwork_key',
      );
      _assertIdentity(uid);
    }
  }
}

/// Account-scoped local cache plus durable pending operations.
///
/// Guests retain the old v2 keys. Cloud imports never occur implicitly.
/// Signed-in devices only see the active user's account cache; a separate
/// guest collection can be imported once after explicit user consent.
class FavoriteSyncController extends ChangeNotifier
    with WidgetsBindingObserver {
  FavoriteSyncController({
    required this.favorites,
    required this.account,
    FavoriteCloudGateway? gateway,
  }) : _testGateway = gateway;

  final Favorites favorites;
  final ArtDriftAccount account;
  final FavoriteCloudGateway? _testGateway;

  String? _userId;
  Future<void> _scopeQueue = Future<void>.value();
  Future<void>? _inFlight;
  bool _observing = false;
  Map<String, FavoriteCloudRecord> _pending = {};
  Timer? _poll;
  bool switching = false;
  bool syncing = false;
  bool hasSynced = false;
  bool guestImportAvailable = false;
  bool guestImported = false;
  String? lastError;

  String? get userId => _userId;
  int get pendingCount => _pending.length;
  bool get enabled => _userId != null;
  bool get ready => !switching;
  FavoriteCloudGateway? get _gateway =>
      _testGateway ?? (account.client == null
        ? null : SupabaseFavoriteCloudGateway(account.client!));

  String _pendingKey(String uid) => 'artdrift.sync.pending.$uid.v1';
  String _importKey(String uid) => 'artdrift.sync.imported_guest.$uid.v1';

  Future<void> bindAccount(String? nextId) {
    // Serialize with local mutations, not merely with other account changes.
    _scopeQueue = _scopeQueue
        .catchError((Object _) {})
        .then((_) => _bindAccount(nextId));
    return _scopeQueue;
  }

  /// Persist local selection and its cloud intent as one serialized action.
  /// A concurrent sign-out or account change waits for the durable queue.
  Future<void> toggleFavorite(Artwork artwork) {
    _scopeQueue = _scopeQueue
        .catchError((Object _) {})
        .then((_) async {
          if (switching) return;
          await favorites.toggle(artwork);
          await recordToggle(artwork);
        });
    return _scopeQueue;
  }

  Future<void> _bindAccount(String? nextId) async {
    if (nextId == _userId && !switching) return;
    switching = true;
    _poll?.cancel();
    // Do not reveal the previous account's works during the transition.
    favorites.keys.clear();
    notifyListeners();
    try {
      _userId = nextId;
      hasSynced = false;
      lastError = null;
      _pending = {};
      await favorites.useAccount(nextId);
      final prefs = await SharedPreferences.getInstance();
      if (nextId != null) {
        final raw = prefs.getString(_pendingKey(nextId));
        if (raw != null) {
          try {
            final data = jsonDecode(raw);
            if (data is Map) {
              for (final entry in data.entries) {
                if (entry.value is! Map) continue;
                final record = FavoriteCloudRecord.decode(
                  Map<String, dynamic>.from(entry.value as Map));
                if (record.valid && record.key == entry.key) {
                  _pending[record.key] = record;
                }
              }
            }
          } catch (_) {
            // Preserve malformed data in storage for possible recovery;
            // do not replace this record with an empty queue.
            lastError = 'Coda locale non leggibile: sincronizzazione sospesa.';
          }
        }
        final guest = Favorites();
        await guest.load();
        guestImported = prefs.getBool(_importKey(nextId)) ?? false;
        guestImportAvailable = !guestImported && guest.keys.isNotEmpty;
        _poll = Timer.periodic(const Duration(seconds: 90),
          (_) => unawaited(synchronize()));
      } else {
        guestImported = false;
        guestImportAvailable = false;
      }
    } finally {
      switching = false;
      notifyListeners();
    }
    if (nextId != null && lastError == null) {
      unawaited(synchronize());
    }
  }

  Future<void> recordToggle(Artwork artwork) async {
    final uid = _userId;
    if (uid == null || switching) return;
    final active = favorites.contains(artwork);
    final record = FavoriteCloudRecord(
      artwork.catalogKey, active, active ? artwork.toJson() : null);
    _pending[record.key] = record;
    // Durability before attempting network writes. Never clear a pending
    // operation merely because a request timed out or an account changed.
    await _savePending(uid);
    notifyListeners();
    unawaited(synchronize());
  }

  Future<void> _savePending(String uid) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode({
      for (final entry in _pending.entries) entry.key: entry.value.toJson(),
    });
    if (!await prefs.setString(_pendingKey(uid), encoded)) {
      throw StateError('artdrift_cloud_queue_write_failed');
    }
  }

  Future<int> importGuestFavorites() async {
    final uid = _userId;
    if (uid == null || switching || guestImported) return 0;
    final guest = Favorites();
    await guest.load();
    final newKeys = {...favorites.keys};
    final newSnapshots = <String, Artwork>{
      for (final key in favorites.keys)
        if (favorites.snapshotFor(key) != null)
          key: favorites.snapshotFor(key)!,
    };
    var added = 0;
    for (final key in guest.keys) {
      if (newKeys.contains(key) || _pending[key]?.selected == false) {
        continue;
      }
      if (!FavoriteCloudRecord(key, true, null).valid) continue;
      newKeys.add(key);
      final snap = guest.snapshotFor(key);
      if (snap != null) newSnapshots[key] = snap;
      _pending[key] = FavoriteCloudRecord(key, true, snap?.toJson());
      added++;
    }
    // First write pending operations, then the account view. If the app
    // stops here, retry uses exactly the same queued upserts.
    await _savePending(uid);
    await favorites.replaceState(newKeys, newSnapshots);
    final prefs = await SharedPreferences.getInstance();
    if (!await prefs.setBool(_importKey(uid), true)) {
      throw StateError('artdrift_guest_import_receipt_failed');
    }
    guestImported = true;
    guestImportAvailable = false;
    notifyListeners();
    unawaited(synchronize());
    return added;
  }

  Future<void> synchronize() {
    final alreadyRunning = _inFlight;
    if (alreadyRunning != null) return alreadyRunning;
    final run = _synchronizeOnce();
    _inFlight = run;
    run.whenComplete(() {
      if (identical(_inFlight, run)) _inFlight = null;
    });
    return run;
  }

  Future<void> _synchronizeOnce() async {
    final uid = _userId;
    if (uid == null || switching ||
        lastError?.contains('non leggibile') == true) {
      return;
    }
    final gateway = _gateway;
    if (gateway == null) return;
    syncing = true;
    lastError = null;
    notifyListeners();
    try {
      final uploadCopy = Map<String, FavoriteCloudRecord>.from(_pending);
      await gateway.upload(uid, uploadCopy.values.toList());
      if (_userId != uid || switching) return;
      // Only drop the operations actually acknowledged by the server.
      for (final entry in uploadCopy.entries) {
        if (identical(_pending[entry.key], entry.value)) {
          _pending.remove(entry.key);
        }
      }
      await _savePending(uid);
      final rows = await gateway.fetch(uid);
      if (_userId != uid || switching) return;
      final state = <String, FavoriteCloudRecord>{
        for (final row in rows) row.key: row,
        ..._pending, // queued offline edits override stale remote state
      };
      final keys = <String>{};
      final snaps = <String, Artwork>{};
      for (final row in state.values) {
        if (!row.selected) continue;
        keys.add(row.key);
        final snapshot = row.artwork ?? favorites.snapshotFor(row.key);
        if (snapshot != null) snaps[row.key] = snapshot;
      }
      await favorites.replaceState(keys, snaps);
      hasSynced = true;
    } catch (_) {
      lastError = 'Preferiti salvati sul dispositivo. Cloud da aggiornare.';
    } finally {
      syncing = false;
      notifyListeners();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && enabled) {
      unawaited(synchronize());
    }
  }

  void start() {
    if (_observing) return;
    WidgetsBinding.instance.addObserver(this);
    _observing = true;
  }

  @override
  void dispose() {
    _poll?.cancel();
    if (_observing) {
      WidgetsBinding.instance.removeObserver(this);
      _observing = false;
    }
    super.dispose();
  }
}
