import 'package:flutter/material.dart';
import 'package:flutter/painting.dart';

import 'canvas/infinite_gallery.dart';
import 'models/artwork.dart';
import 'screens/artwork_detail.dart';
import 'services/catalog_service.dart';
import 'services/favorites.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
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
      final works = await _catalog.load(refresh: refresh);
      if (!mounted) return;
      setState(() { _artworks = works; _loading = false; });
    } catch (error) {
      if (!mounted) return;
      setState(() { _loading = false; _error = '$error'; });
    }
  }

  void _open(Artwork artwork) {
    final index = _artworks.indexWhere((a) => a.id == artwork.id);
    if (index < 0) return;
    Navigator.of(context).push(PageRouteBuilder<void>(
      pageBuilder: (context, animation, secondaryAnimation) => ArtworkDetail(
        artworks: _artworks,
        initialIndex: index,
        isFavorite: _favorites.contains,
        onToggleFavorite: _favorites.toggle,
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
    return Scaffold(body: InfiniteGallery(
      artworks: _artworks,
      onOpen: _open,
    ));
  }
}
