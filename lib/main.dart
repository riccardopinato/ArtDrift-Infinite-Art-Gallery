import 'package:flutter/material.dart';
import 'package:flutter/painting.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'canvas/infinite_gallery.dart';
import 'screens/search_sheet.dart';
import 'screens/doppleganger.dart';
import 'screens/collection_canvas.dart';
import 'collections/art_collections.dart';
import 'screens/settings_sheet.dart';
import 'screens/favorites_sheet.dart';
import 'ui/gallery_toolbar.dart';
import 'ui/localization.dart';
import 'ui/museum_portal.dart';
import 'models/artwork.dart';
import 'screens/artwork_detail.dart';
import 'services/catalog_service.dart';
import 'services/favorites.dart';
import 'services/art_offline_thumbnail_index.dart';
import 'services/art_visual_color_selection.dart';
import 'services/art_mobile_canvas_selection.dart';
import 'services/art_joyful_start.dart';

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
  Offset? _launchWorldCenter;
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
      // First installs get a carefully selected, image-backed color canvas.
      // Saved artdrift.camera coordinates or ID playlists retain the exact
      // previous ordering so no user's existing world tiles are remapped.
      final color = await ArtVisualColorSelection.select(works);
      final canvas = await ArtMobileCanvasSelection.select(works,
        initialColorPlaylist: color);
      if (!mounted) return;
      var launch = _launchWorldCenter;
      if (launch == null) {
        try {
          final prefs = await SharedPreferences.getInstance();
          if (prefs.getBool(ArtJoyfulStart.enabledKey) == true) {
            launch = await ArtJoyfulStart.chooseForLaunch(canvas,
              viewport: MediaQuery.sizeOf(context));
          }
        } catch (_) {
          // Preference failures do not block the original offline canvas.
        }
      }
      if (!mounted) return;
      setState(() {
        _artworks = works;
        _canvasArtworks = canvas;
        _launchWorldCenter = launch;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() { _loading = false; _error = '$error'; });
    }
  }

  void _openDoppleganger() {
    if (!mounted) return;
    Navigator.of(context).push<void>(MaterialPageRoute(
      builder: (_) => const DopplegangerScreen()));
  }

  Future<void> _openSearch() async {
    final collectionArtworks = _artworks.where((art) =>
      art.hasBundledPreview || ArtOfflineThumbnailIndex.instance.has(art))
      .toList(growable: false);
    final selected = await showArtSearchSheet(context, _artworks,
      collectionCatalog: collectionArtworks,
      onOpenCollection: _openCollection,
      onOpenDoppleganger: _openDoppleganger);
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
    final available = _artworks.where((art) =>
      art.hasBundledPreview || ArtOfflineThumbnailIndex.instance.has(art));
    final works = ArtCollections.members(collection, available);
    if (works.isEmpty || !mounted) return;
    Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (_) => ArtCollectionCanvasScreen(
        collection: collection, artworks: works,
        onOpen: _openArtworkInGroup,
      ),
    ));
  }

  void _openArtworkInGroup(Artwork artwork, List<Artwork> artworks) {
    final index = artworks.indexWhere((a) => a.catalogKey == artwork.catalogKey);
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
      transitionDuration: const Duration(milliseconds: 200),
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
      InfiniteGallery(artworks: _canvasArtworks, onOpen: _open,
        initialWorldCenter: _launchWorldCenter),
      Positioned(top: 0, left: 0, right: 0,
        child: SafeArea(bottom: false, child: ArtDriftToolbar(
          onSearch: _openSearch,
          onFavorites: _openFavorites,
          onSettings: () => showArtDriftSettings(context),
        ))),
    ]));
  }
}
