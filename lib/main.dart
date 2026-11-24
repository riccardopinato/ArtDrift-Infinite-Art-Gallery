import 'package:flutter/material.dart';
import 'package:flutter/painting.dart';

import 'canvas/infinite_gallery.dart';
import 'screens/search_sheet.dart';
import 'screens/settings_sheet.dart';
import 'screens/favorites_sheet.dart';
import 'ui/gallery_toolbar.dart';
import 'ui/localization.dart';
import 'ui/museum_portal.dart';
import 'screens/collection_canvas.dart';
import 'collections/art_collections.dart';
import 'models/artwork.dart';
import 'screens/artwork_detail.dart';
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
      final curated = await ArtVisualColorSelection.select(works);
      final visible = await ArtMobileCanvasSelection.select(works,
          initialColorPlaylist: curated);
      if (!mounted) return;
      setState(() {
        _artworks = works;
        _canvasArtworks = visible.isNotEmpty ? visible : works;
        _colorArtworks = curated;
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

  void _openArtworkInGroup(Artwork artwork, List<Artwork> artworks) {
    final index = artworks.indexWhere((a) => a.catalogKey == artwork.catalogKey);
    // Search results outside the currently visible mosaic retain their
    // own true source identity; they never change pinned tile assignments.
    final group = index < 0 ? <Artwork>[artwork] : artworks;
    final start = index < 0 ? 0 : index;
    Navigator.of(context).push(PageRouteBuilder<void>(
      pageBuilder: (context, animation, secondaryAnimation) => ArtworkDetail(
        artworks: group,
        initialIndex: start,
        isFavorite: _favorites.contains,
        onToggleFavorite: _toggleFavorite,
      ),
      transitionsBuilder: (context, animation, secondaryAnimation, child) =>
        FadeTransition(opacity: animation, child: child),
      transitionDuration: MediaQuery.disableAnimationsOf(context)
          ? Duration.zero : const Duration(milliseconds: 200),
    ));
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
    return Scaffold(body: Stack(fit: StackFit.expand, children: [
      InfiniteGallery(artworks: _canvasArtworks, onOpen: _open),
      Positioned(top: 0, left: 0, right: 0,
        child: SafeArea(bottom: false, child: ArtDriftToolbar(
          onSearch: _openSearch,
          onFavorites: _openFavorites,
          onSettings: () => showArtDriftSettings(context),
        ))),
    ]));
  }
}
