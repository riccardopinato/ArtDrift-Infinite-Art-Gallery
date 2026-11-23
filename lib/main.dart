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
import 'services/art_offline_thumbnail_index.dart';
import 'services/art_mobile_canvas_selection.dart';
import 'services/art_visual_color_selection.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ArtDriftLocale.initialize();
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
  List<Artwork> _artworks = [];
  List<Artwork> _canvasArtworks = [];
  List<Artwork> _colorArtworks = [];
  String _lastSearchQuery = '';
  bool _immersive = false;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize({bool refresh = false}) async {
    setState(() { _loading = true; _error = null; });
    try {
      await _favorites.load();
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
    await _favorites.toggle(artwork);
    if (mounted) setState(() {});
  }

  Future<void> _openFavorites() async {
    final selected = await showArtFavoritesSheet(context,
      favorites: _favorites, catalog: _artworks,
      onToggleFavorite: _toggleFavorite);
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
    _catalog.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const MuseumPortal.loading();
    if (_error != null || _artworks.isEmpty) {
      return MuseumPortal.unavailable(onRetry: _initialize);
    }
    return Scaffold(body: ArtAdAwareViewport(
      // QA-only: defaults to zero. No AdMob SDK or artificial ad gap.
      // Once a real banner exists its measured height will replace this value.
      bannerHeight: const double.fromEnvironment(
          'ARTDRIFT_QA_AD_BANNER_HEIGHT', defaultValue: 0),
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
        child: SafeArea(bottom: false, child: ArtDriftToolbar(
          onSearch: _openSearch,
          onFavorites: _openFavorites,
          onSettings: () => showArtDriftSettings(context),
        ))),
    ]),
    ));
  }
}
