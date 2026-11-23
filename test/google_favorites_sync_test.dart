import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:artdrift/models/artwork.dart';
import 'package:artdrift/services/artdrift_account.dart';
import 'package:artdrift/services/favorites.dart';
import 'package:artdrift/services/favorite_cloud_sync.dart';

class MemoryGateway implements FavoriteCloudGateway {
  final Map<String, Map<String, FavoriteCloudRecord>> data = {};
  bool offline = false;

  @override
  Future<List<FavoriteCloudRecord>> fetch(String uid) async {
    if (offline) throw StateError('network_unavailable');
    return data[uid]?.values.toList() ?? [];
  }

  @override
  Future<void> upload(String uid, List<FavoriteCloudRecord> changes) async {
    if (offline) throw StateError('network_unavailable');
    final owned = data.putIfAbsent(uid, () => {});
    for (final change in changes) {
      owned[change.key] = change;
    }
  }
}

class BlockedCloudFetch extends MemoryGateway {
  Completer<void>? gate;
  Completer<void> entered = Completer<void>();

  @override
  Future<List<FavoriteCloudRecord>> fetch(String uid) async {
    final wait = gate;
    if (wait != null) {
      if (!entered.isCompleted) entered.complete();
      await wait.future;
    }
    return super.fetch(uid);
  }
}

void main() {
  const a = Artwork(
    id: 123, title: 'Old Garden', artist: 'Painter',
    date: '1880', imageId: '', publicDomain: true);
  const b = Artwork(
    id: 124, title: 'Quiet Shore', artist: 'Painter',
    date: '1890', imageId: '', publicDomain: true);

  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('legacy guest is preserved under account switching', () async {
    SharedPreferences.setMockInitialValues({
      Favorites.legacyKey: <String>['123'],
    });
    final store = Favorites();
    await store.load();
    expect(store.contains(a), true);
    await store.useAccount('account-A');
    expect(store.contains(a), false);
    await store.toggle(b);
    expect(store.contains(b), true);
    await store.useAccount('account-B');
    expect(store.keys, isEmpty);
    await store.useAccount('account-A');
    expect(store.contains(b), true);
    expect(store.contains(a), false);
    await store.useAccount(null);
    expect(store.contains(a), true);
    expect(store.contains(b), false);
  });

  test('explicit guest import survives new device and does not touch guest',
      () async {
    final cloud = MemoryGateway();
    final store = Favorites();
    await store.load();
    await store.toggle(a);
    await store.toggle(b);
    final sync = FavoriteSyncController(
      favorites: store, account: ArtDriftAccount.instance, gateway: cloud);
    await sync.bindAccount('account-A');
    expect(store.keys, isEmpty);
    expect(sync.guestImportAvailable, true);
    expect(await sync.importGuestFavorites(), 2);
    await Future<void>.delayed(const Duration(milliseconds: 30));
    await sync.synchronize();
    expect(cloud.data['account-A']?.length, 2);
    await store.useAccount(null);
    expect(store.contains(a), true);
    expect(store.contains(b), true);
    sync.dispose();

    // Fresh device: no local favorites or sessions, only cloud records.
    SharedPreferences.setMockInitialValues({});
    final freshStore = Favorites();
    await freshStore.load();
    final another = FavoriteSyncController(
      favorites: freshStore, account: ArtDriftAccount.instance, gateway: cloud);
    await another.bindAccount('account-A');
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(freshStore.contains(a), true);
    expect(freshStore.contains(b), true);
    expect(freshStore.savedFrom([]).length, 2);
    another.dispose();
  });

  test('offline removal writes tombstone; account switch cannot leak data',
      () async {
    final cloud = MemoryGateway();
    final store = Favorites();
    await store.load();
    final sync = FavoriteSyncController(
      favorites: store, account: ArtDriftAccount.instance, gateway: cloud);
    await sync.bindAccount('account-A');
    await Future<void>.delayed(const Duration(milliseconds: 30));
    await store.toggle(a);
    await sync.recordToggle(a);
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(cloud.data['account-A']?[a.catalogKey]?.selected, true);

    cloud.offline = true;
    await store.toggle(a);
    await sync.recordToggle(a);
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(sync.pendingCount, 1);
    expect(store.contains(a), false);
    await sync.bindAccount('account-B');
    expect(store.contains(a), false);
    await store.toggle(b);
    await sync.recordToggle(b);
    expect(sync.pendingCount, 1);
    await sync.bindAccount('account-A');
    expect(store.contains(b), false);
    expect(store.contains(a), false);
    expect(sync.pendingCount, 1);

    cloud.offline = false;
    // Wait for any previous offline attempt to settle before initiating
    // the explicit new-online retry (as the UI disables Sync while busy).
    await Future<void>.delayed(const Duration(milliseconds: 30));
    await sync.synchronize();
    expect(sync.pendingCount, 0);
    expect(cloud.data['account-A']?[a.catalogKey]?.selected, false);
    expect(cloud.data['account-B']?[b.catalogKey], isNull);

    // The second account's pending B upload is still isolated and durable.
    await sync.bindAccount('account-B');
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(cloud.data['account-B']?[b.catalogKey]?.selected, true);
    expect(store.contains(b), true);
    expect(store.contains(a), false);
    sync.dispose();
  });

  test('guest import never replaces an already saved account favorite',
      () async {
    final cloud = MemoryGateway();
    cloud.data['account-A'] = {
      b.catalogKey: FavoriteCloudRecord(b.catalogKey, true, b.toJson()),
    };
    final store = Favorites();
    await store.load();
    await store.toggle(a);
    final sync = FavoriteSyncController(
      favorites: store, account: ArtDriftAccount.instance, gateway: cloud);
    await sync.bindAccount('account-A');
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(store.contains(b), true);
    expect(await sync.importGuestFavorites(), 1);
    await Future<void>.delayed(const Duration(milliseconds: 30));
    expect(store.contains(a), true);
    expect(store.contains(b), true);
    expect(await sync.importGuestFavorites(), 0);
    sync.dispose();
  });
  test('in-flight cloud sync cannot mutate the next account or its queue',
      () async {
    final cloud = BlockedCloudFetch();
    final store = Favorites();
    await store.load();
    final sync = FavoriteSyncController(
      favorites: store, account: ArtDriftAccount.instance, gateway: cloud);
    await sync.bindAccount('account-A');
    await sync.synchronize();
    cloud.gate = Completer<void>();
    await sync.toggleFavorite(a);
    await cloud.entered.future;

    // Simulate a Google account switch during an already-running remote
    // fetch. The coordinator must wait until A's read is settled.
    final changed = sync.bindAccount('account-B');
    await Future<void>.delayed(const Duration(milliseconds: 2));
    expect(sync.switching, true);
    expect(store.contains(a), false,
      reason: 'A favorites must disappear as soon as identity switches');
    cloud.gate!.complete();
    cloud.gate = null;
    await changed;
    await sync.synchronize();
    expect(store.accountId, 'account-B');
    expect(store.contains(a), false);
    expect(sync.pendingCount, 0);

    await sync.toggleFavorite(b);
    await sync.synchronize();
    expect(cloud.data['account-B']?[a.catalogKey], isNull);
    expect(cloud.data['account-B']?[b.catalogKey]?.selected, true);
    await sync.bindAccount('account-A');
    await sync.synchronize();
    expect(store.contains(a), true);
    expect(store.contains(b), false);
    sync.dispose();
  });

  test('guest import completes in original account before switching accounts',
      () async {
    final cloud = MemoryGateway();
    final store = Favorites();
    await store.load();
    await store.toggle(a);
    final sync = FavoriteSyncController(
      favorites: store, account: ArtDriftAccount.instance, gateway: cloud);
    await sync.bindAccount('account-A');
    final import = sync.importGuestFavorites();
    final next = sync.bindAccount('account-B');
    expect(await import, 1);
    await next;
    await sync.synchronize();
    expect(store.accountId, 'account-B');
    expect(store.contains(a), false);
    expect(cloud.data['account-B']?[a.catalogKey], isNull);

    await sync.bindAccount('account-A');
    await sync.synchronize();
    expect(store.contains(a), true);
    await sync.bindAccount(null);
    expect(store.contains(a), true);
    sync.dispose();
  });

}
