import 'package:flutter/material.dart';
import 'package:flutter/painting.dart';

import 'canvas/infinite_gallery.dart';
import 'screens/search_sheet.dart';
import 'screens/settings_sheet.dart';
import 'screens/favorites_sheet.dart';
import 'ui/gallery_toolbar.dart';
import 'ui/localization.dart';
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
        _canvasArtworks = visible.isEmpty ? works : visible;
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
      visualPaletteAvailable: _colorArtworks.isNotEmpty);
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
    if (_loading) return const Scaffold(body: Center(child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text('artdrift ∞', style: TextStyle(
          fontSize: 31, color: Colors.white, fontWeight: FontWeight.w600)),
        SizedBox(height: 24),
        CircularProgressIndicator(color: Color(0xFFD2BB9C)),
        SizedBox(height: 20),
        Text('Carichiamo le opere del tuo museo…',
          style: TextStyle(color: Colors.white54)),
      ],
    )));
    if (_error != null || _artworks.isEmpty) {
      return Scaffold(body: Center(child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.wifi_off_rounded, size: 44, color: Colors.white54),
          const SizedBox(height: 20),
          const Text('La galleria non è disponibile',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 20, color: Colors.white)),
          const SizedBox(height: 10),
          const Text('Serve una connessione per scaricare la prima selezione. '
            'Dopo il primo caricamento potrai riaprire il catalogo salvato.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white60, height: 1.4)),
          const SizedBox(height: 20),
          FilledButton(onPressed: _initialize, child: const Text('Riprova')),
        ]),
      )));
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
