import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/painting.dart';

import 'canvas/infinite_gallery.dart';
import 'screens/search_sheet.dart';
import 'screens/settings_sheet.dart';
import 'screens/favorites_sheet.dart';
import 'ui/gallery_toolbar.dart';
import 'ui/localization.dart';
import 'ui/museum_portal.dart';
import 'ui/tile_origin_flight.dart';
import 'ui/art_ad_aware_viewport.dart';
import 'models/artwork.dart';
import 'screens/artwork_detail.dart';
import 'screens/collection_canvas.dart';
import 'collections/art_collections.dart';
import 'services/catalog_service.dart';
import 'services/favorites.dart';
import 'services/artdrift_account.dart';
import 'services/favorite_cloud_sync.dart';
import 'services/art_offline_thumbnail_index.dart';
import 'services/art_mobile_canvas_selection.dart';
import 'services/art_visual_color_selection.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ArtDriftLocale.initialize();
  await ArtDriftAccount.instance.initialize();
  PaintingBinding.instance.imageCache.maximumSize = 110;
  PaintingBinding.instance.imageCache.maximumSizeBytes = 48 * 1024 * 1024;
  runApp(const ArtDriftApp());
}

class ArtDriftApp extends StatelessWidget {
  const ArtDriftApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'ArtDrift — Infinite Art Gallery',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF101117),
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFFE5C8A5),
        brightness: Brightness.dark),
    ),
    home: const GalleryHome(),
  );
}

class GalleryHome extends StatefulWidget {
  const GalleryHome({super.key});
  @override
  State<GalleryHome> createState() => _GalleryHomeState();
}

class _GalleryHomeState extends State<GalleryHome> {
  final CatalogService _catalog = CatalogService();
  final Favorites _favorites = Favorites();
  late final FavoriteSyncController _sync = FavoriteSyncController(
    favorites: _favorites, account: ArtDriftAccount.instance);
  String? _seenAccountId;
  List<Artwork> _artworks = [];
  List<Artwork> _canvasArtworks = [];
  List<Artwork> _colorArtworks = [];
  String _lastSearchQuery = '';
  bool _immersive = false;
  bool _toolbarQuiet = false;
  Timer? _toolbarQuietTimer;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _seenAccountId = ArtDriftAccount.instance.userId;
    ArtDriftAccount.instance.addListener(_accountChanged);
    _sync.addListener(_syncChanged);
    _sync.start();
    _initialize();
  }

  void _syncChanged() {
    if (mounted) setState(() {});
  }

  void _accountChanged() {
    final next = ArtDriftAccount.instance.userId;
    if (next == _seenAccountId) return;
    _seenAccountId = next;
    unawaited(_sync.bindAccount(next).catchError((Object _) {
      // Keep the museum usable in guest/offline mode after a storage error.
    }));
  }

  // Presentation-only idle fade. The canvas camera and tile registry
  // stay untouched; any pointer restores full toolbar readability.
  void _onCanvasPointer() {
    _toolbarQuietTimer?.cancel();
    if (_toolbarQuiet) setState(() => _toolbarQuiet = false);
    _toolbarQuietTimer = Timer(const Duration(seconds: 3), () {
      if (mounted && !_immersive) {
        setState(() => _toolbarQuiet = true);
      }
    });
  }

  Future<void> _initialize({bool refresh = false}) async {
    setState(() { _loading = true; _error = null; });
    try {
      await _favorites.load();
      try {
        await _sync.bindAccount(ArtDriftAccount.instance.userId);
      } catch (_) {
        // Auth/sync must not make the public art catalog unavailable.
      }
      // Fetch a tiny same-origin index before mounting remote image widgets.
      await ArtOfflineThumbnailIndex.instance.initialize();
      final works = await _catalog.load(refresh: refresh);
      if (!mounted) return;
      // Keep mobile tile-to-artwork assignment pinned across catalog updates.
      // Every image comes from the exact same artwork; all remote-only entries
      // remain searchable and may be viewed individually.
      final color = await ArtVisualColorSelection.select(works);
      // Preserve the existing canvas when a device already has pinned tiles.
      // For a new Android install, seed a stable colorful playlist instead.
      final visible = await ArtMobileCanvasSelection.select(works,
        initialColorPlaylist: color);
      if (!mounted) return;
      setState(() {
        _artworks = works;
        _canvasArtworks = const bool.fromEnvironment(
            'ARTDRIFT_VISUAL_HOME_DEFAULT', defaultValue: false) && color.isNotEmpty
            ? color : (visible.isEmpty ? works : visible);
        _colorArtworks = color;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() { _loading = false; _error = '$error'; });
    }
  }

  Future<void> _openSearch() async {
    final selected = await showArtSearchSheet(context, _artworks,
      collectionCatalog: _canvasArtworks,
      onOpenCollection: _openCollection,
      visualPaletteAvailable: _colorArtworks.isNotEmpty,
      initialQuery: _lastSearchQuery,
      onQueryChanged: (value) => _lastSearchQuery = value);
    if (!mounted || selected == null) return;
    _open(selected);
  }

  Future<void> _toggleFavorite(Artwork artwork) async {
    try {
      await _sync.toggleFavorite(artwork);
    } catch (_) {
      // Local selection remains saved; never claim cloud success.
      if (mounted) ScaffoldMessenger.maybeOf(context)?.showSnackBar(
        const SnackBar(content: Text(
          'Preferito locale salvato, sincronizzazione da riprovare.')));
    }
    if (mounted) setState(() {});
  }

  Future<void> _openFavorites() async {
    final selected = await showArtFavoritesSheet(context,
      favorites: _favorites, catalog: _artworks,
      onToggleFavorite: _toggleFavorite,
      changes: _sync);
    if (!mounted || selected == null) return;
    _open(selected);
  }

  void _open(Artwork artwork) => _openArtworkInGroup(artwork, _artworks);

  void _openCollection(ArtCollection collection) {
    final selected = collection.id == ArtCollections.colorFirst.id
        ? _colorArtworks
        : ArtCollections.members(collection, _canvasArtworks);
    if (selected.isEmpty || !mounted) return;
    Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (_) => ArtCollectionCanvasScreen(
        collection: collection,
        artworks: selected,
        onOpen: _openArtworkInGroup,
      ),
    ));
  }

  void _openArtworkInGroup(Artwork artwork, List<Artwork> artworks, {Rect? tileRect}) {
    final index = artworks.indexWhere((a) => a.catalogKey == artwork.catalogKey);
    final group = index < 0 ? <Artwork>[artwork] : artworks;
    final start = index < 0 ? 0 : index;
    final displayIdentity = ValueNotifier<String>(artwork.catalogKey);
    final route = PageRouteBuilder<void>(
      pageBuilder: (context, animation, secondaryAnimation) => ArtworkDetail(
        artworks: group,
        initialIndex: start,
        isFavorite: _favorites.contains,
        onToggleFavorite: _toggleFavorite,
        onArtworkChanged: (next) => displayIdentity.value = next.catalogKey,
      ),
      transitionsBuilder: (context, animation, secondaryAnimation, child) =>
        tileRect == null
          ? FadeTransition(opacity: animation, child: child)
          : TileOriginFlight(
              animation: animation,
              originRect: tileRect,
              originArtwork: artwork,
              originalArtworkKey: artwork.catalogKey,
              currentArtworkKey: displayIdentity,
              child: child),
      transitionDuration: MediaQuery.disableAnimationsOf(context)
          ? Duration.zero : const Duration(milliseconds: 330),
      reverseTransitionDuration: MediaQuery.disableAnimationsOf(context)
          ? Duration.zero : const Duration(milliseconds: 300),
    );
    Navigator.of(context).push(route);
    route.completed.then((_) => displayIdentity.dispose());
  }

  @override
  void dispose() {
    _toolbarQuietTimer?.cancel();
    ArtDriftAccount.instance.removeListener(_accountChanged);
    _sync.removeListener(_syncChanged);
    _sync.dispose();
    _catalog.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const MuseumPortal.loading();
    if (_error != null || _artworks.isEmpty) {
      return MuseumPortal.unavailable(onRetry: _initialize);
    }
    return Scaffold(body: Listener(
      behavior: HitTestBehavior.translucent,
      onPointerDown: (_) => _onCanvasPointer(),
      child: ArtAdAwareViewport(
      // QA-only: defaults to zero. No AdMob SDK or artificial ad gap.
      // Once a real banner exists its measured height will replace this value.
      bannerHeight: const int.fromEnvironment(
          'ARTDRIFT_QA_AD_BANNER_HEIGHT', defaultValue: 0).toDouble(),
      child: Stack(fit: StackFit.expand, children: [
      InfiniteGallery(
        artworks: _canvasArtworks,
        cameraKey: const bool.fromEnvironment(
            'ARTDRIFT_VISUAL_HOME_DEFAULT', defaultValue: false)
            ? 'artdrift.preview.colorhome.camera' : 'artdrift.camera',
        onOpen: _open,
        onOpenAtRect: (art, rect) =>
            _openArtworkInGroup(art, _artworks, tileRect: rect),
        onToggleFavorite: _toggleFavorite,
        isFavorite: _favorites.contains,
        onImmersiveChanged: (value) {
          if (mounted) setState(() => _immersive = value);
        }),
      if (!_immersive) Positioned(top: 0, left: 0, right: 0,
        child: AnimatedOpacity(
          duration: const Duration(milliseconds: 350),
          opacity: _toolbarQuiet ? .24 : 1.0,
          child: SafeArea(bottom: false, child: ArtDriftToolbar(
            onSearch: _openSearch,
            onFavorites: _openFavorites,
            onSettings: () => showArtDriftSettings(context, sync: _sync),
          )))),
    ]),
    )));
  }
}
