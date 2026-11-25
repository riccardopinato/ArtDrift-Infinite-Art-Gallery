import 'package:flutter/material.dart';
import 'package:flutter/painting.dart';

import 'canvas/infinite_gallery.dart';
import 'canvas/art_bento_world.dart';
import 'screens/search_sheet.dart';
import 'screens/doppleganger.dart';
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
import 'services/art_mobile_canvas_selection.dart';
import 'services/art_visual_color_selection.dart';
import 'services/art_joyful_palette.dart';
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
  ArtBentoWorld? _bento;
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
      // Use real pixel chroma/brightness, with the pinned color-first
      // playlist as a fail-closed fallback for any catalogue identity drift.
      final pixelScores = await ArtJoyfulPalette.load(works);
      final vibrant = ArtJoyfulPalette.select(works, pixelScores);
      final colorFirst = vibrant.isNotEmpty ? vibrant :
          await ArtVisualColorSelection.select(works);
      final extras = ArtJoyfulPalette.supplement(works, pixelScores, colorFirst);
      final canvas = await ArtMobileCanvasSelection.select(works,
        initialColorPlaylist: colorFirst, additionalColorPlaylist: extras);
      final bento = pixelScores.length == works.length &&
          canvas.isNotEmpty ? ArtBentoWorld(canvas, pixelScores) : null;
      if (!mounted) return;
      // A new region only on a fresh app opening, not on catalogue refresh.
      final launch = _launchWorldCenter ??
          await ArtJoyfulStart.chooseForLaunch(canvas,
            viewport: MediaQuery.sizeOf(context),
            pixelScores: pixelScores, bento: bento);
      if (!mounted) return;
      setState(() {
        _artworks = works;
        _canvasArtworks = canvas.isNotEmpty ? canvas : works;
        _bento = bento;
        _launchWorldCenter = launch;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() { _loading = false; _error = '$error'; });
    }
  }

  Future<void> _openSearch() async {
    final selected = await showArtSearchSheet(context, _artworks);
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

  void _open(Artwork artwork) {
    final index = _artworks.indexWhere((a) => a.catalogKey == artwork.catalogKey);
    // Remote discoveries open in detail without perturbing the pinned canvas.
    final group = index < 0 ? <Artwork>[artwork] : _artworks;
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
      InfiniteGallery(
        artworks: _canvasArtworks,
        onOpen: _open,
        initialWorldCenter: _launchWorldCenter,
        bento: _bento,
      ),
      Positioned(top: 0, left: 0, right: 0,
        child: SafeArea(bottom: false, child: ArtDriftToolbar(
          onSearch: _openSearch,
          onFavorites: _openFavorites,
          onSettings: () => showArtDriftSettings(context),
        ))),
      Positioned(
        left: 16,
        bottom: 73,
        child: SafeArea(
          top: false,
          child: FilledButton.tonalIcon(
            onPressed: () => Navigator.of(context).push<void>(
              MaterialPageRoute(builder: (_) => const DopplegangerScreen()),
            ),
            icon: const Icon(Icons.compare_outlined),
            label: const Text('Doppleganger'),
          ),
        ),
      ),
    ]));
  }
}
